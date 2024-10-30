"""CLI for rt-cetsa-plate-extraction-tool."""

import json
import logging
import os
from pathlib import Path

import filepattern
import typer
from polus.images.segmentation.rt_cetsa_plate_extraction import extract_plates

# Initialize the logger
logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger(__file__)
logger.setLevel(os.environ.get("POLUS_LOG", logging.INFO))

POLUS_IMG_EXT = os.environ.get("POLUS_IMG_EXT", ".ome.tiff")

app = typer.Typer()


@app.command()
def main(
    inp_dir: Path = typer.Option(
        ...,
        "--inpDir",
        help="Input directory containing the plate images.",
        exists=True,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    pattern: str = typer.Option(
        ".+",
        "--filePattern",
        help="Pattern to match the files in the input directory.",
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        help="Preview the files that will be processed.",
    ),
    out_dir: Path = typer.Option(
        ...,
        "--outDir",
        help="Output directory to save the results.",
        exists=True,
        dir_okay=True,
        writable=True,
        resolve_path=True,
    ),
) -> None:
    """CLI for rt-cetsa-plate-extraction-tool."""
    logger.info("Starting the CLI for rt-cetsa-plate-extraction-tool.")
    logger.info(f"Input directory: {inp_dir}")
    logger.info(f"File Pattern: {pattern}")
    logger.info(f"Output directory: {out_dir}")

    if preview:
        fp = filepattern.FilePattern(inp_dir, pattern)
        inp_files: list[Path] = [f[1][0] for f in fp()]  # type: ignore[assignment]

        if len(inp_files) < 1:
            msg = "no input files captured by the pattern."
            raise ValueError(msg)

        out_json = {
            "images": [
                (Path("images") / f"{f.stem}{POLUS_IMG_EXT}").as_posix()
                for f in inp_files
            ],
            "masks": [
                (Path("masks") / f"{inp_files[0].stem}{POLUS_IMG_EXT}").as_posix(),
            ],
            "params": [Path("params") / "plate.json"],
        }

        with (out_dir / "preview.json").open("w") as f:
            json.dump(out_json, f, indent=2)

    else:
        extract_plates(inp_dir, pattern, out_dir)


if __name__ == "__main__":
    app()
