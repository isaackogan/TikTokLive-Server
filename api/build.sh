#!/bin/bash

docker buildx build --push \
--platform linux/amd64,linux/arm64 \
--tag isaackogan/fx-connect-serve

r:latest \
--tag isaackogan/fx-connect-server:v0.0.5 .