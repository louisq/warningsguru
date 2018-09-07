#!/usr/bin/env bash

docker build -t warningsguru_analyser .
docker run -it --rm --name warningsguru_analyser-app warningsguru_analyser