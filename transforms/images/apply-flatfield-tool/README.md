# Apply Flatfield Plugin (v2.0.1)

This WIPP plugin applies a flatfield operation on every image in a collection.
The algorithm used to apply the flatfield is as follows:

![Corrected = \frac{Original - Darkfield}{Brightfield} - Photobleach + Offset](https://render.githubusercontent.com/render/math?math=Corrected%20%3D%20%5Cfrac%7BOriginal%20-%20Darkfield%7D%7BBrightfield%7D%20-%20Photobleach%20%2B%20Offset)

A brief description of the variables:
1. ![Corrected](https://render.githubusercontent.com/render/math?math=Corrected) is the flatfield corrected image.
2. ![Darkfield](https://render.githubusercontent.com/render/math?math=Darkfield) is the darkfield image (sometimes referred to as offset, dark current, or dark  noise). This is an image collected by the camera when the shutter is closed.
3. ![Brightfield](https://render.githubusercontent.com/render/math?math=Brightfield) is the normalized brightfield image. This is an image collected when the shutter  is open and illumination is on. The image should contain single precision  floating point values, where ![mean(Brightfield)=1](https://render.githubusercontent.com/render/math?math=mean(Brightfield)%3D1).
4. ![Photobleach](https://render.githubusercontent.com/render/math?math=Photobleach) is a scalar indicating how much the image has been photobleached. This is a per-image scalar offset.
5. ![Offset](https://render.githubusercontent.com/render/math?math=Offset) is a  scalar applied to all images in the collection. If ![Photobleach](https://render.githubusercontent.com/render/math?math=Photobleach) is specified, then this plugin uses ![Offset=mean(Photobleach)](https://render.githubusercontent.com/render/math?math=Offset%3Dmean(Photobleach)).

For more information on flatfielding, see the paper by [Young](https://currentprotocols.onlinelibrary.wiley.com/doi/full/10.1002/0471142956.cy0211s14).
This plugin specifically uses the formulation from [Peng et al](https://www.nature.com/articles/ncomms14836).

For more information on WIPP, visit the
[official WIPP page](https://isg.nist.gov/deepzoomweb/software/wipp).

## TODO

### Additional Flatfield Formulations

Implement additional formulations of flatfield correction. Specifically, the formula specified by Young:

![Corrected = \frac{Original - Darkfield}{Brightfield - Darkfield} ](https://render.githubusercontent.com/render/math?math=Corrected%20%3D%20%5Cfrac%7BOriginal%20-%20Darkfield%7D%7BBrightfield%20-%20Darkfield%7D%20)

Additional formulations may also include reference image free algorithms for flatfield correction, such as the [rolling ball algorithm](https://www.computer.org/csdl/magazine/co/1983/01/01654163/13rRUwwJWBB).

### Photobleach Correction

Since the `basicpy` package and the `basic-flatfield-estimation` tool do not yet support photobleach estimation, this plugin does not yet support photobleach correction.
Once they add support for photobleach estimation, this plugin should be updated to support it.

## Building

To build the Docker image for the conversion plugin, run `./build-docker.sh`.

## Install WIPP Plugin

If WIPP is running, navigate to the plugins page and add a new plugin.
Paste the contents of `plugin.json` into the pop-up window and submit.

## Options

Command line options:

| Name             | Description                                                           | I/O    | Type       |
|------------------|-----------------------------------------------------------------------|--------|------------|
| `--imgDir`       | Input image collection to be processed by this plugin                 | Input  | collection |
| `--imgPattern`   | Filename pattern used to separate data and match with flatfield files | Input  | string     |
| `--ffDir`        | Image collection containing flatfield and/or darkfield images         | Input  | collection |
| `--ffPattern`    | Filename pattern used to match flatfield files to image files         | Input  | string     |
| `--dfPattern`    | Filename pattern used to match darkfield files to image files         | Input  | string     |
| `--outDir`       | Output collection                                                     | Output | collection |
| `--preview`      | Preview the output images' names without actually running computation | Input  | boolean    |
| `--keepOrigDtype`| Keep the original image data type if true                             | Input  | boolean    |