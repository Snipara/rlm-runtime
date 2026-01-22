#!/usr/bin/env bash
# Start RLM Docker REPL container
set -euo pipefail

# Configuration
IMAGE="${RLM_DOCKER_IMAGE:-rlm-runtime:latest}"
CONTAINER_NAME="rlm-repl"
WORKDIR="${1:-$PWD}"
CPUS="${RLM_DOCKER_CPUS:-1.0}"
MEMORY="${RLM_DOCKER_MEMORY:-512m}"

# Check Docker is available
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

# Check Docker daemon is running
if ! docker info &> /dev/null; then
    echo "Error: Docker daemon is not running"
    exit 1
fi

# Build image if it doesn't exist
if ! docker image inspect "$IMAGE" &> /dev/null; then
    echo "Building RLM Docker image..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    docker build -t "$IMAGE" -f "$SCRIPT_DIR/../docker/Dockerfile" "$SCRIPT_DIR/.."
fi

# Stop existing container if running
if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo "Stopping existing container..."
    docker stop "$CONTAINER_NAME" > /dev/null
fi

# Remove existing container if exists
if docker ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
    docker rm "$CONTAINER_NAME" > /dev/null
fi

echo "Starting RLM REPL container..."
echo "  Image: $IMAGE"
echo "  Workdir: $WORKDIR"
echo "  CPUs: $CPUS"
echo "  Memory: $MEMORY"
echo "  Network: disabled"
echo ""

# Run container
docker run -it \
    --name "$CONTAINER_NAME" \
    --network none \
    --cpus="$CPUS" \
    --memory="$MEMORY" \
    -v "${WORKDIR}:/workspace:ro" \
    -w /workspace \
    "$IMAGE" \
    python

echo "Container stopped."
