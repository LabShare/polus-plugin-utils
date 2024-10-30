"""Czi Extract Plugin."""
import json
import logging
import os
from multiprocessing import cpu_count
from pathlib import Path
from typing import Any
from typing import Optional

import filepattern as fp
import polus.plugins.formats.czi_extract.czi as cz
import typer

# Import environment variables
POLUS_EXT = os.environ.get("POLUS_EXT", ".ome.tif")

app = typer.Typer()

# Initialize the logger
logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger("polus.plugins.formats.czi_extract")


@app.command()
def main(
    inp_dir: Path = typer.Option(
        ...,
        "--inpDir",
        "-i",
        help="Path to folder with CZI files",
    ),
    file_pattern: str = typer.Option(
        ".*.czi",
        "--filePattern",
        "-f",
        help="Pattern use to parse filenames",
    ),
    out_dir: Path = typer.Option(
        ...,
        "--outDir",
        "-o",
        help="Output directory",
    ),
    preview: Optional[bool] = typer.Option(
        False,
        "--preview",
        help="Output a JSON preview of files",
    ),
) -> None:
    """Extracts individual fields of view from a CZI file and saves as OME TIFF."""
    logger.info(f"--inpDir = {inp_dir}")
    logger.info(f"--filePattern = {file_pattern}")
    logger.info(f"--outDir = {out_dir}")

    inp_dir = inp_dir.resolve()
    out_dir = out_dir.resolve()

    assert inp_dir.exists(), f"{inp_dir} does not exist!! Please check input path again"
    assert (
        out_dir.exists()
    ), f"{out_dir} does not exist!! Please check output path again"

    files = fp.FilePattern(inp_dir, file_pattern)

    file_ext = all(Path(f[1][0].name).suffix for f in files())
    assert (
        file_ext is True
    ), f"{inp_dir} does not contain all czi files!! Please check input directory again"

    if preview:
        with Path.open(Path(out_dir, "preview.json"), "w") as jfile:
            out_json: dict[str, Any] = {
                "filepattern": file_pattern,
                "outDir": [],
            }
            for file in files():
                out_name = file[1][0].name.replace(
                    "".join(file[1][0].suffixes),
                    ".ome.tif",
                )
                out_json["outDir"].append(out_name)
            json.dump(out_json, jfile, indent=2)
    else:
        for file in files():
            cz.extract_fovs(file[1][0], out_dir)

if __name__ == "__main__":
    app()
