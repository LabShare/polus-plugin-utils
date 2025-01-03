"""Package entrypoint for the ome_zarr_autosegmentation package."""

# Base packages
import json
import logging
from os import environ
from pathlib import Path

import typer
from polus.images.segmentation.ome_zarr_autosegmentation.autosegmentation import autosegmentation

logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
POLUS_LOG = getattr(logging, environ.get("POLUS_LOG", "INFO"))
logger = logging.getLogger("polus.images.segmentation.ome_zarr_autosemgentation")
logger.setLevel(POLUS_LOG)

app = typer.Typer(help="ome_zarr_autosegmentation.")

def generate_preview(
    in_dir: Path,
    out_dir: Path,
) -> None:
    """Generate preview of the plugin outputs."""

    preview = {}

    with Path.open(out_dir / "preview.json", "w") as fw:
        json.dump(preview, fw, indent=2)

@app.command()
def main(
    inp_dir: Path = typer.Option(
        ...,
        "--inpDir",
        "-i",
        help="Input directory to be processed.",
        exists=True,
        readable=True,
        file_okay=False,
        resolve_path=True,
    ),
    out_dir: Path = typer.Option(
        ...,
        "--outDir",
        "-o",
        help="Output directory.",
        exists=False,
        writable=True,
        file_okay=False,
        resolve_path=True,
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        "-v",
        help="Preview of expected outputs (dry-run)",
        show_default=False,
    ),
):
    """ome_zarr_autosegmentation."""
    logger.info(f"inpDir: {inp_dir}")
    logger.info(f"outDir: {out_dir}")

    if preview:
        generate_preview(inp_dir, out_dir)
        logger.info(f"generating preview data in : {out_dir}.")
        return

    autosegmentation(inp_dir, out_dir)


if __name__ == "__main__":
    app()
