"""Assemble images from directories of images and stitching vectors."""

import logging
import re
from math import ceil
from pathlib import Path
from typing import Optional

import filepattern as fp
import numpy as np
from bfio import BioReader
from bfio import BioWriter
from preadator import ProcessManager

logging.basicConfig(format="%(name)-8s - %(levelname)-8s - %(message)s")
logger = logging.getLogger("image-assembler")
logger.setLevel(logging.DEBUG)

# this parameter controls disk writes. Plateau after 8192
chunk_size = 1024 * 8
chunk_width, chunk_height = chunk_size, chunk_size

BACKEND = "python"


def generate_output_filepaths(
    img_path: Path,
    stitch_path: Path,
    output_path: Path,
    derive_name_from_vector_file: Optional[bool],
) -> list[Path]:
    """Generate the output filepaths that would be created if the assembler was called.

    Args:
        img_path: path to the directory containing the images.
        stitch_path: path to the directory containing the stitching vectors.
        output_path: path to the directory where the assembled images will be saved.
        derive_name_from_vector_file: whether to derive the name of the output
        image from the stitching vector.
    """
    output_filepaths = []
    vector_patterns = collect_stitching_vector_patterns(stitch_path)
    for vector_file, pattern in vector_patterns:
        fovs = fp.FilePattern(vector_file, pattern)
        first_image_name = fovs[0][1][0]
        first_image = img_path / first_image_name
        output_image_path = derive_output_image_path(
            fovs,
            derive_name_from_vector_file,
            vector_file,
            first_image,
            output_path,
        )
        output_filepaths.append(output_image_path)

    return output_filepaths


def assemble_images(
    img_path: Path,
    stitch_path: Path,
    output_path: Path,
    derive_name_from_vector_file: Optional[bool],
) -> None:
    """Assemble images from directories of images and stitching vectors.

    Args:
        img_path: path to the directory containing the images.
        stitch_path: path to the directory containing the stitching vectors.
        output_path: path to the directory where the assembled images will be saved.
        derive_name_from_vector_file: whether to derive the name of the output
        image from the stitching vector.
    """
    vector_patterns = collect_stitching_vector_patterns(stitch_path)

    with ProcessManager(name="image-assembler", log_level="INFO") as pm:
        for vector_file, pattern in vector_patterns:
            pm.submit_process(
                assemble_image,
                vector_file,
                pattern,
                derive_name_from_vector_file,
                img_path,
                output_path,
            )
        pm.join_processes()


def collect_stitching_vector_patterns(
    stitching_vector_path: Path,
) -> list[tuple[Path, str]]:
    """Collect all valid stitching vectors in the given directory.

    Returns a tuple containing the vector file and the inferred pattern for it.
    Invalid stitching vectors are ignored.
    """
    # find all files
    if stitching_vector_path.is_dir():
        files = [
            vector
            for vector in list(stitching_vector_path.iterdir())
            if vector.is_file()
        ]
    else:
        files = [stitching_vector_path]

    stitching_vector_pattern: list[tuple[Path, str]] = []

    # make sure files are valid stitching vectors
    for v in files:
        try:
            pattern = fp.infer_pattern(v)
            stitching_vector_pattern.append((v, pattern))
        except RuntimeError:
            logger.critical(
                f"this file cannot be parsed as a stitching vector and will be ignored : {v}",  # noqa: E501
            )

    return stitching_vector_pattern


def derive_output_image_path(
    fovs: fp.FilePattern,
    derive_name_from_vector_file: Optional[bool],
    vector_file: Path,
    first_image: Path,
    output_path: Path,
) -> Path:
    """Derive the name of the output image according to user specified preferences.

    It can be derived from the inferred pattern or from the pattern of the stitching
    vector.

    Args:
        fovs: file pattern of the stitching vector.
        derive_name_from_vector_file: whether to derive the name of the output
        image from the stitching vector.
        vector_file: path to the stitching vector.
        first_image: path to the first image in the stitching vector.
        output_path: path to the output directory.
    """
    # guess a name for the final assembled image
    output_name = fovs.output_name()

    if derive_name_from_vector_file:
        global_regex = ".*global-positions-([0-9]+).txt"
        match = re.match(global_regex, Path(vector_file).name)
        if match and match.groups()[0]:
            output_name = "".join([match.groups()[0], *Path(first_image).suffixes])

    return output_path / output_name


