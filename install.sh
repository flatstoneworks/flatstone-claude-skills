#!/bin/bash
#
# Flatstone Claude Skills Installer
#
# Usage:
#   ./install.sh              # Interactive install
#   ./install.sh --workspace ~/projects --yes  # Quick install
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "  Flatstone Claude Skills Installer"
echo "  =================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "  Error: Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  Python version: $PYTHON_VERSION"

# Check minimum version (3.8)
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]); then
    echo "  Error: Python 3.8+ is required (found $PYTHON_VERSION)"
    exit 1
fi

echo ""

# Run the Python setup script with all arguments passed through
python3 "$SCRIPT_DIR/scripts/setup.py" "$@"
