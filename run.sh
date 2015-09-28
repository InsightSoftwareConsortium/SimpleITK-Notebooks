#!/bin/sh

docker run \
  --rm \
  -p 8888:8888 \
  -v $PWD:/usr/src \
  insighttoolkit/simpleitk-notebooks
