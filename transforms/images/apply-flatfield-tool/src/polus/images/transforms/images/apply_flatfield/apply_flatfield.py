"""Provides the function to apply flatfield."""

import logging
import operator
import pathlib
import typing

import bfio
import numpy
import preadator
import tqdm
from filepattern import FilePattern

from . import utils

logger = logging.getLogger(__name__)
logger.setLevel(utils.POLUS_LOG)


def apply(  # noqa: PLR0913
    *,
    img_dir: pathlib.Path,
    img_pattern: str,
    ff_dir: pathlib.Path,
    ff_pattern: str,
    df_pattern: typing.Optional[str],
    out_dir: pathlib.Path,
    preview: bool = False,
) -> list[pathlib.Path]:
    """Run batch-wise flatfield correction on the image collection.

    Args:
        img_dir: path to the directory containing the images to be processed.
        img_pattern: filename pattern used to select images from img_dir.
        ff_dir: path to the directory containing the flatfield images.
        ff_pattern: filename pattern used to select flatfield components from
        ff_dir.
        df_pattern: filename pattern used to select darkfield components from
        ff_dir.
        out_dir: path to the directory where the corrected images will be
        saved.
        preview: if True, return the paths to the images that would be saved
        without actually performing any other computation.
    """
    img_fp = FilePattern(str(img_dir), img_pattern)
    img_variables = img_fp.get_variables()

    ff_fp = FilePattern(str(ff_dir), ff_pattern)
    ff_variables = ff_fp.get_variables()

    # check that ff_variables are a subset of img_variables
    if set(ff_variables) - set(img_variables):
        msg = (
            f"Flatfield variables are not a subset of image variables: "
            f"{ff_variables} - {img_variables}"
        )
        logger.error(msg)
        raise ValueError(msg)

    if (df_pattern is None) or (not df_pattern):
        df_fp = None
    else:
        df_fp = FilePattern(str(ff_dir), df_pattern)
        df_variables = df_fp.get_variables()
        if set(df_variables) != set(ff_variables):
            msg = (
                f"Flatfield and darkfield variables do not match: "
                f"{ff_variables} != {df_variables}"
            )
            logger.error(msg)
            raise ValueError(msg)

    out_files = []
    for group, files in img_fp(group_by=ff_variables):
        img_paths = [p for _, [p] in files]
        variables = dict(group)

        ff_path: pathlib.Path = ff_fp.get_matching(**variables)[0][1][0]

        df_path = None if df_fp is None else df_fp.get_matching(**variables)[0][1][0]

        if preview:
            out_files.extend(img_paths)
        else:
            _unshade_images(img_paths, out_dir, ff_path, df_path)

    return out_files


def _unshade_images(
    img_paths: list[pathlib.Path],
    out_dir: pathlib.Path,
    ff_path: pathlib.Path,
    df_path: typing.Optional[pathlib.Path],
) -> None:
    """Remove the given flatfield components from all images and save outputs.

    Args:
        img_paths: list of paths to images to be processed
        out_dir: directory to save the corrected images
        ff_path: path to the flatfield image
        df_path: path to the darkfield image
    """
    logger.info(f"Applying flatfield correction to {len(img_paths)} images ...")
    logger.info(f"{ff_path.name = } ...")
    logger.debug(f"Images: {img_paths}")

    with bfio.BioReader(ff_path, max_workers=2) as bf:
        ff_image = bf[:, :, :, 0, 0].squeeze()

    if df_path is not None:
        with bfio.BioReader(df_path, max_workers=2) as df:
            df_image = df[:, :, :, 0, 0].squeeze()
    else:
        df_image = None

    batch_indices = list(range(0, len(img_paths), 16))
    if batch_indices[-1] != len(img_paths):
        batch_indices.append(len(img_paths))

    for i_start, i_end in tqdm.tqdm(
        zip(batch_indices[:-1], batch_indices[1:]),
        total=len(batch_indices) - 1,
    ):
        _unshade_batch(
            img_paths[i_start:i_end],
            out_dir,
            ff_image,
            df_image,
        )


def _unshade_batch(
    batch_paths: list[pathlib.Path],
    out_dir: pathlib.Path,
    ff_image: numpy.ndarray,
    df_image: typing.Optional[numpy.ndarray],
    dtype: numpy.dtype = numpy.float32,
) -> None:
    """Apply flatfield correction to a batch of images.

    Args:
        batch_paths: list of paths to images to be processed
        out_dir: directory to save the corrected images
        ff_image: component to be used for flatfield correction
        df_image: component to be used for flatfield correction
        dtype: data type to use for the corrected images
    """
    # Load images
    with preadator.ProcessManager(
        name="unshade_batch::load",
        num_processes=utils.MAX_WORKERS,
        threads_per_process=2,
    ) as load_executor:
        load_futures = []
        for i, inp_path in enumerate(batch_paths):
            load_futures.append(
                load_executor.submit_process(utils.load_img, inp_path, i),
            )

        load_executor.join_processes()
        images = [f.result() for f in load_futures]

    images = [img for _, img in sorted(images, key=operator.itemgetter(0))]
    img_stack = numpy.stack(images, axis=0).astype(dtype)

    # Apply flatfield correction
    if df_image is not None:
        img_stack -= df_image.astype(dtype)

    img_stack /= ff_image + 1e-8

    # Save outputs
    with preadator.ProcessManager(
        name="unshade_batch::save",
        num_processes=utils.MAX_WORKERS,
        threads_per_process=2,
    ) as save_executor:
        for inp_path, img in zip(batch_paths, img_stack):
            save_executor.submit_process(utils.save_img, inp_path, img, out_dir)
        save_executor.join_processes()
