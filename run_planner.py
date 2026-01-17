#!/usr/bin/env python3
"""
Entry point for running path planning.

Usage:
    python run_planner.py --input scan.ply          # Plan from scan
    python run_planner.py --demo                    # Run demo surfaces
    python run_planner.py --input scan.ply --standoff 7.0 --spacing 3.0
"""

import argparse
import sys
import os
import numpy as np
from backend.path_planning.surface_model import SurfaceModel, ToolpathConfig, SimpleSurfaces
from backend.path_planning.raster_generator import RasterGenerator, test_surface
from backend.utils.file_io import ResultsManager


def load_ply(filename):
    """Load point cloud from PLY file."""
    import open3d as o3d
    
    pcd = o3d.io.read_point_cloud(filename)
    points = np.asarray(pcd.points)
    
    if len(points) == 0:
        raise ValueError(f"Empty point cloud in {filename}")
    
    print(f"[OK] Loaded {len(points)} points from {filename}")
    return points


def main():
    parser = argparse.ArgumentParser(
        description="Plasma Jet Path Planner - Generate toolpaths from 3D scans"
    )
    
    parser.add_argument(
        '--input',
        type=str,
        help='Input point cloud file (.ply)'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run with demo test surfaces'
    )
    
    parser.add_argument(
        '--standoff',
        type=float,
        default=5.0,
        help='Standoff distance in mm (default: 5.0)'
    )
    
    parser.add_argument(
        '--spacing',
        type=float,
        default=4.0,
        help='Line spacing in mm (default: 4.0)'
    )
    
    parser.add_argument(
        '--feed-rate',
        type=float,
        default=50.0,
        help='Feed rate in mm/min (default: 50.0)'
    )
    
    parser.add_argument(
        '--rapid-rate',
        type=float,
        default=200.0,
        help='Rapid rate in mm/min (default: 200.0)'
    )
    
    parser.add_argument(
        '--points-per-line',
        type=int,
        default=60,
        help='Points per raster line (default: 60)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output G-code filename'
    )
    
    args = parser.parse_args()
    
    # Ensure output directories exist
    os.makedirs('data/results', exist_ok=True)
    os.makedirs('data/toolpaths', exist_ok=True)
    os.makedirs('data/surfaces', exist_ok=True)
    
    if args.demo:
        # Run demo with test surfaces
        print("=" * 70)
        print("RASTER PATTERN TEST - DEMO SURFACES")
        print("=" * 70)
        
        surfaces_to_test = [
            ("Gentle_Curve", SimpleSurfaces.gentle_curve()),
            ("Cylinder", SimpleSurfaces.cylinder()),
            ("Saddle", SimpleSurfaces.saddle()),
            ("Sphere_Section", SimpleSurfaces.sphere_section())
        ]
        
        for surface_name, points in surfaces_to_test:
            test_surface(points, surface_name, save_results=True)
        
        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETE!")
        print("=" * 70)
        return 0
    
    if not args.input:
        print("[ERROR] Either --input or --demo must be specified")
        parser.print_help()
        return 1
    
    if not os.path.exists(args.input):
        print(f"[ERROR] Input file not found: {args.input}")
        return 1
    
    try:
        # Load point cloud
        print(f"\n[1/4] Loading point cloud from {args.input}...")
        points = load_ply(args.input)
        
        # Create surface model
        print(f"\n[2/4] Creating surface model...")
        surface_name = os.path.splitext(os.path.basename(args.input))[0]
        surface = SurfaceModel(points, surface_name)
        
        # Configure toolpath
        config = ToolpathConfig(
            standoff_distance=args.standoff,
            line_spacing=args.spacing,
            feed_rate=args.feed_rate,
            rapid_rate=args.rapid_rate,
            use_bidirectional=True,
            points_per_line=args.points_per_line,
            name=surface_name
        )
        
        # Generate toolpath
        print(f"\n[3/4] Generating raster toolpath...")
        generator = RasterGenerator(surface, config)
        toolpath = generator.generate()
        
        # Save results
        print(f"\n[4/4] Saving results...")
        results_file = ResultsManager.save_results(surface, toolpath, config)
        
        if args.output:
            gcode_file = ResultsManager.export_gcode(toolpath, args.output)
        else:
            gcode_file = ResultsManager.export_gcode(toolpath)
        
        csv_file = ResultsManager.export_csv(toolpath)
        surface_file = surface.save()
        
        # Summary
        treatment = [pt for pt in toolpath if not pt.is_rapid]
        length = sum(np.linalg.norm(treatment[i+1].position - treatment[i].position) 
                    for i in range(len(treatment)-1))
        
        print(f"\n{'='*70}")
        print("RESULTS SUMMARY")
        print(f"{'='*70}")
        print(f"Total points:      {len(toolpath)}")
        print(f"Treatment points:  {len(treatment)}")
        print(f"Rapid moves:       {len([pt for pt in toolpath if pt.is_rapid])}")
        print(f"Treatment length:  {length:.1f} mm")
        print(f"Raster lines:      {len([pt for pt in toolpath if pt.is_rapid]) + 1}")
        print(f"\nFiles saved:")
        print(f"  Results:  {results_file}")
        print(f"  G-code:   {gcode_file}")
        print(f"  CSV:      {csv_file}")
        print(f"  Surface:  {surface_file}")
        print(f"{'='*70}\n")
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

