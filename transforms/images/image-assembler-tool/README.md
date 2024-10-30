# Image Assembler (1.5.0-dev0)

This WIPP plugin assembles images into a stitched image using an image stitching
vector. It can assemble 2d and z-stacked images. When assembling z-stacked images,
all images should have the same depth. Support for assembling images with different depth
will be added in the future.

The need for this plugin is due to limitations of the NIST
[WIPP Image Assembling Plugin](https://github.com/usnistgov/WIPP-image-assembling-plugin)
that limits image sizes to less than 2^32 pixels. The NIST plugin works faster
since it is built on optimized C-code. If your image has less than 2^32 pixels,
it is recommended to use NISTs image assembling algorithm.

For more information on WIPP, visit the
[official WIPP page](https://isg.nist.gov/deepzoomweb/software/wipp).

## Outpute Filenames

There are two general options for output file name format:

1. `--timesliceNaming true`: Each image will be named according to the time
index extracted from the stitching vector.
2. `--timesliceNaming false`: The
[filepattern](https://github.com/LabShare/polus-plugins/tree/master/utils/polus-filepattern-util)
utility will attempt to infer an output file name based on all of the input
files (using the method `filepattern.output_name`). *If this fails, it will
default to the first file name in the stitching vector.*

## Building

To build the Docker image for the conversion plugin, run `./build-docker.sh`.

## Install WIPP Plugin

If WIPP is running, navigate to the plugins page and add a new plugin. Paste the
contents of `plugin.json` into the pop-up window and submit.

## Options

This plugin takes two input arguments and one output argument:

| Name                | Description                              | I/O    | Type            |
|---------------------|------------------------------------------|--------|-----------------|
| `--stitchPath`      | Path to stitching vector                 | Input  | stitchingVector |
| `--imgPath`         | Path to input image collection           | Input  | collection      |
| `--timesliceNaming` | Output image names are timeslice numbers | Input  | boolean         |
| `--outDir`          | Path to output image collection          | Output | collection      |
| `--preview`          | Generate preview of outputs             | Output | json file       |
