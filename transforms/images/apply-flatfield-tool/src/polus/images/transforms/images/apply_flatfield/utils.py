"""Utilities for the apply flatfield plugin."""
import logging
import multiprocessing
import os
import pathlib
import typing

import bfio
import numpy

POLUS_LOG = getattr(logging, os.environ.get("POLUS_LOG", "INFO"))
POLUS_IMG_EXT = os.environ.get("POLUS_IMG_EXT", ".ome.tif")
MAX_WORKERS = max(1, multiprocessing.cpu_count() // 2)


def load_img(path: pathlib.Path, i: int) -> typing.Tuple[int, numpy.ndarray]:
    """Load image from path.

    This method is intended to be used in a thread. The index is used to
    identify the image after it has been loaded so that it images can be sorted
    in the correct order.

    Args:
        path: path to image
        i: index of image
    """
    with bfio.BioReader(path, MAX_WORKERS) as reader:
        image = reader[:, :, :, 0, 0].squeeze()
    return i, image


def save_img(
    inp_path: pathlib.Path,
    image: numpy.ndarray,
    out_dir: pathlib.Path,
) -> None:
    """Save image to disk.

    Args:
        inp_path: path to input image
        image: image to be saved
        out_dir: directory to save image
    """
    out_stem = inp_path.stem
    if ".ome" in out_stem:
        out_stem = out_stem.split(".ome")[0]

    out_path = out_dir / f"{out_stem}{POLUS_IMG_EXT}"
    with bfio.BioReader(inp_path, MAX_WORKERS) as reader, bfio.BioWriter(
        out_path,
        MAX_WORKERS,
        metadata=reader.metadata,
    ) as writer:
        writer.dtype = image.dtype
        writer[:] = image
