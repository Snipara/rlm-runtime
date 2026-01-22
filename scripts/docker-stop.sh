#!/usr/bin/env bash
# Stop RLM Docker REPL container
set -euo pipefail

CONTAINER_NAME="rlm-repl"

if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo "Stopping container: $CONTAINER_NAME"
    docker stop "$CONTAINER_NAME"
    echo "Container stopped."
else
    echo "Container not running: $CONTAINER_NAME"
fi
