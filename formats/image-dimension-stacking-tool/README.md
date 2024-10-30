# Image dimension stacking(0.2.0-dev0)

This plugin leverages the [filepattern](https://filepattern2.readthedocs.io/en/latest/Home.html) library and employs the filepattern `groupBy` functionality to enable the matching of image filenames, facilitating their stacking into multi-dimensional images.

The filepattern must include the variables `c`, `t`, and `z`. If all these variables are present in the pattern, the plugin will group images according to the order `z, c, t`. If only one variable is present in the file pattern, the plugin will group images according to that variable.

Currently, the plugin supports the following dimensions and user can choose the relevant variable for the `groupBy` input argument.

1. `tubhiswt_z{z:d+}_c{c:d+}_t{t:d+}.ome.tif`: Images are grouped based on `z` variable
2. `tubhiswt_.*_.*_t{t:d+}.ome.tif`: Images are grouped based on `t` variable
3. `00001_01_{c:d+}.ome.tif`: Images are grouped based on `c` variable

## Note:

Filename patterns may consist of any other filepattern variables, combined with other valid regular expression arguments, excluding the `groupBy` variable.

For more information on WIPP, visit the
[official WIPP page](https://isg.nist.gov/deepzoomweb/software/wipp).

## Building

To build the Docker image for the conversion plugin, run
`./build-docker.sh`.

## Install WIPP Plugin

If WIPP is running, navigate to the plugins page and add a new plugin. Paste the
contents of `plugin.json` into the pop-up window and submit.

## Options

This plugin takes three input argument and one output argument:

| Name            | Description                          | I/O    | Type       |
| --------------- | ------------------------------------ | ------ | ---------- |
| `--inpDir`      | Input image collection               | Input  | Collection |
| `--filePattern` | Pattern to parse image files         | Input  | String     |
| `--axis`        | Dimension to stack images            | Input  | String     |
| `--outDir`      | Output image collection              | Output | Collection |
| `--preview`     | Generate a JSON file to view outputs | Output | Boolean    |

## Run the Docker Container

```bash
docker run -v /path/to/data:/data polusai/image-dimension-stacking-plugin:0.2.0-dev0-dev \
  --inpDir "path/to/data" \
  --filePattern "tubhiswt_C1-z{z:d+}.ome.tif" \
   --axis "z" \
  --outDir "Path/To/Output/Dir"
```
