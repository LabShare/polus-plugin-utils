# Image Calculator (v0.3.0-dev0)

This plugin performs pixel-wise operations between two image collections.
For example, images in one image collection can be subtracted from images in another collection.

For more information on WIPP, visit the [official WIPP page](https://isg.nist.gov/deepzoomweb/software/wipp).

## Operations

The following operations are available:

1. `add`: Add images
2. `subtract`: Subtract images in the second collection from images in the first collection.
3. `multiply`: Multiply images
4. `divide`: Divide images in the first collection by images in the second collection.
5. `and`: Perform a bitwise AND operation between images.
6. `or`: Perform a bitwise OR operation between images.
7. `xor`: Perform a bitwise XOR operation between images.
8. `min`: Take the minimum value between images.
9. `max`: Take the maximum value between images.
10. `absdiff`: Take the absolute difference between images.

Note:

- All operations are performed pixel-wise between one image in the first collection and a matching image in the second collection.
- All operations are performed on the first channel of the images.
- All operations are implemented using numpy.
- The three bitwise operations only with on images with integer data types.

## TODO

1. Check the size and type of both images when applying the operation. Currently, the plugin assumes the images are the same size and data type.
2. Handle overflow of the data type.

## Building

To build the Docker image for the conversion plugin, run `./build-docker.sh`.

## Install WIPP Plugin

If WIPP is running, navigate to the plugins page and add a new plugin. Paste the
contents of `plugin.json` into the pop-up window and submit.

## Options

This plugin takes 5 input arguments and
1 output argument:

| Name                 | Description                            | I/O    | Type       | Default |
| -------------------- | -------------------------------------- | ------ | ---------- | ------- |
| `--primaryDir`       | The first set of images                | Input  | collection | N/A     |
| `--primaryPattern`   | Filename pattern used to separate data | Input  | string     | ".*     |
| `--operator`         | The operation to perform               | Input  | enum       | N/A     |
| `--secondaryDir`     | The second set of images               | Input  | collection | N/A     |
| `--secondaryPattern` | Filename pattern used to separate data | Input  | string     | ".*"    |
| `--outDir`           | Output collection                      | Output | collection | N/A     |
