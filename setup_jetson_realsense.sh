#!/bin/bash
# =============================================================================
# Intel RealSense SDK Setup for Jetson Orin AGX (JetPack 5.x)
# =============================================================================
#
# This script installs:
#   1. librealsense2 SDK (built from source for ARM64)
#   2. pyrealsense2 Python bindings
#   3. Open3D for ARM64
#
# Tested on: Jetson Orin AGX with JetPack 5.1.2 (L4T R35.4.1)
#
# Usage:
#   chmod +x setup_jetson_realsense.sh
#   ./setup_jetson_realsense.sh
#
# =============================================================================

set -e  # Exit on error

echo "=============================================="
echo "Intel RealSense Setup for Jetson Orin AGX"
echo "=============================================="
echo ""

# Check if running on Jetson
if [ ! -f /etc/nv_tegra_release ]; then
    echo "[ERROR] This script is designed for NVIDIA Jetson devices."
    exit 1
fi

echo "[INFO] Detected Jetson platform:"
cat /etc/nv_tegra_release
echo ""

# =============================================================================
# Step 1: Install system dependencies
# =============================================================================
echo "[STEP 1/5] Installing system dependencies..."

sudo apt-get update
sudo apt-get install -y \
    git \
    cmake \
    build-essential \
    libssl-dev \
    libusb-1.0-0-dev \
    libudev-dev \
    pkg-config \
    libgtk-3-dev \
    libglfw3-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    python3-dev \
    python3-pip \
    python3-numpy \
    at

echo "[OK] System dependencies installed"

# =============================================================================
# Step 2: Clone and build librealsense
# =============================================================================
echo ""
echo "[STEP 2/5] Building librealsense from source..."

# Use SSD if available to avoid disk space issues
if [ -d "/mnt/ssd" ] && [ -w "/mnt/ssd" ]; then
    LIBREALSENSE_DIR="/mnt/ssd/librealsense"
    echo "[INFO] Using SSD for build: $LIBREALSENSE_DIR"
else
    LIBREALSENSE_DIR="$HOME/librealsense"
    echo "[INFO] Using home directory for build: $LIBREALSENSE_DIR"
fi

if [ -d "$LIBREALSENSE_DIR" ]; then
    echo "[INFO] librealsense directory exists, pulling latest..."
    cd "$LIBREALSENSE_DIR"
    git fetch --all
    git checkout master
    git pull
else
    echo "[INFO] Cloning librealsense repository..."
    cd "$(dirname "$LIBREALSENSE_DIR")"
    git clone --depth 1 https://github.com/IntelRealSense/librealsense.git "$(basename "$LIBREALSENSE_DIR")"
    cd "$LIBREALSENSE_DIR"
fi

# Get latest stable release
LATEST_TAG=$(git describe --tags $(git rev-list --tags --max-count=1))
echo "[INFO] Checking out latest release: $LATEST_TAG"
git checkout "$LATEST_TAG"

# Create build directory
mkdir -p build && cd build

# Configure with Python bindings
echo "[INFO] Configuring CMake (this may take a minute)..."
# Fix Python version conflict by explicitly specifying Python 3 paths
PYTHON3_EXE=$(which python3)
PYTHON3_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)

# Get Python include directory
if python3 -c "from distutils.sysconfig import get_python_inc" 2>/dev/null; then
    PYTHON3_INCLUDE=$(python3 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())")
else
    PYTHON3_INCLUDE=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))")
fi

# Get Python library
PYTHON3_LIBDIR=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")
PYTHON3_LIBNAME=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('LDLIBRARY') or sysconfig.get_config_var('LIBRARY') or 'libpython' + sysconfig.get_config_var('py_version_short') + '.so')")
PYTHON3_LIB="$PYTHON3_LIBDIR/$PYTHON3_LIBNAME"

# Fallback to standard location if not found
if [ ! -f "$PYTHON3_LIB" ]; then
    PYTHON3_LIB="/usr/lib/aarch64-linux-gnu/libpython${PYTHON3_VERSION}.so"
fi

echo "[INFO] Python 3 executable: $PYTHON3_EXE"
echo "[INFO] Python 3 include: $PYTHON3_INCLUDE"
echo "[INFO] Python 3 library: $PYTHON3_LIB"

# Force CMake to use Python 3, not Python 2
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_EXAMPLES=false \
    -DBUILD_GRAPHICAL_EXAMPLES=false \
    -DBUILD_PYTHON_BINDINGS:bool=true \
    -DPYTHON_EXECUTABLE="$PYTHON3_EXE" \
    -DPython_EXECUTABLE="$PYTHON3_EXE" \
    -DPython3_EXECUTABLE="$PYTHON3_EXE" \
    -DPYTHON_INCLUDE_DIR="$PYTHON3_INCLUDE" \
    -DPYTHON_LIBRARY="$PYTHON3_LIB" \
    -DPython3_INCLUDE_DIR="$PYTHON3_INCLUDE" \
    -DPython3_LIBRARY="$PYTHON3_LIB" \
    -DFORCE_RSUSB_BACKEND=ON \
    -DBUILD_WITH_CUDA=OFF \
    -DPython_FIND_VERSION_MAJOR=3 \
    -DPython3_FIND_VERSION_MAJOR=3

