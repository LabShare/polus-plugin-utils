# This script is designed to help package a new version of a plugin

# Get the new version
version=$(<VERSION)

# Bump the version
bump2version --config-file bumpversion.cfg --new-version ${version} --allow-dirty part

# Build the container
./build-docker.sh

# Push to dockerhub
docker push polusai/czi-extract-plugin:${version}
