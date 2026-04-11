#!/bin/bash
# Launch the interactive visualizer with D405 camera support
cd "$(dirname "$0")"
source venv/bin/activate
cd gcodegen
python interactivevisualizer.py
