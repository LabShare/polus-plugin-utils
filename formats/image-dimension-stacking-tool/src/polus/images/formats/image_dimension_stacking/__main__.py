"""Image dimension stacking package."""

import json
import logging
import os
import pathlib
import warnings

import filepattern
import tqdm
import typer
from polus.images.formats.image_dimension_stacking import copy_stack
from polus.images.formats.image_dimension_stacking import utils
from polus.images.formats.image_dimension_stacking import write_stack

warnings.filterwarnings("ignore")

logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
POLUS_LOG = getattr(logging, os.environ.get("POLUS_LOG", "INFO"))
logger = logging.getLogger("polus.images.formats.image_dimension_stacking")
logger.setLevel(POLUS_LOG)

app = typer.Typer()


@app.command()
def main(
    inp_dir: pathlib.Path = typer.Option(
        ...,
        "--inpDir",
        help="Path to input directory containing binary images.",
        exists=True,
        readable=True,
        resolve_path=True,
        file_okay=False,
        dir_okay=True,
    ),
    file_pattern: str = typer.Option(
        ...,
        "--filePattern",
        help="Filename pattern used to separate data.",
    ),
    axis: utils.StackableAxis = typer.Option(
        utils.StackableAxis.Z,
        "--axis",
        help="Axis to stack images along.",
    ),
    out_dir: pathlib.Path = typer.Option(
        ...,
        "--outDir",
        help="Output collection.",
        exists=True,
        writable=True,
        resolve_path=True,
        file_okay=False,
        dir_okay=True,
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        help="Generate preview of expected outputs.",
    ),
) -> None:
    """Image dimension stacking tool."""
    # Get the file pattern
    fp = filepattern.FilePattern(inp_dir, file_pattern)
    variables = fp.get_variables()

    # Check if the axis is present among the variables
    if axis.value not in variables:
        msg = f"Axis {axis} not present among the variables {variables}."
        logger.error(msg)
        raise ValueError(msg)

    # Collect the files into groups to stack
    groups: dict[pathlib.Path, list[pathlib.Path]] = {}

    # Group the files by all variables except the axis
    group_by = [v for v in variables if v != axis.value]
    for _, files in fp(group_by=group_by):
        out_path = out_dir / fp.output_name(files)
        groups[out_path] = [p for _, [p] in files]

    if preview:
        with (out_dir / "preview.json").open("w") as f:
            preview_data = {"outDir": [str(p) for p in groups]}
            json.dump(preview_data, f, indent=2)
        return

    # TODO: Use some parallelism here
    for out_path, inp_paths in tqdm.tqdm(
        groups.items(),
        desc="Stacking groups",
        total=len(groups),
    ):
        if str(out_path).endswith(".ome.zarr"):
            copy_stack(inp_paths, axis, out_path)
        else:
            write_stack(inp_paths, axis, out_path)


if __name__ == "__main__":
    app()
