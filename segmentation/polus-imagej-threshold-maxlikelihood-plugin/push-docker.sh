#!/bin/bash

version=$(<VERSION)
docker push polusai/imagej-threshold-maxlikelihood-plugin:${version}