# Build (use all available cores)
NPROC=$(nproc)
echo "[INFO] Building with $NPROC cores (this will take 15-30 minutes)..."
make -j$NPROC

# Install
echo "[INFO] Installing librealsense..."
sudo make install

echo "[OK] librealsense built and installed"

# =============================================================================
# Step 3: Setup udev rules for USB permissions
# =============================================================================
echo ""
echo "[STEP 3/5] Setting up udev rules for RealSense cameras..."

cd "$LIBREALSENSE_DIR"
sudo cp config/99-realsense-libusb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger

# Add user to plugdev group
sudo usermod -aG plugdev $USER

echo "[OK] udev rules installed"

# =============================================================================
# Step 4: Install pyrealsense2 Python bindings
# =============================================================================
echo ""
echo "[STEP 4/5] Installing pyrealsense2 Python bindings..."

# Find the built pyrealsense2 library
PYRS_PATH=$(find "$LIBREALSENSE_DIR/build" -name "pyrealsense2*.so" -type f | head -1)

if [ -z "$PYRS_PATH" ]; then
    echo "[ERROR] Could not find pyrealsense2.so - build may have failed"
    exit 1
fi

PYRS_DIR=$(dirname "$PYRS_PATH")

# Get Python site-packages directory
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")

# Copy pyrealsense2 to site-packages
echo "[INFO] Installing pyrealsense2 to $SITE_PACKAGES"
sudo cp "$PYRS_DIR"/pyrealsense2*.so "$SITE_PACKAGES/"
sudo cp "$PYRS_DIR"/pybackend2*.so "$SITE_PACKAGES/" 2>/dev/null || true

# Update library path
echo "/usr/local/lib" | sudo tee /etc/ld.so.conf.d/librealsense.conf
sudo ldconfig

echo "[OK] pyrealsense2 installed"

# =============================================================================
# Step 5: Install Open3D for ARM64
# =============================================================================
echo ""
echo "[STEP 5/5] Installing Open3D for ARM64..."

# Open3D doesn't have official ARM64 wheels, so we need to build or use community builds
# Try pip first (may work with newer versions)
pip3 install --upgrade pip

# Try installing from pip (community ARM64 builds may be available)
if pip3 install open3d 2>/dev/null; then
    echo "[OK] Open3D installed from pip"
else
    echo "[INFO] pip install failed, trying alternative method..."
    
    # Install Open3D dependencies
    sudo apt-get install -y \
        libeigen3-dev \
        libpng-dev \
        libjpeg-dev \
        libtiff-dev \
        libglu1-mesa-dev \
        libglew-dev \
        libglfw3-dev
    
    # Try conda-forge or build from source
    echo "[WARN] Open3D may need to be built from source for ARM64."
    echo "[INFO] Attempting to install Open3D-CPU variant..."
    
    # Alternative: Use Open3D-CPU (lighter version)
    pip3 install open3d-cpu 2>/dev/null || {
        echo ""
        echo "[WARN] Could not install Open3D automatically."
        echo "[INFO] You may need to build Open3D from source:"
        echo "       https://github.com/isl-org/Open3D/blob/master/docs/arm.rst"
        echo ""
        echo "[INFO] As an alternative, you can use a simpler visualizer."
        echo "       The script will be modified to work without Open3D if needed."
    }
fi

# =============================================================================
# Verification
# =============================================================================
echo ""
echo "=============================================="
echo "Installation Complete - Verification"
echo "=============================================="

echo ""
echo "[TEST] Checking pyrealsense2..."
python3 -c "import pyrealsense2 as rs; print(f'  Version: {rs.__version__}')" 2>/dev/null && echo "[OK] pyrealsense2 works!" || echo "[WARN] pyrealsense2 import failed"

echo ""
echo "[TEST] Checking Open3D..."
python3 -c "import open3d as o3d; print(f'  Version: {o3d.__version__}')" 2>/dev/null && echo "[OK] Open3D works!" || echo "[WARN] Open3D import failed"

echo ""
echo "[TEST] Checking for RealSense cameras..."
python3 -c "
import pyrealsense2 as rs
ctx = rs.context()
devices = ctx.query_devices()
if len(devices) == 0:
    print('  No RealSense cameras detected')
    print('  Make sure camera is connected to USB 3.0 port')
else:
    for dev in devices:
        print(f'  Found: {dev.get_info(rs.camera_info.name)}')
        print(f'  Serial: {dev.get_info(rs.camera_info.serial_number)}')
" 2>/dev/null || echo "[WARN] Could not query cameras"

echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "IMPORTANT: You may need to log out and log back in"
echo "for the plugdev group membership to take effect."
echo ""
echo "To test your camera, run:"
echo "  realsense-viewer"
echo ""
echo "To run the point cloud visualizer:"
echo "  cd /home/sam/ASWY_NexHacks-main"
echo "  python3 live_arm_pointcloud.py"
echo ""
