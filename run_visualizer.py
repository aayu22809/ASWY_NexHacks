#!/usr/bin/env python3
"""
Entry point for running the interactive visualizer.

Usage:
    python run_visualizer.py                    # Launch GUI
    python run_visualizer.py --file results.json # Load file
"""

import argparse
import sys
import os
import tkinter as tk
from backend.visualization.interactive_viewer import InteractiveVisualizer


def main():
    parser = argparse.ArgumentParser(
        description="Interactive 3D Visualizer for Toolpaths and Surfaces"
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='Results file to load on startup (.json or .pkl)'
    )
    
    args = parser.parse_args()
    
    try:
        # Create Tkinter root
        root = tk.Tk()
        
        # Create visualizer application
        app = InteractiveVisualizer(root)
        
        # Load file if specified
        if args.file:
            if not os.path.exists(args.file):
                print(f"[WARNING] File not found: {args.file}")
            else:
                # TODO: Implement auto-load functionality
                print(f"[INFO] Use File > Open to load: {args.file}")
        
        # Run main loop
        root.mainloop()
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

