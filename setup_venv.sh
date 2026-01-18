#!/bin/bash

# Unified Virtual Environment Setup Script
# Creates and configures a Python virtual environment with all project dependencies

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}   Cold Plasma Treatment System${NC}"
echo -e "${GREEN}   Virtual Environment Setup${NC}"
echo -e "${BLUE}=================================================${NC}"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed.${NC}"
    echo "Please install Python 3.10 or higher."
    exit 1
fi

# Check Python version (need 3.10+)
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}Error: Python 3.10 or higher is required.${NC}"
    echo "Found Python version: $PYTHON_VERSION"
    exit 1
fi

echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"

# Check if venv already exists
if [ -d "venv" ]; then
    echo -e "\n${YELLOW}Virtual environment already exists.${NC}"
    read -p "Remove existing venv and create fresh one? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Removing existing virtual environment...${NC}"
        rm -rf venv
    else
        echo -e "${BLUE}Using existing virtual environment.${NC}"
        echo -e "${GREEN}To activate: source venv/bin/activate${NC}"
        exit 0
    fi
fi

# Create virtual environment
echo -e "\n${BLUE}[1/4] Creating virtual environment...${NC}"
python3 -m venv venv
echo -e "${GREEN}✓ Virtual environment created${NC}"

# Activate virtual environment
echo -e "\n${BLUE}[2/4] Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo -e "\n${BLUE}[3/4] Upgrading pip...${NC}"
pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install dependencies
echo -e "\n${BLUE}[4/4] Installing dependencies (this may take a few minutes)...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed from requirements.txt${NC}"
else
    echo -e "${RED}Error: requirements.txt not found!${NC}"
    exit 1
fi

# Verify critical imports
echo -e "\n${BLUE}Verifying installation...${NC}"
python3 -c "import numpy; print('✓ numpy')" 2>/dev/null || { echo -e "${RED}✗ numpy failed${NC}"; exit 1; }
python3 -c "import fastapi; print('✓ fastapi')" 2>/dev/null || { echo -e "${RED}✗ fastapi failed${NC}"; exit 1; }
python3 -c "import open3d; print('✓ open3d')" 2>/dev/null || { echo -e "${RED}✗ open3d failed${NC}"; exit 1; }
python3 -c "import scipy; print('✓ scipy')" 2>/dev/null || { echo -e "${RED}✗ scipy failed${NC}"; exit 1; }
python3 -c "import matplotlib; print('✓ matplotlib')" 2>/dev/null || { echo -e "${RED}✗ matplotlib failed${NC}"; exit 1; }

# Check for tkinter (needed for interactivevisualizer.py)
echo -e "\n${BLUE}Checking for tkinter (needed for visualizer)...${NC}"
python3 -c "import tkinter; print('✓ tkinter')" 2>/dev/null || { 
    echo -e "${YELLOW}⚠ tkinter not found${NC}"
    echo -e "${YELLOW}  On Ubuntu/Debian: sudo apt-get install python3-tk${NC}"
    echo -e "${YELLOW}  On macOS: Usually included with Python${NC}"
    echo -e "${YELLOW}  On Windows: Usually included with Python${NC}"
}

echo -e "\n${BLUE}=================================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${BLUE}=================================================${NC}"
echo -e "\nTo activate the virtual environment, run:"
echo -e "${GREEN}  source venv/bin/activate${NC}"
echo -e "\nTo deactivate, run:"
echo -e "${GREEN}  deactivate${NC}"
echo ""
