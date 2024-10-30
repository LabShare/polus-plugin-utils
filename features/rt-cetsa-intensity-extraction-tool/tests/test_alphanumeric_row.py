"""Test plate coordinates."""

from polus.images.features.rt_cetsa_intensity_extraction import PLATE_DIMS
from polus.images.features.rt_cetsa_intensity_extraction import PlateSize
from polus.images.features.rt_cetsa_intensity_extraction import alphanumeric_row


def test_alphanumeric_row_48():
    """Test plate coordinates for plate size 48."""
    rows, cols = PLATE_DIMS[PlateSize(48)]
    assert alphanumeric_row(0, 0, (rows, cols)) == "A1"
    assert alphanumeric_row(5, 7, (rows, cols)) == "F8"


def test_alphanumeric_row_96():
    """Test plate coordinates for plate size 96."""
    rows, cols = PLATE_DIMS[PlateSize(96)]
    assert alphanumeric_row(0, 0, (rows, cols)) == "A01"
    assert alphanumeric_row(7, 11, (rows, cols)) == "H12"


def test_alphanumeric_row_384():
    """Test plate coordinates for plate size 384."""
    rows, cols = PLATE_DIMS[PlateSize(384)]
    assert alphanumeric_row(0, 0, (rows, cols)) == "A01"
    assert alphanumeric_row(15, 23, (rows, cols)) == "P24"


def test_alphanumeric_row_1536():
    """Test plate coordinates for plate size 1536."""
    rows, cols = PLATE_DIMS[PlateSize(1536)]
    assert alphanumeric_row(0, 0, (rows, cols)) == "A01"
    assert alphanumeric_row(31, 47, (rows, cols)) == "AF48"
