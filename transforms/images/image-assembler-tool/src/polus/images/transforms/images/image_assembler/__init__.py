"""Image Assembler Plugin."""

__version__ = "1.5.0-dev0"

from .image_assembler import (  # noqa
    assemble_images,
    generate_output_filepaths,
)

__all__ = ["assemble_images", "generate_output_filepaths"]
