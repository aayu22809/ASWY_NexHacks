import os, re, glob
import argparse
import numpy as np
import open3d as o3d
import cv2

COLOR_PATTERNS = ["*Color*.*", "*color*.*", "*RGB*.*", "*rgb*.*"]
DEPTH_PATTERNS = ["*Depth*.*", "*depth*.*", "*Z16*.*", "*z16*.*"]

def find_files(data_dir, patterns):
    files = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(data_dir, "**", pat), recursive=True))
    return sorted(set(files))

def extract_ts(path):
    # grabs the last floating-ish number in the filename
    # e.g. hand_export_Color_145447.15600000001723.png -> 145447.156...
    m = re.findall(r"(\d+\.\d+|\d+)", os.path.basename(path))
    return float(m[-1]) if m else None

def read_metadata(data_dir, prefix):
    """Read depth scale from metadata file created by bagtopng.py"""
    meta_path = os.path.join(data_dir, f"{prefix}_meta.txt")
    depth_scale_m_per_unit = None
    depth_saved_as = None
    
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            for line in f:
                if line.startswith("depth_scale_m_per_unit="):
                    depth_scale_m_per_unit = float(line.split("=")[1].strip())
                elif line.startswith("depth_saved_as="):
                    depth_saved_as = line.split("=")[1].strip()
    
    return depth_scale_m_per_unit, depth_saved_as

def main():
    ap = argparse.ArgumentParser(description="Reconstruct 3D mesh from color/depth PNG pairs")
    ap.add_argument("--data_dir", default=os.path.expanduser("~/Documents"),
                    help="Directory containing color/depth PNG files (default: ~/Documents)")
    ap.add_argument("--prefix", default="hand_export",
                    help="Filename prefix used by bagtopng.py (default: hand_export)")
    ap.add_argument("--out_mesh", default=None,
                    help="Output mesh file (default: <data_dir>/<prefix>_mesh.ply)")
    ap.add_argument("--voxel_length", type=float, default=0.003,
                    help="TSDF voxel size in meters (default: 0.003)")
    ap.add_argument("--sdf_trunc", type=float, default=0.02,
                    help="TSDF truncation distance in meters (default: 0.02)")
    ap.add_argument("--depth_trunc", type=float, default=1.0,
                    help="Maximum depth in meters (default: 1.0)")
    args = ap.parse_args()
    
    data_dir = os.path.expanduser(args.data_dir)
    if args.out_mesh is None:
        out_mesh = os.path.join(data_dir, f"{args.prefix}_mesh.ply")
    else:
        out_mesh = os.path.expanduser(args.out_mesh)
    
    color_paths = find_files(data_dir, COLOR_PATTERNS)
    depth_paths = find_files(data_dir, DEPTH_PATTERNS)

    if not color_paths or not depth_paths:
        raise RuntimeError(f"Could not find both color and depth frames under {data_dir}")

    # Build (timestamp, path) lists
    colors = [(extract_ts(p), p) for p in color_paths]
    depths = [(extract_ts(p), p) for p in depth_paths]
    colors = [(t, p) for t, p in colors if t is not None]
    depths = [(t, p) for t, p in depths if t is not None]
    colors.sort()
    depths.sort()

    depth_ts = np.array([t for t, _ in depths], dtype=np.float64)
    depth_p = [p for _, p in depths]

    # Pair each color with nearest depth by timestamp
    pairs = []
    for ct, cp in colors:
        idx = int(np.argmin(np.abs(depth_ts - ct)))
        dp = depth_p[idx]
        pairs.append((cp, dp))

    print(f"Scanning: {data_dir}")
    print(f"Found colors={len(colors)} depths={len(depths)} -> paired={len(pairs)}")
    if pairs:
        print("Example pair:")
        print("  color:", pairs[0][0])
        print("  depth:", pairs[0][1])
    
    # Read depth scale from metadata
    depth_scale_m_per_unit, depth_saved_as = read_metadata(data_dir, args.prefix)
    
    if depth_scale_m_per_unit is not None:
        print(f"Found metadata: depth_scale={depth_scale_m_per_unit} m/unit, saved_as={depth_saved_as}")
        if depth_saved_as == "raw":
            # Depth is in sensor units, convert to meters: depth_m = depth_raw * scale
            # Open3D expects depth in meters, so depth_scale = 1 / scale
            depth_scale = 1.0 / depth_scale_m_per_unit
        elif depth_saved_as == "mm":
            # Depth is in millimeters, convert to meters: depth_m = depth_mm / 1000
            depth_scale = 1000.0
        else:
            print(f"Warning: Unknown depth format '{depth_saved_as}', using default depth_scale=1000.0")
            depth_scale = 1000.0
    else:
        print("Warning: No metadata file found, using default depth_scale=1000.0")
        print("  (Assuming depth is in millimeters)")
        depth_scale = 1000.0
    
    print(f"Using depth_scale={depth_scale} (depth values will be divided by this to get meters)")
    
    # Intrinsics (starting default; we can refine later)
    intr = o3d.camera.PinholeCameraIntrinsic(
        o3d.camera.PinholeCameraIntrinsicParameters.PrimeSenseDefault
    )

    volume = o3d.pipelines.integration.ScalableTSDFVolume(
        voxel_length=args.voxel_length,
        sdf_trunc=args.sdf_trunc,
        color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8
    )
    
    prev_rgbd = None
    T = np.eye(4)
    
    for i, (cp, dp) in enumerate(pairs):
        # Read with Open3D
        color_o3d = o3d.io.read_image(cp)
        depth_o3d = o3d.io.read_image(dp)

        # Convert to numpy to resize depth to match color
        color_np = np.asarray(color_o3d)            # HxWx3 uint8
        depth_np = np.asarray(depth_o3d)            # HxW uint16 or similar

        ch, cw = color_np.shape[:2]
        dh, dw = depth_np.shape[:2]

        if (dh, dw) != (ch, cw):
            # Resize depth with nearest-neighbor (do NOT blur depth)
            depth_np = cv2.resize(depth_np, (cw, ch), interpolation=cv2.INTER_NEAREST)

        # Back to Open3D Images
        color = o3d.geometry.Image(color_np)
        depth = o3d.geometry.Image(depth_np)

        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            color, depth,
            depth_scale=depth_scale,
            depth_trunc=args.depth_trunc,
            convert_rgb_to_intensity=False
        )
        
        if prev_rgbd is not None:
            option = o3d.pipelines.odometry.OdometryOption()
            success, trans, _ = o3d.pipelines.odometry.compute_rgbd_odometry(
                prev_rgbd, rgbd, intr, np.eye(4),
                o3d.pipelines.odometry.RGBDOdometryJacobianFromHybridTerm(),
                option
            )
            if success:
                T = T @ trans
            else:
                prev_rgbd = rgbd
                continue
        
        volume.integrate(rgbd, intr, np.linalg.inv(T))
        prev_rgbd = rgbd
        
        if i % 30 == 0:
            print(f"Integrated {i}/{len(pairs)}")
    
    print("Extracting mesh...")
    mesh = volume.extract_triangle_mesh()
    mesh.compute_vertex_normals()
    
    print("Cleaning mesh...")
    mesh = mesh.remove_degenerate_triangles()
    mesh = mesh.remove_duplicated_triangles()
    mesh = mesh.remove_duplicated_vertices()
    mesh = mesh.remove_non_manifold_edges()
    
    o3d.io.write_triangle_mesh(out_mesh, mesh)
    print(f"Wrote: {out_mesh}")
    print(f"Mesh has {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles")

if __name__ == "__main__":
    main()
