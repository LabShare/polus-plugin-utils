#!/bin/bash

version=$(<VERSION)
docker push polusai/polus-imagej-threshold-rosin-plugin:${version}