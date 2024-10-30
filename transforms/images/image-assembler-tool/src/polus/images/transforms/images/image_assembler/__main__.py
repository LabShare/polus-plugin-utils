"""Package entrypoint for Image Assembler."""
import json
import logging
from os import environ
from pathlib import Path

import typer

from .image_assembler import assemble_images
from .image_assembler import generate_output_filepaths

logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
POLUS_LOG = getattr(logging, environ.get("POLUS_LOG", "INFO"))
logger = logging.getLogger("polus.images.transforms.images.image_assembler")
logger.setLevel(POLUS_LOG)
logging.getLogger("bfio").setLevel(POLUS_LOG)

POLUS_IMG_EXT = environ.get("POLUS_IMG_EXT", ".ome.tif")

app = typer.Typer(help="Image Assembler plugin.")


def generate_preview(
    img_path: Path,
    stitch_path: Path,
    out_dir: Path,
    timeslice_naming: bool,
) -> None:
    """Generate preview of the plugin outputs."""
    output_paths = generate_output_filepaths(
        img_path,
        stitch_path,
        out_dir,
        timeslice_naming,
    )

    preview: dict[str, list[str]] = {
        "outputDir": [],
    }

    for filepath in output_paths:
        preview["outputDir"].append(str(filepath))

    with Path.open(out_dir / "preview.json", "w") as fw:
        json.dump(preview, fw, indent=2)


@app.command()
def main(
    img_path: Path = typer.Option(
        ...,
        "--imgPath",
        "-i",
        help="""Absolute path to the input image collection
        directory to be processed by this plugin.""",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    stitch_path: Path = typer.Option(
        ...,
        "--stitchPath",
        "-s",
        help="Absolute path to a stitching vector directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    out_dir: Path = typer.Option(
        ...,
        "--outDir",
        "-o",
        help="Absolute path to the output collection directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
    ),
    timeslice_naming: bool = typer.Option(
        False,
        "--timesliceNaming",
        "-t",
        help="Use timeslice number as image name.",
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        "-p",
        help="Generate preview of expected outputs.",
    ),
) -> None:
    """Assemble images from a single stitching vector."""
    logger.info(f"imgPath: {img_path}")
    logger.info(f"stitchPath: {stitch_path}")
    logger.info(f"outDir: {out_dir}")
    logger.info(f"timesliceNaming: {timeslice_naming}")

    # if the input image collection contains a images subdirectory, we use that
    # TODO this is an artifact from WIPP integration.
    # This should eventually be removed from the implementation.
    if img_path.joinpath("images").is_dir():
        img_path = img_path.joinpath("images")
        logger.warning(f"imgPath : images subdirectory found so using that: {img_path}")

    if preview:
        generate_preview(img_path, stitch_path, out_dir, timeslice_naming)
        logger.info(f"generating preview data in {out_dir}")
        return

    assemble_images(img_path, stitch_path, out_dir, timeslice_naming)


if __name__ == "__main__":
    app()
