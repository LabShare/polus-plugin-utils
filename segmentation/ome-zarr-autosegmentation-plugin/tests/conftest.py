"""Test fixtures.

Set up all data used in tests.
"""
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pytest
import itertools

from bfio import BioWriter, BioReader

def pytest_addoption(parser: pytest.Parser) -> None:
    """Add options to pytest."""
    parser.addoption(
        "--downloads",
        action="store_true",
        dest="downloads",
        default=False,
        help="run tests that download large data files",
    )
    parser.addoption(
        "--slow",
        action="store_true",
        dest="slow",
        default=False,
        help="run slow tests",
    )




IMAGE_SIZES = [(1024 * (2**i) ,1024 * (2**i)) for i in range(1, 2)]
LARGE_IMAGE_SIZES = [(1024 * (2**i) ,1024 * (2**i)) for i in range(4, 5)]
PIXEL_TYPES = [np.uint8, float]
PARAMS = [
    (image_size, pixel_type)
    for image_size, pixel_type in itertools.product(
        IMAGE_SIZES, PIXEL_TYPES
    )
]
LARGE_DATASET_PARAMS = [
    (image_size, pixel_type)
    for image_size, pixel_type in itertools.product(
        LARGE_IMAGE_SIZES, PIXEL_TYPES
    )
]


FixtureReturnType = tuple[
    Path,  # input dir
    Path,  # output dir
    Path,  # ground truth path
    Path,  # input image path
    Path,  # ground truth path
]


@pytest.fixture(params=PARAMS)
def generate_test_data(request: pytest.FixtureRequest) -> FixtureReturnType:
    """Generate staging temporary directories with test data and ground truth."""

    # collect test params
    image_size, pixel_type = request.param
    test_data =  _generate_test_data(image_size, pixel_type)
    print(test_data)
    yield from test_data


@pytest.fixture(params=LARGE_DATASET_PARAMS)
def generate_large_test_data(request: pytest.FixtureRequest) -> FixtureReturnType:
    """Generate staging temporary directories with test data and ground truth."""

    # collect test params
    image_size, pixel_type = request.param
    test_data =_generate_test_data(image_size, pixel_type)

    print(test_data)

    yield from test_data


def _generate_test_data(image_size : tuple[int,int], pixel_type: int) -> FixtureReturnType:
    """Generate staging temporary directories with test data and ground truth."""

    image_x, image_y = image_size

    # staging area
    data_dir = Path(tempfile.mkdtemp(suffix="_data_dir"))
    inp_dir = data_dir.joinpath("inp_dir")
    inp_dir.mkdir(exist_ok=True)
    out_dir = data_dir.joinpath("out_dir")
    out_dir.mkdir(exist_ok=True)
    ground_truth_dir = data_dir.joinpath("ground_truth_dir")
    ground_truth_dir.mkdir(exist_ok=True)

    # generate image and ground_truth
    img_path = inp_dir.joinpath("img.ome.tif")
    image = gen_2D_image(img_path, image_x, image_y, pixel_type)
    ground_truth_path = ground_truth_dir.joinpath("ground_truth.ome.tif")
    gen_ground_truth(img_path, ground_truth_path)

    yield inp_dir, out_dir, ground_truth_dir, img_path, ground_truth_path

    shutil.rmtree(data_dir)

def gen_2D_image(
    img_path,
    image_x,
    image_y,
    pixel_type
) :
    """Generate a random 2D square image."""

    if np.issubdtype(pixel_type, np.floating) :
        rng = np.random.default_rng()
        image = rng.uniform(0.0, 1.0,
                            size=(image_y, image_x)
                            ).astype(pixel_type)
    else:
        image = np.random.randint(0, 255, size=(image_y, image_x))

    with BioWriter(img_path) as writer:
        (y, x) = image.shape
        writer.Y = y
        writer.X = x
        writer.Z = 1
        writer.C = 1
        writer.T = 1
        writer.dtype = image.dtype
        writer[:] = image[:]

    return image


def gen_ground_truth(img_path : Path, ground_truth_path : Path):
    """generate some ground truth from the image data.
    Here we generate a simple binary mask.
    """

    with BioReader(img_path) as reader:
        with BioWriter(ground_truth_path, metadata=reader.metadata) as writer:
            ground_truth = np.asarray(reader[:] != 0)
            writer[:] = ground_truth

    return ground_truth