"""Provides the CLI for the Apply Flatfield plugin."""

import json
import logging
import pathlib
import typing

import typer
from polus.images.transforms.images.apply_flatfield import apply, utils

# Initialize the logger
logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger("polus.images.transforms.images.apply_flatfield")
logger.setLevel(utils.POLUS_LOG)

app = typer.Typer()


@app.command()
def main(  # noqa: PLR0913
    img_dir: pathlib.Path = typer.Option(
        ...,
        "--imgDir",
        help="Path to input images.",
        exists=True,
        readable=True,
        resolve_path=True,
        file_okay=False,
    ),
    img_pattern: str = typer.Option(
        ...,
        "--imgPattern",
        help="Filename pattern used to select images from imgDir.",
    ),
    ff_dir: pathlib.Path = typer.Option(
        ...,
        "--ffDir",
        help="Path to flatfield (and optionally darkfield) images.",
        exists=True,
        readable=True,
        resolve_path=True,
        file_okay=False,
    ),
    ff_pattern: str = typer.Option(
        ...,
        "--ffPattern",
        help="Filename pattern used to select flatfield components from ffDir.",
    ),
    df_pattern: typing.Optional[str] = typer.Option(
        None,
        "--dfPattern",
        help="Filename pattern used to select darkfield components from ffDir.",
    ),
    out_dir: pathlib.Path = typer.Option(
        ...,
        "--outDir",
        help="Path to output directory.",
        exists=True,
        writable=True,
        resolve_path=True,
        file_okay=False,
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        help="Preview the output without saving.",
    ),
    keep_orig_dtype: typing.Optional[bool] = typer.Option(
        True,
        "--keepOrigDtype",
        help="Keep the original dtype of the input images.",
    ),
) -> None:
    """CLI for the Apply Flatfield plugin.

    The variables used in ffPattern and dfPattern must be a subset of those used
    in imgPattern.

    If dfPattern is not specified, then darkfield correction will not be
    applied.
    """
    logger.info("Starting Apply Flatfield plugin ...")

    logger.info(f"imgDir = {img_dir}")
    logger.info(f"imgPattern = {img_pattern}")
    logger.info(f"ffDir = {ff_dir}")
    logger.info(f"ffPattern = {ff_pattern}")
    logger.info(f"dfPattern = {df_pattern}")
    logger.info(f"outDir = {out_dir}")
    logger.info(f"preview = {preview}")
    logger.info(f"keepOrigDtype = {keep_orig_dtype}")

    out_files = apply(
        img_dir=img_dir,
        img_pattern=img_pattern,
        ff_dir=ff_dir,
        ff_pattern=ff_pattern,
        df_pattern=df_pattern,
        out_dir=out_dir,
        preview=preview,
        keep_orig_dtype=keep_orig_dtype,
    )

    if preview:
        with out_dir.joinpath("preview.json").open("w") as writer:
            out_dict = {"files": [p.name for p in out_files]}
            json.dump(out_dict, writer, indent=2)


if __name__ == "__main__":
    app()
