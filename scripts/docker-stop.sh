#!/usr/bin/env bash
# Stop Snipara Sandbox Docker REPL container
set -euo pipefail

CONTAINER_NAME="snipara-sandbox-repl"

if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo "Stopping container: $CONTAINER_NAME"
    docker stop "$CONTAINER_NAME"
    echo "Container stopped."
else
    echo "Container not running: $CONTAINER_NAME"
fi
