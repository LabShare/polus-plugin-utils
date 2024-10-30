"""Functions for performing image calculations."""

import enum
import logging
import multiprocessing
import os
import pathlib
import typing

import bfio
import numpy

# Import environment variables
POLUS_LOG = getattr(logging, os.environ.get("POLUS_LOG", "INFO"))
POLUS_IMG_EXT = os.environ.get("POLUS_IMG_EXT", ".ome.tif")
MAX_WORKERS = max(1, multiprocessing.cpu_count() // 2)

CHUNK_SIZE = 4_096
SUFFIX_LEN = 6


class Operation(str, enum.Enum):
    """The operations that can be performed on the images."""

    Multiply = "multiply"
    Divide = "divide"
    Add = "add"
    Subtract = "subtract"
    And = "and"
    Or = "or"
    Xor = "xor"
    Min = "min"
    Max = "max"
    AbsDiff = "absdiff"

    @classmethod
    def variants(cls) -> list["Operation"]:
        """Returns a list of all the variants of the operation."""
        return [
            cls.Multiply,
            cls.Divide,
            cls.Add,
            cls.Subtract,
            cls.And,
            cls.Or,
            cls.Xor,
            cls.Min,
            cls.Max,
            cls.AbsDiff,
        ]

    def func(self) -> typing.Callable[[numpy.ndarray, numpy.ndarray], numpy.ndarray]:
        """Returns the function associated with the operation."""
        if self.value == "multiply":
            f = numpy.multiply
        elif self.value == "divide":
            f = numpy.divide
        elif self.value == "add":
            f = numpy.add
        elif self.value == "subtract":
            f = numpy.subtract
        elif self.value == "and":
            f = numpy.bitwise_and
        elif self.value == "or":
            f = numpy.bitwise_or
        elif self.value == "xor":
            f = numpy.bitwise_xor
        elif self.value == "min":
            f = numpy.minimum
        elif self.value == "max":
            f = numpy.maximum
        else:  # self.value == "absdiff":

            def f(x: numpy.ndarray, y: numpy.ndarray) -> numpy.ndarray:
                return numpy.abs(numpy.subtract(x, y))

        return f


def _process_chunk(  # noqa: PLR0913
    primary_reader: bfio.BioReader,
    secondary_reader: bfio.BioReader,
    x: int,
    x_max: int,
    y: int,
    y_max: int,
    z: int,
    writer: bfio.BioWriter,
    operation: Operation,
) -> None:
    """Process on chunk of the images in a thread/process."""
    left = primary_reader[y:y_max, x:x_max, z]
    right = secondary_reader[y:y_max, x:x_max, z]
    writer[y:y_max, x:x_max, z] = operation.func()(
        left,
        right.astype(primary_reader.dtype),
    )


def process_image(
    primary_image: pathlib.Path,
    secondary_image: pathlib.Path,
    output_dir: pathlib.Path,
    operation: Operation,
) -> None:
    """Applies the specified operation on the two images and saves the output image.

    Args:
        primary_image: The primary image file.
        secondary_image: The secondary image file.
        output_dir: The output directory.
        operation: The operation to perform on the images.
    """
    with (
        bfio.BioReader(primary_image, max_workers=1) as primary_reader,
        bfio.BioReader(secondary_image, max_workers=1) as secondary_reader,
    ):
        input_extension = "".join(
            [s for s in primary_image.suffixes[-2:] if len(s) < SUFFIX_LEN],
        )
        out_name = primary_image.name.replace(input_extension, POLUS_IMG_EXT)
        out_path = output_dir.joinpath(out_name)

        # Initialize the output image
        with bfio.BioWriter(out_path, metadata=primary_reader.metadata) as writer:
            writer.dtype = primary_reader.dtype

            for z in range(primary_reader.Z):
                for x in range(0, primary_reader.X, CHUNK_SIZE):
                    x_max = min(x + CHUNK_SIZE, primary_reader.X)
                    for y in range(0, primary_reader.Y, CHUNK_SIZE):
                        y_max = min(y + CHUNK_SIZE, primary_reader.Y)

                        _process_chunk(
                            primary_reader,
                            secondary_reader,
                            x,
                            x_max,
                            y,
                            y_max,
                            z,
                            writer,
                            operation,
                        )
