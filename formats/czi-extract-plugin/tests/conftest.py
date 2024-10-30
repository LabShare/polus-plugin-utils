"""Test fixtures.

Set up all data used in tests.
"""
import shutil
import tempfile
from pathlib import Path
from typing import Union

import pytest
import requests

def clean_directories() -> None:
    """Remove all temporary directories."""
    for d in Path(".").cwd().iterdir():
        if d.is_dir() and d.name.startswith("tmp"):
            shutil.rmtree(d)


@pytest.fixture()
def output_directory() -> Union[str, Path]:
    """Create output directory."""
    return Path(tempfile.mkdtemp())


@pytest.fixture()
def download_czi() -> Union[str, Path]:
    """Download czi images."""
    inp_path = Path.cwd().joinpath("tmp_czi")
    if not inp_path.exists():
        Path(inp_path).mkdir(parents=True)

        url_list = [
            "https://downloads.openmicroscopy.org/images/Zeiss-CZI/idr0011/Plate1-Blue-A_TS-Stinger/Plate1-Blue-A-08-Scene-3-P2-B2-03.czi",
            "https://downloads.openmicroscopy.org/images/Zeiss-CZI/idr0011/Plate1-Blue-A_TS-Stinger/Plate1-Blue-A-02-Scene-1-P2-E1-01.czi",
        ]
        for url in url_list:
            file = Path(url).name
            req = requests.get(url, timeout=10)
            with Path.open(inp_path.joinpath(file), "wb") as fw:
                fw.write(req.content)

    return inp_path