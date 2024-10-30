#!/bin/bash

version=$(<VERSION)
docker build . -t polusai/rt-cetsa-plate-extraction-tool:"${version}"
