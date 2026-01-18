#!/usr/bin/env python3
"""
Unified script to convert a RealSense .bag file to a 3D mesh.

This script:
1. Extracts color and depth frames from the .bag file (using bagtopng.py logic)
2. Reconstructs a 3D mesh using TSDF volume integration (using reconstruct_tsdf.py logic)

Usage:
    python3 bag_to_3d_model.py --bag input.bag [options]
"""

import os
import sys
import argparse
import subprocess
import tempfile
import shutil


def main():
    ap = argparse.ArgumentParser(
        description="Convert RealSense .bag file to 3D mesh",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python3 bag_to_3d_model.py --bag recording.bag

  # Specify output directory and mesh name
  python3 bag_to_3d_model.py --bag recording.bag --out_dir ./output --mesh_name my_model.ply

  # Process every 5th frame with max 200 frames
  python3 bag_to_3d_model.py --bag recording.bag --stride 5 --max_frames 200
        """
    )
    
    # Bag file input
    ap.add_argument("--bag", required=True, help="Path to input .bag file")
    
    # Output options
    ap.add_argument("--out_dir", default=None,
                    help="Output directory for frames and mesh (default: same directory as .bag)")
    ap.add_argument("--mesh_name", default=None,
                    help="Output mesh filename (default: <bag_name>_mesh.ply)")
    ap.add_argument("--prefix", default=None,
                    help="Filename prefix for extracted frames (default: <bag_name>)")
    
    # Frame extraction options
    ap.add_argument("--stride", type=int, default=1,
                    help="Save every Nth frame (default: 1 = save all)")
    ap.add_argument("--max_frames", type=int, default=0,
                    help="Maximum frames to extract (0 = no limit, default: 0)")
    ap.add_argument("--depth_unit", choices=["raw", "mm"], default="raw",
                    help="Depth unit: 'raw' = sensor units (recommended), 'mm' = millimeters")
    
    # Mesh reconstruction options
    ap.add_argument("--voxel_length", type=float, default=0.003,
                    help="TSDF voxel size in meters (default: 0.003)")
    ap.add_argument("--sdf_trunc", type=float, default=0.02,
                    help="TSDF truncation distance in meters (default: 0.02)")
    ap.add_argument("--depth_trunc", type=float, default=1.0,
                    help="Maximum depth in meters (default: 1.0)")
    
    # Advanced options
    ap.add_argument("--keep_frames", action="store_true",
                    help="Keep extracted PNG frames after reconstruction (default: delete them)")
    ap.add_argument("--skip_extraction", action="store_true",
                    help="Skip frame extraction (assume frames already exist)")
    
    args = ap.parse_args()
    
    # Validate bag file exists
    bag_path = os.path.abspath(args.bag)
    if not os.path.exists(bag_path):
        print(f"Error: Bag file not found: {bag_path}")
        sys.exit(1)
    
    # Determine output directory
    if args.out_dir is None:
        out_dir = os.path.dirname(bag_path)
        if not out_dir:
            out_dir = os.getcwd()
    else:
        out_dir = os.path.expanduser(args.out_dir)
    
    os.makedirs(out_dir, exist_ok=True)
    
    # Determine prefix
    if args.prefix is None:
        prefix = os.path.splitext(os.path.basename(bag_path))[0]
    else:
        prefix = args.prefix
    
    # Determine mesh output path
    if args.mesh_name is None:
        mesh_path = os.path.join(out_dir, f"{prefix}_mesh.ply")
    else:
        mesh_path = os.path.join(out_dir, args.mesh_name)
    
    print("=" * 70)
    print("RealSense .bag to 3D Model Converter")
    print("=" * 70)
    print(f"Input bag file: {bag_path}")
    print(f"Output directory: {out_dir}")
    print(f"Frame prefix: {prefix}")
    print(f"Output mesh: {mesh_path}")
    print()
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bagtopng_script = os.path.join(script_dir, "bagtopng.py")
    reconstruct_script = os.path.join(script_dir, "reconstruct_tsdf.py")
    
    # Step 1: Extract frames from bag file
    if not args.skip_extraction:
        print("Step 1: Extracting frames from .bag file...")
        print("-" * 70)
        
        cmd = [
            sys.executable, bagtopng_script,
            "--bag", bag_path,
            "--out_dir", out_dir,
            "--prefix", prefix,
            "--stride", str(args.stride),
            "--max_frames", str(args.max_frames),
            "--depth_unit", args.depth_unit
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=False)
            print()
        except subprocess.CalledProcessError as e:
            print(f"Error during frame extraction (exit code {e.returncode})")
            sys.exit(1)
        except FileNotFoundError:
            print(f"Error: Could not find {bagtopng_script}")
            sys.exit(1)
    else:
        print("Step 1: Skipping frame extraction (--skip_extraction)")
        print()
    
    # Step 2: Reconstruct 3D mesh
    print("Step 2: Reconstructing 3D mesh...")
    print("-" * 70)
    
    cmd = [
        sys.executable, reconstruct_script,
        "--data_dir", out_dir,
        "--prefix", prefix,
        "--out_mesh", mesh_path,
        "--voxel_length", str(args.voxel_length),
        "--sdf_trunc", str(args.sdf_trunc),
        "--depth_trunc", str(args.depth_trunc)
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print()
    except subprocess.CalledProcessError as e:
        print(f"Error during mesh reconstruction (exit code {e.returncode})")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Could not find {reconstruct_script}")
        sys.exit(1)
    
    # Step 3: Cleanup (optional)
    if not args.keep_frames:
        print("Step 3: Cleaning up extracted frames...")
        print("-" * 70)
        
        import glob
        color_patterns = [f"{prefix}_Color_*.png", f"{prefix}_color_*.png"]
        depth_patterns = [f"{prefix}_Depth_*.png", f"{prefix}_depth_*.png"]
        meta_pattern = f"{prefix}_meta.txt"
        
        removed = 0
        for pattern in color_patterns + depth_patterns:
            for f in glob.glob(os.path.join(out_dir, pattern)):
                os.remove(f)
                removed += 1
        
        meta_file = os.path.join(out_dir, meta_pattern)
        if os.path.exists(meta_file):
            os.remove(meta_file)
            removed += 1
        
        print(f"Removed {removed} temporary files")
        print()
    
    # Summary
    print("=" * 70)
    print("Conversion complete!")
    print(f"3D mesh saved to: {mesh_path}")
    
    if os.path.exists(mesh_path):
        file_size = os.path.getsize(mesh_path) / (1024 * 1024)  # MB
        print(f"Mesh file size: {file_size:.2f} MB")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
