"""Helpers for the tool."""

import enum
import logging
import os

import bfio
import numpy

POLUS_LOG = getattr(logging, os.environ.get("POLUS_LOG", "INFO"))
POLUS_IMG_EXT = os.environ.get("POLUS_IMG_EXT", ".ome.zarr")
TILE_SIZE = 1024

# Units for conversion
UNITS = {
    "m": 10**9,
    "cm": 10**7,
    "mm": 10**6,
    "µm": 10**3,
    "nm": 1,
    "Å": 10**-1,
}


def make_logger(name: str) -> logging.Logger:
    """Create a logger with the given name."""
    logger = logging.getLogger(name)
    logger.setLevel(POLUS_LOG)
    return logger


logger = make_logger(__name__)


def z_unit_distance(reader: bfio.BioReader) -> tuple[float, str]:
    """Get physical z-distance.

    This estimates zdistance if not provided by averaging physical distances of x and y.

    Args:
        reader: BioReader object.

    Returns:
        A tuple of float and string values.
    """
    # Get the physical z-distance if available, set to physical x if not
    ps_z = reader.ps_z

    # If the z-distances are undefined, average the x and y together
    if None in ps_z:
        # Get the size and units for x and y
        x_val, xunits = reader.ps_x
        y_val, yunits = reader.ps_y

        x_units = xunits.value
        y_units = yunits.value

        # Convert x and y values to the same units and average
        z_val = (x_val * UNITS[x_units] + y_val * UNITS[y_units]) / 2

        # Set z units to the smaller of the units between x and y
        z_units = x_units if UNITS[x_units] < UNITS[y_units] else y_units

        # Convert z to the proper unit scale
        z_val /= UNITS[z_units]
        ps_z = (z_val, z_units)

        if not ps_z:
            msg = f"Unable to find physical z-size {ps_z}"
            raise ValueError(
                msg,
            )

    return ps_z


class StackableAxis(str, enum.Enum):
    """Axis along which images can be stacked."""

    Z = "z"
    C = "c"
    T = "t"

    def read_tile(
        self,
        reader: bfio.BioReader,
        x: tuple[int, int],
        y: tuple[int, int],
    ) -> numpy.ndarray:
        """Read a tile from the reader."""
        if self == StackableAxis.Z:
            return reader[y[0] : y[1], x[0] : x[1], 0, :, :]
        if self == StackableAxis.C:
            return reader[y[0] : y[1], x[0] : x[1], :, 0, :]
        if self == StackableAxis.T:
            return reader[y[0] : y[1], x[0] : x[1], :, :, 0]
        return None

    def write_tile(  # noqa: PLR0913
        self,
        writer: bfio.BioWriter,
        x: tuple[int, int],
        y: tuple[int, int],
        tile: numpy.ndarray,
        index: int,
    ) -> None:
        """Write a tile to the writer."""
        if self == StackableAxis.Z:
            writer[y[0] : y[1], x[0] : x[1], index, :, :] = tile
        if self == StackableAxis.C:
            writer[y[0] : y[1], x[0] : x[1], :, index, :] = tile
        if self == StackableAxis.T:
            writer[y[0] : y[1], x[0] : x[1], :, :, index] = tile
