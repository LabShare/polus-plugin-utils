"""ome_zarr_autosegmentation."""

from pathlib import Path

import os

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

import pathlib
from uuid import UUID

import numpy as np
import ome_zarr.scale
import torch
import zarr
from ome_zarr.io import parse_url
from ome_zarr.reader import Reader
from ome_zarr.writer import write_multiscale
from PIL import Image
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
from sam2.build_sam import build_sam2

def get_device():
    """Get the appropriate device for the current system."""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def init_sam2_predictor(checkpoint_path):
    """Initialize SAM2 predictor with given checkpoint"""
    device = get_device()
    model = build_sam2("configs/sam2.1/sam2.1_hiera_s.yaml", checkpoint_path, device=str(device))
    return SAM2AutomaticMaskGenerator(model)


def generate_segmentation_mask(predictor, image):
    """Generate segmentation mask for given PIL image."""
    # Convert PIL image to numpy array
    img_array = np.array(image)

    # Convert grayscale to RGB if necessary
    if len(img_array.shape) == 2 or (
        len(img_array.shape) == 3 and img_array.shape[2] == 1
    ):
        # Stack the single channel three times to create RGB
        img_array = np.stack([img_array] * 3, axis=-1)

    # Ensure array is in correct format (H, W, C)
    if len(img_array.shape) != 3 or img_array.shape[2] != 3:
        raise ValueError(f"Unexpected image shape: {img_array.shape}")

    # Generate masks
    with torch.inference_mode():
        masks = predictor.generate(img_array)

    # Convert list of mask dictionaries to numpy array
    mask_array = np.stack([mask["segmentation"] for mask in masks], axis=0)
    return mask_array


def create_segmentation_overlay(image, masks, colors=None):
    """Create a new image showing segmentation masks with different colors."""
    if len(masks) == 0:
        return Image.new("RGB", image.size, (0, 0, 0))

    # Generate random colors if none provided
    if colors is None:
        colors = []
        for i in range(len(masks)):
            # Distribute hues evenly around color wheel
            hue = i / len(masks)
            h = hue * 6
            c = int(255)
            x = int(255 * (1 - abs(h % 2 - 1)))

            if h < 1:
                rgb = (c, x, 0)
            elif h < 2:
                rgb = (x, c, 0)
            elif h < 3:
                rgb = (0, c, x)
            elif h < 4:
                rgb = (0, x, c)
            elif h < 5:
                rgb = (x, 0, c)
            else:
                rgb = (c, 0, x)

            colors.append(rgb)

    # Create a black background image
    result = Image.new("RGB", image.size, (0, 0, 0))

    # Add each mask with its color
    for i, mask in enumerate(masks):
        mask_img = Image.fromarray((mask * 255).astype(np.uint8)).convert("L")
        overlay = Image.new("RGB", image.size, colors[i])
        result = Image.composite(overlay, result, mask_img)

    return result


def segment_image(predictor, image):
    # Generate masks
    masks = generate_segmentation_mask(predictor, image)

    # Create visualization
    return create_segmentation_overlay(image, masks)


def create_zarr_from_segmentations(segmentations, original_dataset_path, output_dataset_path):
    """Create an OME-ZARR dataset from segmentation PNGs matching original structure."""
    # Get original structure
    location = parse_url(original_dataset_path)
    reader = Reader(location)
    nodes = list(reader())
    image_node = nodes[0]
    image_data = image_node.data[0]
    ndim = len(image_data.shape)

    # Get original metadata
    axes = image_node.metadata["axes"]
    original_chunks = image_data.chunks[0]  # First resolution level

    # Create output directory
    output_path = pathlib.Path(output_dataset_path)
    if output_path.exists():
        import shutil

        shutil.rmtree(output_path)
    output_path.mkdir(parents=True)

    # Create store with nested directory settings
    store = zarr.DirectoryStore(
        str(output_path), dimension_separator="/"
    )  # Use '/' for nested directories
    root = zarr.group(store)

    # Get dimensions from first mask
    first_mask = np.array(segmentations[0])
    if len(first_mask.shape) == 3:
        first_mask = first_mask[..., 0]

    # Create array matching original dimensions
    if ndim == 5:  # (T, C, Z, Y, X)
        masks = np.zeros(
            (1, 1, len(segmentations), first_mask.shape[0], first_mask.shape[1]),
            dtype=np.uint8,
        )
    else:  # (C, Z, Y, X)
        masks = np.zeros(
            (1, len(segmentations), first_mask.shape[0], first_mask.shape[1]),
            dtype=np.uint8,
        )

    # Load all masks
    print(f"Loading {len(segmentations)} segmentation masks...")
    for i, segmentation in enumerate(segmentations):
        mask = np.array(segmentation)
        if len(mask.shape) == 3:
            mask = mask[..., 0]
        if ndim == 5:
            masks[0, 0, i] = mask
        else:
            masks[0, i] = mask

    # Create pyramid using nearest neighbor for labels
    scaler = ome_zarr.scale.Scaler()
    pyramid = scaler.nearest(masks)

    # Write with nested directory structure
    write_multiscale(
        pyramid=pyramid,
        group=root,
        axes=axes,
        storage_options={
            "chunks": original_chunks,
            "dimension_separator": "/",  # Ensure nested directory structure
        },
    )

    return output_path


def autosegment_dataset(input_dataset_path: Path | str, output_dataset_path: Path | str):
    location = parse_url(input_dataset_path)
    reader = Reader(location)
    nodes = list(reader())

    # First node has highest resolution
    image_node = nodes[0]
    image_data = image_node.data[0]

    print(f"Dataset shape: {image_data.shape}")
    print(f"Data chunks: {image_data.chunks}")

    ndim = len(image_data.shape)

    if ndim == 5:  # Typically (T, C, Z, Y, X)
        print("5D dataset detected (T, C, Z, Y, X)")
        volume = image_data[0, 0]
    elif ndim == 4:  # Typically (C, Z, Y, X)
        print("4D dataset detected (C, Z, Y, X)")
        volume = image_data[0]
    else:
        raise ValueError(f"Unexpected number of dimensions: {ndim}")

    num_slices = volume.shape[0]
    print(f"Processing {num_slices} Z-slices from channel")

    segmentations = []
    sam2_predictor = init_sam2_predictor(
        "../models/sam2.1_hiera_small.pt",
    )
    for z in range(num_slices):
        slice_data = volume[z].compute()

        # Normalize to 0-255 range
        if slice_data.dtype != np.uint8:
            slice_min = slice_data.min()
            slice_max = slice_data.max()
            if slice_max > slice_min:
                slice_data = (
                    (slice_data - slice_min) * 255 / (slice_max - slice_min)
                ).astype(np.uint8)
            else:
                slice_data = np.zeros_like(slice_data, dtype=np.uint8)

        img = Image.fromarray(slice_data)
        segmentations.append(segment_image(sam2_predictor, img))

        if z % 10 == 0:
            print(f"Processed slice {z}/{num_slices}")
           
            
    create_zarr_from_segmentations(segmentations,
        input_dataset_path, output_dataset_path
    )


def autosegmentation(inp_dir: Path, out_dir: Path):
    """ome_zarr_autosegmentation.

    Args:
        inp_dir: input directory to process
        filepattern: filepattern to filter inputs
        out_dir: output directory
    Returns:
        None
    """
    autosegment_dataset(inp_dir, out_dir)