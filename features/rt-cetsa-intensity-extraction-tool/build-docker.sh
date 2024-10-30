#!/bin/bash

version=$(<VERSION)
docker build . -t polusai/rt-cetsa-intensity-extraction-tool:"${version}"
