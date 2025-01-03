"""Tests for ome_zarr_autosegmentation."""

import pytest
from polus.plugins.images.segmentation.ome_zarr_autosegmentation.ome_zarr_autosegmentation import (
    ome_zarr_autosegmentation,
)
from .conftest import FixtureReturnType


def test_ome_zarr_autosegmentation(generate_test_data : FixtureReturnType):
    """Test ome_zarr_autosegmentation."""
    inp_dir, out_dir, ground_truth_dir, img_path, ground_truth_path = generate_test_data
    filepattern = ".*"
    assert ome_zarr_autosegmentation(inp_dir, filepattern, out_dir) == None


@pytest.mark.skipif("not config.getoption('slow')")
def test_ome_zarr_autosegmentation(generate_large_test_data : FixtureReturnType):
    """Test ome_zarr_autosegmentation."""
    inp_dir, out_dir, ground_truth_dir, img_path, ground_truth_path = generate_large_test_data
    filepattern = ".*"
    assert ome_zarr_autosegmentation(inp_dir, filepattern, out_dir) == None