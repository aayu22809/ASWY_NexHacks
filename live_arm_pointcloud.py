#!/usr/bin/env python3
"""
================================================================================
Intel RealSense L515 - Live Arm Point Cloud Capture
================================================================================

DESCRIPTION:
    Real-time RGB-D point cloud capture from Intel RealSense L515 with
    arm-focused filtering, visualization, and mesh generation capabilities.

REQUIREMENTS:
    Python 3.10+ (including 3.13)
    pyrealsense2 >= 2.56.5 (for Python 3.13 support)
    Intel RealSense L515 camera
    USB 3.0 port

SETUP INSTRUCTIONS:

1. Create Virtual Environment:
   Windows:
       python -m venv venv
       .venv\\Scripts\\activate
   
   Linux/macOS:
       python3 -m venv venv
       source venv/bin/activate

2. Install Dependencies:
       pip install --upgrade pip
       pip install -r requirements.txt

3. Run the Script:
       python live_arm_pointcloud.py

CONTROLS:
    Q / ESC  : Quit application
    S        : Save current point cloud to .ply file
    M        : Generate mesh snapshot (Poisson reconstruction) and save

TROUBLESHOOTING:

1. Camera Not Found:
   - Ensure L515 is connected to a USB 3.0 port (blue connector)
   - Try different USB ports or cables
   - Update firmware using Intel RealSense Viewer
   - On Windows: Check Device Manager for proper driver installation

2. Linux Permissions:
   - Add user to plugdev group: sudo adduser $USER plugdev
   - Log out and log back in
   - Check udev rules: https://github.com/IntelRealSense/librealsense/blob/master/config/99-realsense-libusb.rules

3. Performance Issues:
   - Adjust VOXEL_SIZE (increase for better FPS)
   - Disable ROI filtering if not needed
   - Reduce spatial/temporal filter strength
   - Close other applications using camera

4. L515 SPECIFIC NOTES:
   - For Python 3.13: Requires pyrealsense2 >= 2.56.5
   - For older Python: Use pyrealsense2 >= 2.50.0
   - Optimal depth range: 0.25m to 1.5m (laser scanner technology)
   - This script defaults to 0.20-0.90m for arm tracking
   - Avoid reflective surfaces and direct sunlight
   - White background provides excellent contrast for arm segmentation

================================================================================
"""

import pyrealsense2 as rs
import numpy as np
import open3d as o3d
import time
from datetime import datetime


# ============================================================================
# CONFIGURATION - Adjust these parameters as needed
# ============================================================================

# Stream Configuration
COLOR_WIDTH = 640
COLOR_HEIGHT = 480
COLOR_FPS = 30
DEPTH_WIDTH = 640
DEPTH_HEIGHT = 480
DEPTH_FPS = 30

# Depth Range for Arm Filtering (meters)
Z_MIN = 0.20  # Minimum depth (20 cm)
Z_MAX = 0.90  # Maximum depth (90 cm)

# Region of Interest (ROI) - Center crop to reduce background
USE_ROI = True
ROI_CENTER_WIDTH_RATIO = 0.6   # Use center 60% width
ROI_CENTER_HEIGHT_RATIO = 0.6  # Use center 60% height

# Point Cloud Downsampling
VOXEL_SIZE = 0.003  # 3mm voxel grid (smaller = higher quality, lower FPS)

# RealSense Depth Filters
SPATIAL_FILTER_MAGNITUDE = 2  # Smooth spatial noise (1-5)
SPATIAL_FILTER_ALPHA = 0.5    # Weight of current pixel (0-1)
TEMPORAL_FILTER_ALPHA = 0.4   # Temporal smoothing strength (0-1)
TEMPORAL_FILTER_DELTA = 20    # Threshold for temporal update (pixels)
HOLE_FILLING_MODE = 1         # 0=off, 1=2px, 2=4px, 3=8px, 4=16px, 5=unlimited

# Mesh Generation
POISSON_DEPTH = 9             # Octree depth for Poisson reconstruction (6-12)
MESH_FORMAT = "ply"           # Output format: "ply" or "obj"

# FPS Display
FPS_UPDATE_INTERVAL = 1.0     # Print FPS every N seconds


# ============================================================================
# Global State
# ============================================================================

g_quit_flag = False
g_current_pcd = None


# ============================================================================
# RealSense Pipeline Setup
# ============================================================================