def assemble_image(
    vector_file: Path,
    pattern: str,
    derive_name_from_vector_file: Optional[bool],
    img_path: Path,
    output_path: Path,
) -> None:
    """Assemble an image from fovs.

    Args:
        vector_file: path to the stitching vector.
        pattern: inferred pattern for this stitching vector.
        derive_name_from_vector_file: whether to derive the name of the output
        image from the stitching vector.
        img_path: path to the image directory.
        output_path: path to the output directory.
    """
    fovs = fp.FilePattern(vector_file, pattern)

    # let's figure out the size of a partial FOV.
    # Pick the first image in stitching vector.
    # We assume all images have the same size.
    first_image_name = fovs[0][1][0]
    first_image = img_path / first_image_name
    with BioReader(first_image, backend=BACKEND) as br:
        full_image_metadata = br.metadata
        fov_width = br.x
        fov_height = br.y
        # stitching is only performed on the (x,y) plane
        if br.z != 1:
            msg = f"this image has a z_stack of {br.z} and cannot be assembled"
            logger.critical(msg)
            raise ValueError(msg)

    output_image_path: Path = derive_output_image_path(
        fovs,
        derive_name_from_vector_file,
        vector_file,
        first_image,
        output_path,
    )

    # compute final full image size (requires a full pass over the partial fovs)
    full_image_width, full_image_height = fov_width, fov_height
    for fov in fovs():
        metadata = fov[0]
        full_image_width = max(full_image_width, metadata["posX"] + fov_width)
        full_image_height = max(full_image_height, metadata["posY"] + fov_height)

    # divide our image into chunks that can be processed separately
    chunk_grid_col = ceil(full_image_width / chunk_width)
    chunk_grid_row = ceil(full_image_height / chunk_height)
    chunks: list[list] = [
        [[] for _ in range(chunk_grid_col)] for _ in range(chunk_grid_row)
    ]

    # figure out regions of fovs that needs to be copied into each chunk.
    # This is fast so it can be done beforehand in a single process.
    for fov in fovs():
        # we are parsing a stitching vector, so we are always getting unique records.
        filename = fov[1][0]

        # get global coordinates of fov in the final image
        metadata = fov[0]
        global_fov_start_x = metadata["posX"]
        global_fov_start_y = metadata["posY"]

        # check which chunks the fov overlaps
        chunk_col_min = global_fov_start_x // chunk_width
        chunk_col_max = (global_fov_start_x + fov_width) // chunk_width
        chunk_row_min = global_fov_start_y // chunk_height
        chunk_row_max = (global_fov_start_y + fov_height) // chunk_height

        # define regions of fovs to copy to each chunk
        for row in range(chunk_row_min, chunk_row_max + 1):
            for col in range(chunk_col_min, chunk_col_max + 1):
                # global coordinates of the contribution
                global_start_x = max(global_fov_start_x, col * chunk_width)
                global_end_x = min(
                    global_fov_start_x + fov_width,
                    (col + 1) * chunk_width,
                )
                global_start_y = max(global_fov_start_y, row * chunk_height)
                global_end_y = min(
                    global_fov_start_y + fov_height,
                    (row + 1) * chunk_height,
                )

                # coordinates within the fov we will copy from
                fov_start_x = (
                    max(global_fov_start_x, col * chunk_width) - global_fov_start_x
                )
                fov_start_y = (
                    max(global_fov_start_y, row * chunk_height) - global_fov_start_y
                )

                # coordinates within the chunk we will copy to
                chunk_start_x = global_start_x - col * chunk_width
                chunk_start_y = global_start_y - row * chunk_height

                ## dimensions of the region to be copied
                region_width = global_end_x - global_start_x
                region_height = global_end_y - global_start_y

                region_to_copy = (
                    filename,
                    (fov_start_x, fov_start_y),
                    (chunk_start_x, chunk_start_y),
                    (region_width, region_height),
                )
                chunks[row][col].append(region_to_copy)

    # A single copy of of the writer is shared amongst all threads.
    with BioWriter(
        output_image_path,
        metadata=full_image_metadata,
        backend=BACKEND,
    ) as bw:
        bw.x = full_image_width
        bw.y = full_image_height
        bw._CHUNK_SIZE = chunk_size

        # Copy each fov regions.
        # This requires multiple reads and copies and a final write.
        # This is a slow IObound process so it can benefit from multithreading
        # in order to overlap reads/writes.
        output_name = output_image_path.name
        with ProcessManager(name="assemble_" + output_name, log_level="INFO") as pm:
            for row in range(chunk_grid_row):
                for col in range(chunk_grid_col):
                    pm.submit_thread(
                        assemble_chunk,
                        row,
                        col,
                        chunks[row][col],
                        bw,
                        img_path,
                    )


def assemble_chunk(
    row: int,
    col: int,
    regions_to_copy: list[
        tuple[Path, tuple[int, int], tuple[int, int], tuple[int, int]]
    ],
    bw: BioWriter,
    img_path: Path,
) -> None:
    """Assemble a chunk of data from all the fovs it overlaps with.

    We pass the BioWriter as an argument to the task because we cannot initialize
    the process state with preadator.

    Args:
        row: row of the chunk in the grid of chunks
        col: column of the chunk in the grid of chunks
        regions_to_copy: list of regions of fovs to copy to this chunk. The regions
        are tuples containing:
            - the filename of the fov
            - the starting x and y coordinates of the fov
            - the starting x and y coordinates of the chunk
            - the width and height of the region to copy
        bw: BioWriter to write the assembled chunk to
        img_path: path to the image directory
    """
    chunk = np.zeros((chunk_width, chunk_height), bw.dtype)

    for region_to_copy in regions_to_copy:
        filepath = img_path / region_to_copy[0]
        (fov_start_x, fov_start_y) = region_to_copy[1]
        (chunk_start_x, chunk_start_y) = region_to_copy[2]
        (region_width, region_height) = region_to_copy[3]

        with BioReader(filepath, backend=BACKEND) as br:
            # read data from region of fov
            data = br[
                fov_start_y : fov_start_y + region_height,
                fov_start_x : fov_start_x + region_width,
            ]
            # copy data to chunk
            chunk[
                chunk_start_y : chunk_start_y + region_height,
                chunk_start_x : chunk_start_x + region_width,
            ] = data.astype(bw.dtype)

    # completed chunk is written to disk
    # we only write what fits in the image since that the behavior bfio expects
    max_y = min((row + 1) * chunk_height, bw.y)
    max_x = min((col + 1) * chunk_width, bw.x)
    bw[row * chunk_height : max_y, col * chunk_width : max_x] = chunk[
        0 : max_y - row * chunk_height,
        0 : max_x - col * chunk_width,
    ]
