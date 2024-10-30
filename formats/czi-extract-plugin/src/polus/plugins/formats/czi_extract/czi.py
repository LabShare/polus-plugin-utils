"""Czi Extract Plugin."""
import logging
from pathlib import Path
from typing import Optional
from multiprocessing import cpu_count

import czifile
import numpy as np
from bfio import BioReader
from bfio import BioWriter
import preadator

logger = logging.getLogger(__name__)

num_workers = max([cpu_count(), 2])

def _get_image_dim(s: np.ndarray, dim: str) -> int:
    """Get czi image dimension."""
    ind = s.axes.find(dim)
    if ind < 0:
        return 1
    return s.shape[ind]


def _get_image_name(  # noqa: PLR0913
    base_name: str,
    row: int,
    col: int,
    z: Optional[int] = None,
    c: Optional[int] = None,
    t: Optional[int] = None,
    padding: int = 3,
) -> str:
    """This function generates an image name from image coordinates."""
    name = base_name
    name += "_y" + str(row).zfill(padding)
    name += "_x" + str(col).zfill(padding)
    if z is not None:
        name += "_z" + str(z).zfill(padding)
    if c is not None:
        name += "_c" + str(c).zfill(padding)
    if t is not None:
        name += "_t" + str(t).zfill(padding)
    name += ".ome.tif"
    return name


def write_thread(
    out_file_path: Path,
    data: np.ndarray,
    metadata: BioReader.metadata,
    chan_name: str,
) -> None:
    """Thread for saving images.

    This function is intended to be run inside a threadpool to save an image.

    Args:
        out_file_path : Path to an output file
        data : FOV to save
        metadata : Metadata for the image
        chan_name: Name of the channel
    """
    logger.info(f"Writing: {Path(out_file_path).name}")
    with BioWriter(out_file_path, metadata=metadata) as bw:
        bw.X = data.shape[1]
        bw.Y = data.shape[0]
        bw.Z = 1
        bw.C = 1
        bw.cnames = [chan_name]
        bw[:] = data


def extract_fovs(file_path: Path, out_path: Path) -> None:
    """Extract individual FOVs from a czi file.

    When CZI files are loaded by BioFormats, it will generally try to mosaic
    images together by stage position if the image was captured with the
    intention of mosaicing images together. At the time this function was
    written, there was no clear way of extracting individual FOVs so this
    algorithm was created.

    Every field of view in each z-slice, channel, and timepoint contained in a
    CZI file is saved as an individual image.

    Args:
        file_path : Path to CZI file
        out_path : Path to output directory
    """
    logger.info("Starting extraction from " + str(file_path.name) + "...")

    base_name = Path(file_path.name).stem

    # Load files without mosaicing
    czi = czifile.CziFile(file_path, detectmosaic=False)
    subblocks = [
        s for s in czi.filtered_subblock_directory if s.mosaic_index is not None
    ]

    ind: dict = {"X": [], "Y": [], "Z": [], "C": [], "T": [], "Row": [], "Col": []}

    # Get the indices of each FOV
    for s in subblocks:
        scene = [dim.start for dim in s.dimension_entries if dim.dimension == "S"]
        if scene is not None and scene[0] != 0:
            continue

        for dim in s.dimension_entries:
            if dim.dimension == "X":
                ind["X"].append(dim.start)
            elif dim.dimension == "Y":
                ind["Y"].append(dim.start)
            elif dim.dimension == "Z":
                ind["Z"].append(dim.start)
            elif dim.dimension == "C":
                ind["C"].append(dim.start)
            elif dim.dimension == "T":
                ind["T"].append(dim.start)

    unique_y = np.unique(ind["Y"])
    unique_x = np.unique(ind["X"])

    row_conv = dict(
        zip(
            np.sort(unique_y),
            range(0, len(unique_y)),
        ),
    )
    col_conv = dict(
        zip(
            np.sort(unique_x),
            range(0, len(unique_x)),
        ),
    )

    ind["Row"] = [row_conv[y] for y in ind["Y"]]
    ind["Col"] = [col_conv[x] for x in ind["X"]]

    if ind.__len__() != 0:
        with BioReader(file_path) as br:
            metadata = br.metadata
            chan_names = br.cnames

        with preadator.ProcessManager(
                name="Convert czi to individual ome tif",
                num_processes=num_workers,
                threads_per_process=2,
            ) as pm:
                for s, i in zip(subblocks, range(0, len(subblocks))):
                    z = None if len(ind["Z"]) == 0 else ind["Z"][i]
                    c = None if len(ind["C"]) == 0 else ind["C"][i]
                    t = None if len(ind["T"]) == 0 else ind["T"][i]

                    out_file_path = out_path.joinpath(
                        _get_image_name(
                            base_name,
                            row=ind["Row"][i],
                            col=ind["Col"][i],
                            z=z,
                            c=c,
                            t=t,
                        ),
                    )

                    dims = [
                        _get_image_dim(s, "Y"),
                        _get_image_dim(s, "X"),
                        _get_image_dim(s, "Z"),
                        _get_image_dim(s, "C"),
                        _get_image_dim(s, "T"),
                    ]

                    data = s.data_segment().data().reshape(dims)
                    pm.submit_process(write_thread, out_file_path, data, metadata, chan_names[c])
                pm.join_processes()

    else:
        msg = logger.info("Unable to extract individual fovs in czi file")
        raise ValueError(msg)

