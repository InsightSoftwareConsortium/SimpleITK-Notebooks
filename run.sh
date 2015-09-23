#!/bin/sh

docker run \
  --rm \
  -p 8889:8889 \
  -v $PWD:/usr/src \
  insighttoolkit/simpleitk-notebooks