def setup_realsense_pipeline():
    """
    Initialize RealSense pipeline with L515, configure streams, and setup filters.
    
    Returns:
        tuple: (pipeline, align, pc, spatial_filter, temporal_filter, hole_filter)
    """
    print("Initializing Intel RealSense L515...")
    
    # Create pipeline
    pipeline = rs.pipeline()
    config = rs.config()
    
    # Enable streams
    config.enable_stream(rs.stream.color, COLOR_WIDTH, COLOR_HEIGHT, 
                        rs.format.bgr8, COLOR_FPS)
    config.enable_stream(rs.stream.depth, DEPTH_WIDTH, DEPTH_HEIGHT, 
                        rs.format.z16, DEPTH_FPS)
    
    # Start pipeline with error handling
    try:
        profile = pipeline.start(config)
        print(f"[OK] Pipeline started successfully")
        
        # Get device info
        device = profile.get_device()
        device_name = device.get_info(rs.camera_info.name)
        serial = device.get_info(rs.camera_info.serial_number)
        firmware = device.get_info(rs.camera_info.firmware_version)
        print(f"[OK] Device: {device_name}")
        print(f"[OK] Serial: {serial}")
        print(f"[OK] Firmware: {firmware}")
        
    except Exception as e:
        print(f"\n[ERROR] Could not start RealSense pipeline!")
        print(f"Details: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure L515 is connected to USB 3.0 port")
        print("  2. Try different USB port or cable")
        print("  3. Check Windows Device Manager for driver issues")
        print("  4. Update firmware using Intel RealSense Viewer")
        raise
    
    # Create align object to align depth to color
    align = rs.align(rs.stream.color)
    
    # Create point cloud object
    pc = rs.pointcloud()
    
    # Setup depth filters for stability
    spatial_filter = rs.spatial_filter()
    spatial_filter.set_option(rs.option.filter_magnitude, SPATIAL_FILTER_MAGNITUDE)
    spatial_filter.set_option(rs.option.filter_smooth_alpha, SPATIAL_FILTER_ALPHA)
    
    temporal_filter = rs.temporal_filter()
    temporal_filter.set_option(rs.option.filter_smooth_alpha, TEMPORAL_FILTER_ALPHA)
    temporal_filter.set_option(rs.option.filter_smooth_delta, TEMPORAL_FILTER_DELTA)
    
    hole_filter = rs.hole_filling_filter(HOLE_FILLING_MODE)
    
    print(f"[OK] Depth filters configured (spatial + temporal + hole filling)")
    print(f"[OK] Alignment to color enabled")
    print(f"[OK] Point cloud generator ready")
    
    return pipeline, align, pc, spatial_filter, temporal_filter, hole_filter


# ============================================================================
# Point Cloud Processing
# ============================================================================

def process_frames_to_pointcloud(frames, align, pc, spatial_filter, 
                                 temporal_filter, hole_filter):
    """
    Process RealSense frames into filtered, colored point cloud.
    
    Args:
        frames: RealSense frameset
        align: RealSense align object
        pc: RealSense pointcloud object
        spatial_filter, temporal_filter, hole_filter: RealSense filters
    
    Returns:
        open3d.geometry.PointCloud or None if processing fails
    """
    
    # Align depth to color
    aligned_frames = align.process(frames)
    
    depth_frame = aligned_frames.get_depth_frame()
    color_frame = aligned_frames.get_color_frame()
    
    if not depth_frame or not color_frame:
        return None
    
    # Apply depth filters for stability
    try:
        depth_frame = spatial_filter.process(depth_frame)
        depth_frame = temporal_filter.process(depth_frame)
        depth_frame = hole_filter.process(depth_frame)
    except Exception as e:
        print(f"[WARN] Filter application failed: {e}")
    
    # Generate point cloud
    pc.map_to(color_frame)
    points = pc.calculate(depth_frame)
    
    # Extract vertices and texture coordinates
    vertices = np.asanyarray(points.get_vertices()).view(np.float32).reshape(-1, 3)
    tex_coords = np.asanyarray(points.get_texture_coordinates()).view(np.float32).reshape(-1, 2)
    
    # Get color data
    color_image = np.asanyarray(color_frame.get_data())
    
    # Map texture coordinates to colors
    # Texture coords are normalized [0,1], convert to pixel coords
    width = color_frame.get_width()
    height = color_frame.get_height()
    
    u = (tex_coords[:, 0] * (width - 1)).astype(np.int32)
    v = (tex_coords[:, 1] * (height - 1)).astype(np.int32)
    
    # Clamp to valid range
    u = np.clip(u, 0, width - 1)
    v = np.clip(v, 0, height - 1)
    
    # Sample colors (BGR -> RGB) and normalize to [0, 1]
    colors = color_image[v, u, :].astype(np.float32) / 255.0
    colors = colors[:, ::-1]  # BGR to RGB
    
    # Filter 1: Remove invalid points (NaN, Inf)
    valid_mask = np.isfinite(vertices).all(axis=1)
    
    # Filter 2: Depth range (arm-focused)
    depth_mask = (vertices[:, 2] >= Z_MIN) & (vertices[:, 2] <= Z_MAX)
    
    # Filter 3: ROI (optional center crop)
    if USE_ROI:
        x_min = (1.0 - ROI_CENTER_WIDTH_RATIO) / 2.0
        x_max = (1.0 + ROI_CENTER_WIDTH_RATIO) / 2.0
        y_min = (1.0 - ROI_CENTER_HEIGHT_RATIO) / 2.0
        y_max = (1.0 + ROI_CENTER_HEIGHT_RATIO) / 2.0
        
        roi_mask = (
            (tex_coords[:, 0] >= x_min) & (tex_coords[:, 0] <= x_max) &
            (tex_coords[:, 1] >= y_min) & (tex_coords[:, 1] <= y_max)
        )
    else:
        roi_mask = np.ones(len(vertices), dtype=bool)
    
    # Combine all filters
    final_mask = valid_mask & depth_mask & roi_mask
    
    filtered_vertices = vertices[final_mask]
    filtered_colors = colors[final_mask]
    
    if len(filtered_vertices) == 0:
        return None
    
    # Create Open3D point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(filtered_vertices)
    pcd.colors = o3d.utility.Vector3dVector(filtered_colors)
    
    # Downsample for performance
    if VOXEL_SIZE > 0:
        pcd = pcd.voxel_down_sample(voxel_size=VOXEL_SIZE)
    
    return pcd


