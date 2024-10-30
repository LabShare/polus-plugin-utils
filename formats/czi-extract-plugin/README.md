# Polus CZI Extraction Plugin (v1.1.2-dev)

This WIPP plugin will import individual fields of view from a CZI file (will
only import one scene or collection of images). Images are exported as tiled
tiffs using bfio. File names indicate their relative X and Y coordinates, as
well as their channel, z-slice, and time-slice.

The need for this plugin is due to the bioformats mechanism of importing CZI
images. If the image in the CZI file is mosaiced (stitched based off image
positions in Zen), then bioformats imports the mosaiced image. However,
preprocessing prior to mosaicing and use of alternative image stitching
algorithms (such as correlation based stitching) can improve the
quality/accuracy of the stitching. Correlation based image stitching can address
small errors in the microscope stage positions, leading to better stitched
images than use of stage positions alone.

The file names exported by this plugin use the following convention:
(imageName)_y000_x000_c000_z000_t000.ome.tif

If any of the zct coordinates are not present, they are ommitted from the
filename. Three characters are always used to indicate a position (for example,
`_y000_`, `_y001_`, etc).

For more information on WIPP, visit the
[official WIPP page](https://isg.nist.gov/deepzoomweb/software/wipp).

For more information on Bioformats, vist the
[official page](https://www.openmicroscopy.org/bio-formats/).

## Building

To build the Docker image for the conversion plugin, run
`./build-docker.sh`.

## Install WIPP Plugin

If WIPP is running, navigate to the plugins page and add a new plugin. Paste
the contents of `plugin.json` into the pop-up window and submit.

## Options

This plugin takes two input arguments and one output argument:

| Name     | Description             | I/O    | Type |
| -------- | ----------------------- | ------ | ---- |
| `--inpDir` | Input image collection  | Input  | genericData |
| `--filePattern` | Pattern to parse image files  | Input  | string |
| `--outDir` | Output image collection | Output | collection |
| `--preview`        | Generate a JSON file with outputs                                  | Output | JSON          |

## Run the plugin

### Run the Docker Container

```bash
docker run -v /path/to/data:/data polusai/czi-extract-plugin:1.1.2-dev \
  --inpDir /data/input \
  --filePattern ".*.czi" \
  --outDir /data/output
```
