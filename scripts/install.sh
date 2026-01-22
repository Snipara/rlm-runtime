#!/usr/bin/env bash
# One-line installer for RLM Runtime
set -euo pipefail

echo "Installing RLM Runtime..."

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

# Install based on arguments
EXTRAS=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            EXTRAS="${EXTRAS},docker"
            shift
            ;;
        --snipara)
            EXTRAS="${EXTRAS},snipara"
            shift
            ;;
        --all)
            EXTRAS="all"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--docker] [--snipara] [--all]"
            exit 1
            ;;
    esac
done

# Install package
if [ -n "$EXTRAS" ]; then
    EXTRAS="${EXTRAS#,}"  # Remove leading comma
    pip install "rlm-runtime[$EXTRAS]"
else
    pip install rlm-runtime
fi

echo ""
echo "Installation complete!"
echo ""
echo "Quick start:"
echo "  rlm init           # Initialize config"
echo "  rlm run 'prompt'   # Run a completion"
echo "  rlm doctor         # Check setup"
echo ""
echo "For Docker isolation (recommended):"
echo "  pip install 'rlm-runtime[docker]'"
echo "  rlm run --env docker 'prompt'"
echo ""
echo "For Snipara context optimization:"
echo "  pip install 'rlm-runtime[snipara]'"
echo "  # Set SNIPARA_API_KEY and SNIPARA_PROJECT_SLUG"
