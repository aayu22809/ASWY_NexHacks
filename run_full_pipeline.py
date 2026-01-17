#!/usr/bin/env python3
"""
Entry point for running the complete pipeline.

This script demonstrates the full workflow:
1. Load or generate test surface
2. Generate toolpath
3. Validate safety
4. Export results
5. Optionally launch visualizer

Usage:
    python run_full_pipeline.py --demo              # Run with demo surface
    python run_full_pipeline.py --input scan.ply    # Run with scanned data
"""

import argparse
import sys
import os
import numpy as np
from backend.path_planning.surface_model import SurfaceModel, ToolpathConfig, SimpleSurfaces
from backend.path_planning.raster_generator import RasterGenerator
from backend.utils.file_io import ResultsManager
from backend.safety.thermal_predictor import ThermalSafetyAgent


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
        description="Complete Plasma Jet Path Planning Pipeline"
    )
    
    parser.add_argument(
        '--input',
        type=str,
        help='Input point cloud file (.ply)'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run with demo cylindrical surface (arm-like)'
    )
    
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Launch visualizer after generation'
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
    
    args = parser.parse_args()
    
    # Ensure output directories exist
    os.makedirs('data/results', exist_ok=True)
    os.makedirs('data/toolpaths', exist_ok=True)
    os.makedirs('data/surfaces', exist_ok=True)
    os.makedirs('data/logs', exist_ok=True)
    
    print("\n" + "=" * 80)
    print("PLASMA JET PATH PLANNING - FULL PIPELINE")
    print("=" * 80)
    
    try:
        # STEP 1: Load or generate surface
        print("\n[STEP 1/5] Loading surface data...")
        print("-" * 80)
        
        if args.demo:
            print("Generating demo cylindrical surface (arm-like)...")
            points = SimpleSurfaces.cylinder(radius=40, length=150, samples=2000)
            surface_name = "demo_cylinder"
        elif args.input:
            if not os.path.exists(args.input):
                print(f"[ERROR] Input file not found: {args.input}")
                return 1
            print(f"Loading from {args.input}...")
            points = load_ply(args.input)
            surface_name = os.path.splitext(os.path.basename(args.input))[0]
        else:
            print("[ERROR] Either --input or --demo must be specified")
            parser.print_help()
            return 1
        
        print(f"[OK] Surface loaded: {len(points)} points")
        
        # STEP 2: Create surface model
        print("\n[STEP 2/5] Creating surface model...")
        print("-" * 80)
        surface = SurfaceModel(points, surface_name)
        print(f"[OK] Surface model created: {surface_name}")
        
        # STEP 3: Generate toolpath
        print("\n[STEP 3/5] Generating toolpath...")
        print("-" * 80)
        config = ToolpathConfig(
            standoff_distance=args.standoff,
            line_spacing=args.spacing,
            feed_rate=args.feed_rate,
            rapid_rate=200.0,
            use_bidirectional=True,
            points_per_line=60,
            name=surface_name
        )
        
        print(f"  Standoff distance: {config.standoff_distance} mm")
        print(f"  Line spacing: {config.line_spacing} mm")
        print(f"  Feed rate: {config.feed_rate} mm/min")
        
        generator = RasterGenerator(surface, config)
        toolpath = generator.generate()
        
        treatment = [pt for pt in toolpath if not pt.is_rapid]
        length = sum(np.linalg.norm(treatment[i+1].position - treatment[i].position) 
                    for i in range(len(treatment)-1))
        
        print(f"[OK] Toolpath generated:")
        print(f"  Total points: {len(toolpath)}")
        print(f"  Treatment points: {len(treatment)}")
        print(f"  Treatment length: {length:.1f} mm")
        
        # STEP 4: Safety validation
        print("\n[STEP 4/5] Validating safety...")
        print("-" * 80)
        
        safety_agent = ThermalSafetyAgent(max_temp_c=40.0)
        
        # Test with typical parameters
        test_state = {
            "current_temp": 36.5,
            "planned_speed": config.feed_rate,
            "plasma_power": 80.0,
            "standoff_mm": config.standoff_distance,
            "tissue_type": 0
        }
        
        action = safety_agent.recommend_action(test_state)
        
        print(f"  Safety check: {action['action'].upper()}")
        print(f"  Predicted temperature: {action['predicted_temp']:.1f}°C")
        print(f"  Reason: {action['reason']}")
        
        if action['action'] == 'stop':
            print("[WARNING] Safety check recommends stopping!")
            print("          Consider reducing feed rate or increasing standoff")
        else:
            print("[OK] Toolpath passes safety validation")
        
        # STEP 5: Save results
        print("\n[STEP 5/5] Saving results...")
        print("-" * 80)
        
        results_file = ResultsManager.save_results(surface, toolpath, config)
        gcode_file = ResultsManager.export_gcode(toolpath)
        csv_file = ResultsManager.export_csv(toolpath)
        surface_file = surface.save()
        
        print(f"[OK] Results saved:")
        print(f"  Results:  {results_file}")
        print(f"  G-code:   {gcode_file}")
        print(f"  CSV:      {csv_file}")
        print(f"  Surface:  {surface_file}")
        
        # Summary
        print("\n" + "=" * 80)
        print("PIPELINE COMPLETE!")
        print("=" * 80)
        print(f"\nSummary:")
        print(f"  Surface:          {surface_name}")
        print(f"  Points scanned:   {len(points):,}")
        print(f"  Toolpath points:  {len(toolpath):,}")
        print(f"  Treatment length: {length:.1f} mm")
        print(f"  Safety status:    {action['action'].upper()}")
        print(f"\nNext steps:")
        print(f"  1. Review results: python run_visualizer.py")
        print(f"  2. Load G-code to robot: {gcode_file}")
        print(f"  3. Monitor during treatment")
        print("=" * 80 + "\n")
        
        # Launch visualizer if requested
        if args.visualize:
            print("\n[INFO] Launching visualizer...")
            from backend.visualization.interactive_viewer import InteractiveVisualizer
            import tkinter as tk
            
            root = tk.Tk()
            app = InteractiveVisualizer(root)
            root.mainloop()
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