# ============================================================================
# Save Point Cloud
# ============================================================================

def save_pointcloud(pcd):
    """Save current point cloud to .ply file with timestamp."""
    if pcd is None or not pcd.has_points():
        print("[WARN] Cannot save: No point cloud data")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pcd_{timestamp}.ply"
    
    try:
        o3d.io.write_point_cloud(filename, pcd)
        num_points = len(pcd.points)
        print(f"[OK] Saved point cloud: {filename} ({num_points} points)")
    except Exception as e:
        print(f"[ERROR] Error saving point cloud: {e}")


# ============================================================================
# Generate and Save Mesh
# ============================================================================

def generate_and_save_mesh(pcd):
    """
    Generate mesh from point cloud using Poisson reconstruction.
    Note: This may freeze the display briefly while processing.
    """
    if pcd is None or not pcd.has_points():
        print("[WARN] Cannot generate mesh: No point cloud data")
        return
    
    print("[INFO] Generating mesh (this may take a few seconds)...")
    start_time = time.time()
    
    try:
        # Create a copy to avoid modifying original
        pcd_mesh = o3d.geometry.PointCloud(pcd)
        
        # Estimate normals
        pcd_mesh.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(
                radius=0.01, max_nn=30
            )
        )
        
        # Orient normals consistently
        pcd_mesh.orient_normals_consistent_tangent_plane(k=15)
        
        # Poisson surface reconstruction
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd_mesh, depth=POISSON_DEPTH
        )
        
        # Crop mesh to bounding box of original point cloud
        bbox = pcd.get_axis_aligned_bounding_box()
        mesh = mesh.crop(bbox)
        
        # Save mesh
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mesh_{timestamp}.{MESH_FORMAT}"
        
        if MESH_FORMAT == "ply":
            o3d.io.write_triangle_mesh(filename, mesh)
        elif MESH_FORMAT == "obj":
            o3d.io.write_triangle_mesh(filename, mesh, write_vertex_colors=True)
        
        elapsed = time.time() - start_time
        num_vertices = len(mesh.vertices)
        num_triangles = len(mesh.triangles)
        
        print(f"[OK] Mesh saved: {filename}")
        print(f"  Vertices: {num_vertices}, Triangles: {num_triangles}")
        print(f"  Generation time: {elapsed:.2f}s")
        
    except Exception as e:
        print(f"[ERROR] Error generating mesh: {e}")


# ============================================================================
# Keyboard Callbacks
# ============================================================================

def key_callback_quit(vis):
    """Callback for Q key - quit application."""
    global g_quit_flag
    g_quit_flag = True
    print("Quit requested...")
    return False

def key_callback_save(vis):
    """Callback for S key - save point cloud."""
    global g_current_pcd
    save_pointcloud(g_current_pcd)
    return False

def key_callback_mesh(vis):
    """Callback for M key - generate and save mesh."""
    global g_current_pcd
    generate_and_save_mesh(g_current_pcd)
    return False


