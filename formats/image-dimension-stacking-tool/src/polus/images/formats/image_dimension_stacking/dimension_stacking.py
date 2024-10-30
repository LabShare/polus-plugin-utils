"""Stacking images along a given dimension."""

import pathlib
import shutil

import bfio

from . import utils

logger = utils.make_logger(__name__)


def write_stack(
    inp_paths: list[pathlib.Path],
    axis: utils.StackableAxis,
    out_path: pathlib.Path,
) -> None:
    """Stack the input images along the given axis.

    This will read all the images from the input directory and stack them along
    the given axis. The output will be written to the output directory.

    Args:
        inp_paths: List of paths to input images. Should be sorted by filepattern.
        axis: Axis to stack images along.
        out_path: Path to output directory.
    """
    logger.debug(f"Stacking images along {axis} axis.")
    logger.debug(f"Input: {inp_paths}")
    logger.debug(f"Output: {out_path}")

    # Get the metadata from the first image
    with bfio.BioReader(inp_paths[0]) as reader:
        metadata = reader.metadata
        z_unit_distance = utils.z_unit_distance(reader)

    # Open all the input images
    readers = [bfio.BioReader(p) for p in inp_paths]

    # Create the output writer
    with bfio.BioWriter(out_path, metadata=metadata) as writer:
        if axis.value == "z":
            writer.Z = len(inp_paths)
            writer.ps_z = z_unit_distance
        elif axis.value == "c":
            writer.C = len(inp_paths)
        elif axis.value == "t":
            writer.T = len(inp_paths)

        for y_min in range(0, writer.Y, utils.TILE_SIZE):
            y_max = min(writer.Y, y_min + utils.TILE_SIZE)

            for x_min in range(0, writer.X, utils.TILE_SIZE):
                x_max = min(writer.X, x_min + utils.TILE_SIZE)

                # Read the tiles from the input images
                tiles = [
                    axis.read_tile(r, (x_min, x_max), (y_min, y_max)) for r in readers
                ]

                # Write the tiles to the output image
                for i, tile in enumerate(tiles):
                    axis.write_tile(writer, (x_min, x_max), (y_min, y_max), tile, i)

    # Close the readers
    [r.close() for r in readers]


def copy_stack(
    inp_paths: list[pathlib.Path],
    axis: utils.StackableAxis,
    out_path: pathlib.Path,
) -> None:
    """Copy the input images to the output directory.

    This will copy the input images to the output directory without any stacking.

    Args:
        inp_paths: List of paths to input images. Should be sorted by filepattern.
        axis: Axis to stack images along.
        out_path: Path to output directory.

    Raises:
        ValueError: If any of the input images or the output image is not .ome.zarr.
    """
    if not (
        all(p.name.endswith(".ome.zarr") for p in inp_paths)
        and out_path.name.endswith(".ome.zarr")
    ):
        msg = "Cannot copy, not all files are .ome.zarr."
        logger.error(msg)
        raise ValueError(msg)

    logger.debug("Copying images.")
    logger.debug(f"Input: {inp_paths}")
    logger.debug(f"Output: {out_path}")

    for i, p in enumerate(inp_paths):
        logger.info(f"Copying image {i} from {p.name} to {out_path.name}")

    # Get the metadata from the first image
    with bfio.BioReader(inp_paths[0]) as reader:
        metadata = reader.metadata
        z_unit_distance = utils.z_unit_distance(reader)

    # Create the output writer
    with bfio.BioWriter(out_path, metadata=metadata) as writer:
        if axis.value == "z":
            writer.Z = len(inp_paths)
            writer.ps_z = z_unit_distance
            writer[:, :, 0, :, :] = reader[:, :, 0, :, :]
        elif axis.value == "c":
            writer.C = len(inp_paths)
            writer[:, :, :, 0, :] = reader[:, :, :, 0, :]
        elif axis.value == "t":
            writer.T = len(inp_paths)
            writer[:, :, :, :, 0] = reader[:, :, :, :, 0]

        # writer[0:utils.TILE_SIZE, 0:utils.TILE_SIZE, 0, 0, 0] = numpy.zeros(

        # for y_min in range(0, writer.Y, utils.TILE_SIZE):

        #     for x_min in range(0, writer.X, utils.TILE_SIZE):

        for i, p in enumerate(inp_paths):
            copy_zarr_stack(p, i, axis, out_path)

    logger.debug(f"Done copying {out_path}")


def copy_zarr_stack(
    inp_path: pathlib.Path,
    index: int,
    axis: utils.StackableAxis,
    out_path: bfio.BioWriter,
) -> None:
    """Copy image stack.

    This function works like write_stack except it copies rather than performs a
    read and write operation.

    This can only be used by .ome.zarr files using v0.4.

    Args:
        inp_path: Path to input image file.
        index: Index along dimension being stacked.
        axis: Name of the axis being stacked.
        out_path: Path to output zarr file.
    """
    base_path = inp_path / "0"
    destination = out_path / "0"

    for src in base_path.rglob("*"):
        chunk = str(src.relative_to(base_path))
        if chunk.startswith("."):
            logger.debug(f"Skipping {chunk}")
            continue

        logger.debug(f"src: {src}")
        logger.debug(f"Chunk: {chunk}")

        dims = chunk.split("." if "." in chunk else "/")

        logger.debug(f"dims: {dims}")

        if len(dims) >= 3:  # noqa: PLR2004
            if axis.value == "z":
                dims[2] = str(index)
            elif axis.value == "c":
                dims[1] = str(index)
            elif axis.value == "t":
                dims[0] = str(index)

        new_slice = "/".join(dims)
        logger.debug(f"New slice: {new_slice}")

        destination.joinpath(new_slice).parent.mkdir(parents=True, exist_ok=True)
        dest = destination.joinpath(new_slice)

        logger.debug(f"Copying {src} to {dest}")
        if src.is_file():
            shutil.copyfile(src, dest)
        else:
            shutil.copytree(src, dest, dirs_exist_ok=True)

    logger.debug(f"Done copying {inp_path} to {out_path}")
