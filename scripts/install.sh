#!/usr/bin/env bash
# One-line installer for Snipara Sandbox
set -euo pipefail

echo "Installing Snipara Sandbox..."

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
    pip install "snipara-sandbox[$EXTRAS]"
else
    pip install snipara-sandbox
fi

echo ""
echo "Installation complete!"
echo ""
echo "Quick start:"
echo "  snipara-sandbox init           # Initialize config"
echo "  snipara-sandbox run 'prompt'   # Run a completion"
echo "  snipara-sandbox doctor         # Check setup"
echo ""
echo "For Docker isolation (recommended):"
echo "  pip install 'snipara-sandbox[docker]'"
echo "  snipara-sandbox run --env docker 'prompt'"
echo ""
echo "For Snipara context optimization:"
echo "  pip install 'snipara-sandbox[snipara]'"
echo "  # Set SNIPARA_API_KEY and SNIPARA_PROJECT_SLUG"