# ============================================================================
# Main Application
# ============================================================================

def main():
    global g_quit_flag, g_current_pcd
    
    print("\n" + "="*80)
    print("Intel RealSense L515 - Live Arm Point Cloud Capture")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Stream: {COLOR_WIDTH}×{COLOR_HEIGHT} @ {COLOR_FPS} fps")
    print(f"  Depth range: {Z_MIN:.2f}m to {Z_MAX:.2f}m")
    print(f"  ROI enabled: {USE_ROI}")
    print(f"  Voxel size: {VOXEL_SIZE*1000:.1f}mm")
    print(f"\nKeyboard Controls:")
    print(f"  Q / ESC  : Quit")
    print(f"  S        : Save point cloud (.ply)")
    print(f"  M        : Generate mesh (.{MESH_FORMAT})")
    print("="*80 + "\n")
    
    # Setup RealSense
    try:
        pipeline, align, pc, spatial_filter, temporal_filter, hole_filter = \
            setup_realsense_pipeline()
    except Exception:
        print("\n[ERROR] Failed to initialize RealSense. Exiting.")
        return
    
    # Wait for first valid frames
    print("\nWaiting for camera to stabilize...")
    for _ in range(30):  # Skip first 30 frames
        pipeline.wait_for_frames()
    
    # Get first point cloud for visualization setup
    print("Capturing initial point cloud...")
    pcd = None
    max_attempts = 100
    for attempt in range(max_attempts):
        frames = pipeline.wait_for_frames()
        pcd = process_frames_to_pointcloud(frames, align, pc, 
                                          spatial_filter, temporal_filter, hole_filter)
        if pcd is not None and pcd.has_points():
            break
    
    if pcd is None or not pcd.has_points():
        print("[ERROR] Could not capture initial point cloud. Check depth range and ROI settings.")
        pipeline.stop()
        return
    
    print(f"[OK] Initial point cloud captured ({len(pcd.points)} points)")
    
    # Setup Open3D visualizer
    print("Initializing Open3D visualizer...")
    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window(window_name="L515 Live Arm Point Cloud", width=1280, height=720)
    
    # Register key callbacks
    vis.register_key_callback(ord('Q'), key_callback_quit)
    vis.register_key_callback(256, key_callback_quit)  # ESC key
    vis.register_key_callback(ord('S'), key_callback_save)
    vis.register_key_callback(ord('M'), key_callback_mesh)
    
    # Add initial geometry
    vis.add_geometry(pcd)
    g_current_pcd = pcd
    
    # Configure view
    view_ctrl = vis.get_view_control()
    render_opt = vis.get_render_option()
    render_opt.point_size = 2.0
    render_opt.background_color = np.array([0.1, 0.1, 0.1])
    
    print("[OK] Visualizer ready")
    print("\n[START] Starting live capture... (Press Q or ESC to quit)\n")
    
    # FPS tracking
    frame_count = 0
    fps_timer = time.time()
    
    # Main loop
    try:
        while not g_quit_flag:
            # Get frames
            frames = pipeline.wait_for_frames(timeout_ms=5000)
            if not frames:
                print("[WARN] No frames received")
                continue
            
            # Process to point cloud
            new_pcd = process_frames_to_pointcloud(frames, align, pc,
                                                   spatial_filter, temporal_filter, hole_filter)
            
            if new_pcd is None or not new_pcd.has_points():
                # Skip this frame but don't crash
                continue
            
            # Update visualization
            g_current_pcd = new_pcd
            pcd.points = new_pcd.points
            pcd.colors = new_pcd.colors
            vis.update_geometry(pcd)
            
            # Non-blocking visualization update
            if not vis.poll_events():
                break
            vis.update_renderer()
            
            # FPS calculation
            frame_count += 1
            elapsed = time.time() - fps_timer
            if elapsed >= FPS_UPDATE_INTERVAL:
                fps = frame_count / elapsed
                num_points = len(pcd.points)
                print(f"FPS: {fps:.1f} | Points: {num_points:,}")
                frame_count = 0
                fps_timer = time.time()
    
    except KeyboardInterrupt:
        print("\n\n[WARN] Interrupted by user (Ctrl+C)")
    
    except Exception as e:
        print(f"\n[ERROR] Error during capture: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\nShutting down...")
        vis.destroy_window()
        pipeline.stop()
        print("[OK] RealSense pipeline stopped")
        print("[OK] Visualizer closed")
        print("\n" + "="*80)
        print("Session complete. Goodbye!")
        print("="*80 + "\n")


if __name__ == "__main__":
    main()

