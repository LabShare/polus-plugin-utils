#!/bin/bash

version=$(<VERSION)
datapath=$(readlink --canonicalize ../../../data)

# Inputs
opName=RichardsonLucyC
#opName=PadAndRichardsonLucy
out_input=/data/input
in1=/data/input
in2=/data/input
maxIterations=5

# Output paths
out=/data/output

docker run --mount type=bind,source=${datapath},target=/data/ \
            polusai/imagej-deconvolve-richardsonlucy-plugin:${version} \
            --opName ${opName} \
            --inpDir ${in1} \
            --psf ${in2} \
            --maxIterations ${maxIterations} \
            --out ${out}
            