import itertools
from enum import Enum

import numpy as np
from pydantic import BaseModel
from scipy import ndimage as ndi
from skimage.draw import disk
from skimage.filters import threshold_otsu
from skimage.transform import rotate


class PlateExtractionError(Exception):
    """Raised if the plate could not be processed successfully."""


class PlateSize(Enum):
    """Common Plate Sizes."""

    SIZE_6 = 6
    SIZE_12 = 12
    SIZE_24 = 24
    SIZE_48 = 48
    SIZE_96 = 96
    SIZE_384 = 384
    SIZE_1536 = 1536


"""Plate layouts."""
# Dims in row/cols
PLATE_DIMS = {
    PlateSize.SIZE_6: (2, 3),
    PlateSize.SIZE_12: (3, 4),
    PlateSize.SIZE_24: (4, 6),
    PlateSize.SIZE_48: (6, 8),
    PlateSize.SIZE_96: (8, 12),
    PlateSize.SIZE_384: (16, 24),
    PlateSize.SIZE_1536: (32, 48),
}

"""Half rotation matrix of all degree-wise rotation on [0,180)."""
ROTATION = np.vstack(
    [
        -np.sin(np.arange(0, np.pi, np.pi / 180)),
        np.cos(np.arange(0, np.pi, np.pi / 180)),
    ],
)


class PlateParams(BaseModel):
    rotate: int
    """Counterclockwise rotation of image in degrees."""

    bbox: tuple[int, int, int, int]
    """Bounding box of plate after rotation, [ymin,ymax,xmin,xmax]."""

    size: PlateSize
    """The plate size, also determines layout."""

    radius: int
    """Well radius."""

    roi_radius: int
    """Radius of the region of interest."""

    X: list[int]
    """The the x axis points for wells."""

    Y: list[int]
    """The the y axis points for wells."""


def crop_and_rotate(image: np.ndarray, params: PlateParams):
    """Crop and rotate image according to plate params."""
    return rotate(image, params.rotate, preserve_range=True)[
        params.bbox[0] : params.bbox[1],
        params.bbox[2] : params.bbox[3],
    ].astype(image.dtype)


def create_mask(params: PlateParams):
    """Create a mask for all wells given the plate parameters."""
    width = params.bbox[3] - params.bbox[2]
    heigth = params.bbox[1] - params.bbox[0]
    wells_mask = np.zeros((heigth, width), dtype=np.uint16)

    for mask_label, (y, x) in enumerate(itertools.product(params.Y, params.X), start=1):
        y_crop, x_crop = (y, x)
        rr, cc = disk((y_crop, x_crop), params.radius)
        wells_mask[rr, cc] = mask_label

    return wells_mask


def get_plate_params(image: np.ndarray) -> PlateParams:
    """Detect wells in the image plate.

    Args:
        image: the original RT_cetsa image.

    Returns:
        PlateParams: The description of the plate.
    """
    # Since RT-CETSA are generally high signal to noise,
    # we use a Simple Otsu threshold to segment the well.
    threshold = threshold_otsu(image)

    # Get initial well positions
    cx, cy, radii, _ = detect_wells(image > threshold)

    # Calculate the counterclockwise rotations
    locations = np.vstack([cx, cy]).T
    transform = locations @ ROTATION

    # Find the rotation that aligns the long edge of the plate horizontally
    angle = np.argmin(transform.max(axis=0) - transform.min(axis=0))

    # Shortest rotation to alignment
    if angle > 90:
        angle -= 180

    # Rotate the plate and recalculate well positions
    image_rotated = rotate(image, angle, preserve_range=True)

    # Recalculate well positions
    cx, cy, radii, _ = detect_wells(image_rotated > threshold)

    # Determine the plate layout
    n_wells = len(cx)
    plate_config = None
    for layout in PlateSize:
        error = abs(1 - n_wells / layout.value)
        if error < 0.05:
            plate_config = layout
            break
    if plate_config is None:
        msg = f"Could not determine plate layout, detected {n_wells} wells."
        raise ValueError(msg)

    # Get the mean radius
    # all wells must have the same size.
    radii_mean = int(np.mean(radii))

    # Get the bounding box after rotation
    cx_min, cx_max = np.min(cx) - 2 * radii_mean, np.max(cx) + 2 * radii_mean
    cy_min, cy_max = np.min(cy) - 2 * radii_mean, np.max(cy) + 2 * radii_mean
    bbox = (int(cy_min), int(cy_max), int(cx_min), int(cx_max))

    # Get X and Y indices
    points = []
    for p, mval in zip([cy, cx], [int(cy_min), int(cx_min)]):
        z_pos = list(p)
        z_pos.sort()
        z_index = 0
        z_count = 1
        Z = [z_pos[0]]
        for z in z_pos[1:]:
            if abs(Z[z_index] - z) < radii_mean // 3:
                Z[z_index] = (Z[z_index] * z_count + z) / (z_count + 1)
                z_count += 1
            else:
                Z[z_index] = int(Z[z_index])
                Z.append(z)
                z_index += 1
                z_count = 1
        Z[-1] = int(Z[-1])
        points.append(Z)

    Y = points[0]
    X = points[1]

    # estimated distance from the well center we need to consider
    roi_radius = min(X[1] - X[0], Y[1] - Y[0]) // 2

    return PlateParams(
        rotate=angle,
        size=plate_config,
        radius=int(radii_mean),
        roi_radius=int(roi_radius),
        bbox=bbox,
        X=X,
        Y=Y,
    )


def detect_wells(
    image: np.ndarray,
) -> tuple[list[float], list[float], list[float], int]:
    """Detect well locations and radii estimations.

    Wells are assumed to be disks.
    """
    markers, n_objects = ndi.label(image)

    radii = []
    cx = []
    cy = []
    for s in ndi.find_objects(markers):
        cy.append((s[0].start + s[0].stop) / 2)
        cx.append((s[1].start + s[1].stop) / 2)
        radii.append(np.sqrt((markers[s] > 0).sum() / np.pi))

    return cx, cy, radii, n_objects
