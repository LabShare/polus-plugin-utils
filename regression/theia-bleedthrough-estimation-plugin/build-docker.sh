#!/bin/bash

version=$(<VERSION)
docker build . -t polusai/theia-bleedthrough-estimation-plugin:"${version}"
