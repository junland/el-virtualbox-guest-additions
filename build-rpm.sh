#!/bin/bash
set -e

# RPM Build Entrypoint Script
# This script consolidates all RPM build functionality into a single entry point

# Verify that we are in a container environment
if [ ! -f /.containerenv ]; then
    echo "Error: This script is intended to be run inside a container"
    exit 1
fi

if [ $# -eq 0 ]; then
    echo "Error: No arguments provided."
    echo "Usage: $0 <spec-file>"
    exit 1
elif [ $# -gt 1 ]; then
    echo "Error: Too many arguments."
    echo "Usage: $0 <spec-file>"
    exit 1
fi

# If we reach here, exactly one argument was passed
SPEC_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_ROOT="/home/builder/rpmbuild"


echo "=== Starting RPM build process ==="
echo "SPEC_FILE: $SPEC_FILE"
echo "BUILD_ROOT: $BUILD_ROOT"

# Ensure we're running as builder user
if [ "$(whoami)" != "builder" ]; then
    echo "Error: This script must be run as the 'builder' user"
    exit 1
fi

# Create rpmbuild directory structure
echo "Creating RPM build directory structure..."
mkdir -vp "$BUILD_ROOT"/{SOURCES,SPECS,BUILD,RPMS,SRPMS}

# Copy SOURCES and SPECS if they exist in the script directory
if [ -d "$SCRIPT_DIR/SOURCES" ]; then
    echo "Copying SOURCES..."
    cp -rv "$SCRIPT_DIR/SOURCES"/* "$BUILD_ROOT/SOURCES/"
fi

if [ -d "$SCRIPT_DIR/SPECS" ]; then
    echo "Copying SPECS..."
    cp -rv "$SCRIPT_DIR/SPECS"/* "$BUILD_ROOT/SPECS/"
fi

# Check if spec file exists
if [ ! -f "$BUILD_ROOT/SPECS/$SPEC_FILE" ]; then
    echo "Error: Spec file $BUILD_ROOT/SPECS/$SPEC_FILE not found"
    exit 1
fi

# Get sources using spectool
echo "Downloading sources with spectool..."
spectool -g -C "$BUILD_ROOT/SOURCES/" "$BUILD_ROOT/SPECS/$SPEC_FILE" || {
    echo "Warning: spectool failed or no remote sources to download"
}

# Build SRPM
echo "Building SRPM..."
rpmbuild -bs "$BUILD_ROOT/SPECS/$SPEC_FILE"

# Build binary RPMs
echo "Building binary RPMs..."
rpmbuild -bb "$BUILD_ROOT/SPECS/$SPEC_FILE"

echo "=== RPM build completed successfully ==="
echo "Built packages:"
find "$BUILD_ROOT/RPMS" "$BUILD_ROOT/SRPMS" -name "*.rpm" -type f -exec ls -lhG {} \; 2>/dev/null || echo "No RPM files found"
