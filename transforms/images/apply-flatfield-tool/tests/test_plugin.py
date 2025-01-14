"""Tests for the plugin."""
import itertools
import logging
import pathlib
import shutil
import tempfile
import typing

import bfio
import numpy
import pytest
import typer.testing
from polus.images.transforms.images.apply_flatfield import apply
from polus.images.transforms.images.apply_flatfield.__main__ import app

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _make_random_image(
    path: pathlib.Path,
    rng: numpy.random.Generator,
    size: int,
    dtype: numpy.dtype = numpy.float32,
) -> None:
    with bfio.BioWriter(path) as writer:
        writer.X = size
        writer.Y = size
        writer.dtype = dtype
        if dtype == numpy.float32:
            writer[:] = rng.random(size=(size, size), dtype=writer.dtype)
        else:
            writer[:] = rng.integers(
                low=0,
                high=numpy.iinfo(writer.dtype).max,
                size=(size, size),
                dtype=writer.dtype,
            )


FixtureReturnType = typing.Tuple[pathlib.Path, str, pathlib.Path, str, bool]


def gen_once(
    num_groups: int, img_size: int, dtype: numpy.dtype = numpy.float32
) -> FixtureReturnType:
    """Generate a set of random images for testing."""
    img_pattern = "img_x{x}_c{c}.ome.tif"
    ff_pattern = "img_x(1-10)_c{c}"

    img_dir = pathlib.Path(tempfile.mkdtemp(suffix="img_dir"))
    ff_dir = pathlib.Path(tempfile.mkdtemp(suffix="ff_dir"))

    rng = numpy.random.default_rng(42)

    for i in range(num_groups):
        ff_path = ff_dir.joinpath(f"{ff_pattern.format(c=i + 1)}_flatfield.ome.tif")
        _make_random_image(ff_path, rng, img_size, dtype)

        df_path = ff_dir.joinpath(f"{ff_pattern.format(c=i + 1)}_darkfield.ome.tif")
        _make_random_image(df_path, rng, img_size, dtype)

        for j in range(10):  # 10 images in each group
            img_path = img_dir.joinpath(img_pattern.format(x=j + 1, c=i + 1))
            _make_random_image(img_path, rng, img_size, dtype)

    image_names = list(sorted(p.name for p in img_dir.iterdir()))
    logger.debug(f"Generated {image_names} images in {img_dir}")

    ff_names = list(sorted(p.name for p in ff_dir.iterdir()))
    logger.debug(f"Generated {ff_names} flatfield images in {ff_dir}")

    img_pattern = "img_x{x:d+}_c{c:d}.ome.tif"
    ff_pattern = "img_x\\(1-10\\)_c{c:d}"
    return img_dir, img_pattern, ff_dir, ff_pattern, True


NUM_GROUPS = [1, 4]
IMG_SIZES = [1024, 4096]
IMG_DTYPE = [numpy.float32, numpy.uint16]
KEEP_ORIG_DTYPE = [True, False]
PARAMS = list(itertools.product(NUM_GROUPS, IMG_SIZES, IMG_DTYPE, KEEP_ORIG_DTYPE))
IDS = [
    f"{num_groups}_{img_size}_{dtype}_{keep_orig}"
    for num_groups, img_size, dtype, keep_orig in PARAMS
]


@pytest.fixture(params=PARAMS, ids=IDS)
def gen_images(
    request: pytest.FixtureRequest,
) -> typing.Generator[FixtureReturnType, None, None]:
    """Generate a set of random images for testing."""
    num_groups: int
    img_size: int
    num_groups, img_size, dtype, keep_orig = request.param
    img_dir, img_pattern, ff_dir, ff_pattern, _ = gen_once(num_groups, img_size, dtype)

    yield img_dir, img_pattern, ff_dir, ff_pattern, keep_orig

    # Cleanup
    shutil.rmtree(img_dir)
    shutil.rmtree(ff_dir)


def test_estimate(gen_images: FixtureReturnType) -> None:
    """Test the `estimate` function."""
    img_dir, img_pattern, ff_dir, ff_pattern, keep_orig = gen_images
    out_dir = pathlib.Path(tempfile.mkdtemp(suffix="out_dir"))

    apply(
        img_dir=img_dir,
        img_pattern=img_pattern,
        ff_dir=ff_dir,
        ff_pattern=f"{ff_pattern}_flatfield.ome.tif",
        df_pattern=f"{ff_pattern}_darkfield.ome.tif",
        out_dir=out_dir,
        keep_orig_dtype=keep_orig,
    )

    img_names = sorted([p.name for p in img_dir.iterdir()])
    out_names = sorted([p.name for p in out_dir.iterdir()])

    for name in img_names:
        assert name in out_names, f"{name} not in {out_names}"

    shutil.rmtree(out_dir)


def test_cli() -> None:
    """Test the CLI."""
    img_dir, img_pattern, ff_dir, ff_pattern, _ = gen_once(2, 2_048)
    out_dir = pathlib.Path(tempfile.mkdtemp(suffix="out_dir"))

    runner = typer.testing.CliRunner()

    result = runner.invoke(
        app,
        [
            "--imgDir",
            str(img_dir),
            "--imgPattern",
            img_pattern,
            "--ffDir",
            str(ff_dir),
            "--ffPattern",
            f"{ff_pattern}_flatfield.ome.tif",
            "--dfPattern",
            f"{ff_pattern}_darkfield.ome.tif",
            "--outDir",
            str(out_dir),
        ],
    )

    assert result.exit_code == 0, result.stdout

    img_paths = {p.name for p in img_dir.iterdir() if p.name.endswith(".ome.tif")}

    out_names = {p.name for p in out_dir.iterdir() if p.name.endswith(".ome.tif")}

    assert img_paths == out_names, f"{(img_paths)} != {out_names}"

    # Cleanup
    shutil.rmtree(img_dir)
    shutil.rmtree(ff_dir)
    shutil.rmtree(out_dir)
