"""Tests for the CLI."""

import pathlib
import shutil

import bfio
import numpy
import pytest
import scipy.ndimage
import typer.testing

from polus.images.formats.image_dimension_stacking.__main__ import app


def gen_images(
    inp_dir: pathlib.Path,
    pattern: str,
    axis: str,
    num_images: int,
    size: int,
) -> list[pathlib.Path]:
    """Generate synthetic images."""

    # Generate a image with a square in the middle
    square = numpy.zeros((size, size), dtype=numpy.uint8)
    lq = size // 4
    hq = 3 * size // 4
    square[lq:hq, lq:hq] = 255

    paths = []
    for i in range(num_images):
        # Rotate the image by i degrees
        img = scipy.ndimage.rotate(square, i * 3, reshape=False)

        name = pattern.format(**{axis: i})
        path = inp_dir / name
        paths.append(path)

        with bfio.BioWriter(path) as writer:
            writer.X = size
            writer.Y = size
            writer.Z = 1
            writer.C = 1
            writer.T = 1
            writer.dtype = square.dtype

            writer.ps_x = (1, "mm")
            writer.ps_y = (1, "mm")

            writer[:] = img.astype(numpy.uint8)

    return paths


@pytest.mark.parametrize("axis", ["z", "c", "t"])
@pytest.mark.parametrize("ext", ["ome.tif", "ome.zarr"])
def test_cli(
    axis: str,
    ext: str,
) -> None:
    """Test the command line."""

    data_dir = pathlib.Path(__file__).parent / "data"
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(exist_ok=True)

    # data_dir = pathlib.Path(tempfile.mkdtemp(suffix="_data_dir"))
    inp_dir = data_dir / "input"
    out_dir = data_dir / "output"

    for d in [inp_dir, out_dir]:
        d.mkdir(exist_ok=True)

    num_images = 10
    size = 1024

    pattern = f"image_{axis}" + "{" + f"{axis}" + ":03d}" + f".{ext}"
    inp_paths = gen_images(inp_dir, pattern, axis, num_images, size)
    assert len(inp_paths) == num_images

    pattern = f"image_{axis}" + "{" + f"{axis}" + ":d+}" + f".{ext}"

    runner = typer.testing.CliRunner()
    result = runner.invoke(
        app,
        [
            "--inpDir",
            str(inp_dir),
            "--filePattern",
            pattern,
            "--axis",
            axis,
            "--outDir",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0

    # Check the output
    start = f"{0:03d}"
    end = f"{num_images - 1:03d}"
    out_path = out_dir / f"image_{axis}({start}-{end}).{ext}"
    assert out_path.exists()

    with bfio.BioReader(out_path) as out_reader:
        assert out_reader.X == size
        assert out_reader.Y == size

        if axis == "z":
            assert out_reader.Z == num_images
            assert out_reader.C == 1
            assert out_reader.T == 1
        elif axis == "c":
            assert out_reader.Z == 1
            assert out_reader.C == num_images
            assert out_reader.T == 1
        elif axis == "t":
            assert out_reader.Z == 1
            assert out_reader.C == 1
            assert out_reader.T == num_images

        for i, p in enumerate(inp_paths[1:], start=1):
            if axis == "z":
                out_img = out_reader[:, :, i, 0, 0]
            elif axis == "c":
                out_img = out_reader[:, :, 0, i, 0]
            elif axis == "t":
                out_img = out_reader[:, :, 0, 0, i]
            else:
                pytest.fail(f"Unknown axis {axis}")

            out_img = numpy.squeeze(out_img)

            with bfio.BioReader(p) as inp_reader:
                inp_img = numpy.squeeze(inp_reader[:, :, 0, 0, 0])

            error = numpy.mean(numpy.abs(out_img - inp_img))

            numpy.testing.assert_array_equal(
                inp_img,
                out_img,
                err_msg=f"Image {i} does not match. Error: {error}",
            )
