#!/bin/bash
# Local build script for Bsense
# Usage: ./build.sh

set -e

echo "Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

echo "Building Bsense..."
pyinstaller bsense.spec

echo ""
echo "Build complete! Executable is in: dist/Bsense"
echo ""

# Show file info
if [ -f "dist/Bsense" ]; then
    ls -lh dist/Bsense
elif [ -f "dist/Bsense.exe" ]; then
    ls -lh dist/Bsense.exe
fi
