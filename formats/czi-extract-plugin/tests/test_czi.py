"""Cell border segmentation package."""
from pathlib import Path
import czifile
import skimage
import polus.plugins.formats.czi_extract.czi as cz
from tests.conftest import clean_directories



def test_extract_fovs(download_czi: Path, output_directory: Path) -> None:
    """Test extracting fovs from czi image."""
    for im in download_czi.iterdir():
        fname = Path(Path(im).name).stem
        cz.extract_fovs(Path(im), output_directory)
        czi_image = czifile.CziFile(Path(im), detectmosaic=False)
        (_, _, ch, zpos, _, _, _) = czi_image.shape
        num_files = ch * zpos

        out_files = [
            f for f in output_directory.iterdir() if f.name.startswith(f"{fname}")
        ]
        assert len(out_files) == num_files

    out_ext = all([Path(f.name).suffix for f in output_directory.iterdir()])

    assert out_ext == True


def test_get_image_dim(download_czi: Path) -> None:
    """Test getting czi image dimensions."""
    im = list(download_czi.iterdir())[0]
    czi_image = czifile.CziFile(im, detectmosaic=False)
    for s in czi_image.filtered_subblock_directory:
        dimensions = ["X", "Y", "Z", "C", "T"]
        for d in dimensions:
            dim_numb = cz._get_image_dim(s, d)
            assert dim_numb != 0


def test_write_thread(output_directory: Path) -> None:
    """Test writing ome tif image."""
    for i in range(10):
        blobs = skimage.data.binary_blobs(
            length=1024, volume_fraction=0.05, blob_size_fraction=0.05
        )
        syn_img = skimage.measure.label(blobs)
        outname = f"test_image_{i}.ome.tif"
        out_file_path = Path(output_directory, outname)
        chan_name = "c"
        cz.write_thread(out_file_path, syn_img, None, chan_name)

        out_ext = all([Path(f.name).suffix for f in output_directory.iterdir()])
        assert out_ext == True

    clean_directories()
