#!/bin/bash

version=$(<VERSION)
datapath=$(readlink --canonicalize ../data)

# Inputs
inpDir=/data/path_to_files
filePattern="tubhiswt_z{z:d+}_c{c:d+}_t{t:d+}.ome.tif"
axis="Z"

# Output paths
outDir=/data/path_to_output

# Log level, must be one of ERROR, CRITICAL, WARNING, INFO, DEBUG
LOGLEVEL=INFO

docker run --mount type=bind,source=${datapath},target=/data/ \
            --user $(id -u):$(id -g) \
            --env POLUS_LOG=${LOGLEVEL} \
            polusai/image-dimension-stacking-plugin:${version} \
            --inpDir ${inpDir} \
            --filePattern ${filePattern} \
            --axis ${axis} \
            --outDir ${outDir}
