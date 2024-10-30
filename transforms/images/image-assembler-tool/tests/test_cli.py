"""Testing the Command Line Tool."""

import faulthandler
import json
from pathlib import Path

from polus.images.transforms.images.image_assembler.__main__ import app
from typer.testing import CliRunner

faulthandler.enable()


def test_cli(local_data: tuple[Path, Path, Path, Path]):
    """Test the command line."""
    runner = CliRunner()

    inp_dir, stitch_dir, out_dir, _ = local_data

    result = runner.invoke(
        app,
        [
            "--imgPath",
            str(inp_dir),
            "--stitchPath",
            str(stitch_dir),
            "--outDir",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0


def test_cli_preview(local_data: tuple[Path, Path, Path, Path]):
    """Test the preview option."""
    runner = CliRunner()

    inp_dir, stitch_dir, out_dir, _ = local_data

    result = runner.invoke(
        app,
        [
            "--imgPath",
            str(inp_dir),
            "--stitchPath",
            str(stitch_dir),
            "--outDir",
            str(out_dir),
            "--preview",
        ],
    )

    print(result.exception)
    print(result.stdout)
    assert result.exit_code == 0

    with Path.open(out_dir / "preview.json") as file:
        plugin_json = json.load(file)

    # verify we generate the preview file
    result = plugin_json["outputDir"]
    assert len(result) == 1
    assert Path(result[0]).name == "img_r00(1-2)_c00(1-2).ome.tif"


def test_cli_bad_input(local_data: tuple[Path, Path, Path, Path]):
    """Test bad inputs."""
    runner = CliRunner()

    inp_dir, stitch_dir, out_dir, _ = local_data
    inp_dir = Path("does_not_exists")

    result = runner.invoke(
        app,
        [
            "--imgPath",
            str(inp_dir),
            "--stitchPath",
            str(stitch_dir),
            "--outDir",
            str(out_dir),
        ],
    )

    assert result.exc_info[0] is SystemExit
