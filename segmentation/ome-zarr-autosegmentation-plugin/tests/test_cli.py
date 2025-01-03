"""Testing the Command Line Tool."""

import faulthandler
import json
from pathlib import Path
from typer.testing import CliRunner

from .conftest import FixtureReturnType

from polus.plugins.images.segmentation.ome_zarr_autosegmentation.__main__ import app

faulthandler.enable()


def test_cli(generate_test_data : FixtureReturnType) -> None:  # noqa
    """Test the command line."""
    inp_dir, out_dir, ground_truth_dir, img_path, ground_truth_path = generate_test_data #noqa

    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "--inpDir",
            inp_dir,
            "--outDir",
            out_dir,
        ],
    )

    assert result.exit_code == 0

def test_cli_short(generate_test_data : FixtureReturnType):  # noqa
    """Test the command line."""
    runner = CliRunner()

    inp_dir, out_dir, _, _, _ = generate_test_data #noqa

    result = runner.invoke(
        app,
        [
            "-i",
            inp_dir,
            "-o",
            out_dir,
        ],
    )

    assert result.exit_code == 0

def test_cli_preview(generate_test_data : FixtureReturnType):  # noqa
    """Test the preview option."""
    runner = CliRunner()

    inp_dir, out_dir, _, _, _ = generate_test_data #noqa


    result = runner.invoke(
        app,
        [
            "--inpDir",
            inp_dir,
            "--outDir",
            out_dir,
            "--preview",
        ],
    )

    assert result.exit_code == 0

    with Path.open(out_dir / "preview.json") as file:
        plugin_json = json.load(file)

    # verify we generate the preview file
    assert plugin_json == {}


def test_cli_bad_input(generate_test_data : FixtureReturnType):  # noqa
    """Test bad inputs."""
    runner = CliRunner()

    inp_dir, out_dir, _, _, _ = generate_test_data #noqa
    # replace with a bad path
    inp_dir = "/does_not_exists"

    result = runner.invoke(
        app,
        [
            "--inpDir",
            inp_dir,
            "--outDir",
            out_dir,
        ],
    )

    assert result.exc_info[0] is SystemExit
