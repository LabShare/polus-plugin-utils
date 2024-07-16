"""Provides the ImageJ filter convolve tool."""


__version__ = "0.5.1-dev0"


import logging
import os
import pathlib
import typing

import bfio
import imagej
import numpy
from polus.images.segmentation.imagej_threshold_apply import ij_typing

TILE_SIZE = 2048

POLUS_LOG = getattr(logging, os.environ.get("POLUS_LOG", "INFO"))
POLUS_EXT = os.environ.get("POLUS_EXT", ".ome.tif")

logger = logging.getLogger("polus.images.transforms.imagej_filter_convolve")
logger.setLevel(POLUS_LOG)


def filter_convolve(
    inp_path: pathlib.Path,
    filter_path: pathlib.Path,
    out_dir: pathlib.Path,
    ij: typing.Any = None,
) -> None:
    """Segment an image."""
    if ij is None:
        logger.debug("Starting ImageJ...")
        ij = imagej.init("sc.fiji:fiji:2.1.1+net.imagej:imagej-legacy:0.37.4")
        logger.debug(f"Loaded ImageJ version: {ij.getVersion()}")

    logger.info(f"{ij.op().help('filter.convolve')}")

    with bfio.BioReader(filter_path) as br_filter:
        filter_img = br_filter[:].squeeze()

    inp_name = (inp_path.name).split(".")[0]
    out_path = out_dir / f"{inp_name}{POLUS_EXT}"
    with bfio.BioReader(inp_path) as br_img:
        dtype = br_img.dtype
        ij_type: ij_typing.IjType = ij_typing.IjType.from_dtype(dtype)
        filter_img = ij_type.cast_image_to_ij(ij, filter_img)

        with bfio.BioWriter(out_path, metadata=br_img.metadata) as bw:
            for y_min in range(0, br_img.Y, TILE_SIZE):
                y_max = min(y_min + TILE_SIZE, br_img.Y)
                for x_min in range(0, br_img.X, TILE_SIZE):
                    x_max = min(x_min + TILE_SIZE, br_img.X)
                    logger.debug(
                        f"Processing tile: ({x_min}:{x_max}, {y_min}:{y_max})",
                    )
                    img_tile = br_img[y_min:y_max, x_min:x_max, ...]
                    img_tile = ij_type.cast_image_to_ij(ij, img_tile)

                    img_tile = ij.op().filter().convolve(img_tile, filter_img)
                    img_tile = ij_type.cast_ij_to_image(ij, img_tile)

                    # Fill nan values with 0
                    img_tile[numpy.isnan(img_tile)] = 0
                    bw[y_min:y_max, x_min:x_max, ...] = img_tile

    logger.debug(f"Segmentation complete: {out_path}")
