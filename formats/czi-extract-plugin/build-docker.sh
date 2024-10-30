#!/bin/bash

version=$(<VERSION)
docker build . -t polusai/czi-extract-plugin:${version}
