#!/bin/bash

version=$(<VERSION)
docker build . -t polusai/ome-zarr-autosegmentation-plugin:${version}
