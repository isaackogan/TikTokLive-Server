#!/bin/bash

docker buildx build --push \
--platform linux/amd64,linux/arm64 \
--tag isaackogan/tiktoklive-server:latest \
--tag isaackogan/tiktoklive-server:v0.0.7 .