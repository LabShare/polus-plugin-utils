# ome_zarr_autosegmentation (0.1.0)

description goes here

## Building

To build the Docker image for the conversion plugin, run `./build-docker.sh`.
Download the model you want to use for SAM from `https://github.com/facebookresearch/sam2?tab=readme-ov-file#download-checkpoints`

## Install WIPP Plugin

If WIPP is running, navigate to the plugins page and add a new plugin. Paste the
contents of `plugin.json` into the pop-up window and submit.

## Options

This plugin takes 1 input arguments and 1 output argument:

| Name          | Description             | I/O    | Type   | Default
|---------------|-------------------------|--------|--------|
| inpDir        | Input dataset to be processed by this plugin | Input | collection
| preview   | Generate an output preview | Input | boolean | False
| outDir        | Output collection | Output | collection
