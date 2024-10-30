# RT_CETSA Plate Extraction Tool (v0.2.0-dev0)

This tool extracts detect wells in a RT-CETSA plate image.
It outputs a cropped and rotated image and the well detection mask.

## Building

To build the Docker image for the conversion plugin, run
`./build-docker.sh`.

## Install WIPP Plugin

If WIPP is running, navigate to the plugins page and add a new plugin. Paste the contents of `plugin.json` into the pop-up window and submit.

## Options

This plugin takes eight input argument and one output argument:

| Name            | Description                                        | I/O    | Type        |
|-----------------|----------------------------------------------------|--------|-------------|
| `--inpDir`      | Input data collection to be processed by this tool | Input  | genericData |
| `--filePattern` | FilePattern to parse input files                   | Input  | string      |
| `--outDir`      | Output dir                                         | Output | genericData |
| `--preview`     | Generate JSON file with outputs                    | Output | JSON        | Optional
