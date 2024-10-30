"""RT_CETSA Plate Extraction Tool."""
__version__ = "0.2.0-dev0"

import logging
import os
from pathlib import Path

import bfio
import filepattern
import tifffile
from polus.images.segmentation.rt_cetsa_plate_extraction.core import PlateParams
from polus.images.segmentation.rt_cetsa_plate_extraction.core import create_mask
from polus.images.segmentation.rt_cetsa_plate_extraction.core import crop_and_rotate
from polus.images.segmentation.rt_cetsa_plate_extraction.core import get_plate_params

logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger(__file__)
logger.setLevel(os.environ.get("POLUS_LOG", logging.INFO))

POLUS_IMG_EXT = os.environ.get("POLUS_IMG_EXT", ".ome.tiff")


def extract_plates(inp_dir, pattern, out_dir) -> PlateParams:
    """Preprocess RT_cetsa images.

    Using the first plate image, determine plate params.
    Create a plate mask and a plate parameters file.
    Then crop and rotate all RT_cetsa images.
    """
    fp = filepattern.FilePattern(inp_dir, pattern)
    sorted_fp = sorted(fp(), key=lambda f: f[0]["index"])
    inp_files: list[Path] = [f[1][0] for f in sorted_fp]  # type: ignore[assignment]

    if len(inp_files) < 1:
        msg = "no input files captured by the pattern."
        raise ValueError(msg)

    (out_dir / "images").mkdir(parents=False, exist_ok=True)
    (out_dir / "masks").mkdir(parents=False, exist_ok=True)
    (out_dir / "params").mkdir(parents=False, exist_ok=True)

    # extract plate params from first image
    first_image_path = inp_files[0]

    first_image = tifffile.imread(first_image_path)

    params: PlateParams = get_plate_params(first_image)

    logger.info(f"Processing plate of size: {params.size.value}")

    # crop and rotate each image
    num_images = len(inp_files)
    for index, f in enumerate(inp_files):
        logger.info(f"Processing Image {index+1}/{num_images}: {f}")
        image = tifffile.imread(f)
        cropped_and_rotated = crop_and_rotate(image, params)

        if index == 1:
            first_image = cropped_and_rotated

        out_path = out_dir / "images" / (f.stem + POLUS_IMG_EXT)
        with bfio.BioWriter(out_path) as writer:
            writer.dtype = cropped_and_rotated.dtype
            writer.shape = cropped_and_rotated.shape
            writer[:] = cropped_and_rotated

    # save plate parameters for the first processed image
    processed_params = get_plate_params(first_image)
    plate_path = out_dir / "params" / "plate.json"
    with plate_path.open("w") as f:
        f.write(processed_params.model_dump_json())  # type: ignore
        logger.info(f"Plate params saved: {plate_path}")

    # save the corresponding mask for reference
    mask = create_mask(processed_params)
    mask_path = out_dir / "masks" / (first_image_path.stem + POLUS_IMG_EXT)
    with bfio.BioWriter(mask_path) as writer:
        writer.dtype = mask.dtype
        writer.shape = mask.shape
        writer[:] = mask
        logger.info(f"Generate plate mask: {mask_path}")

    return processed_params
