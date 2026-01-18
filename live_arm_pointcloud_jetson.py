#!/usr/bin/env python3
"""
================================================================================
Intel RealSense L515 - Live Point Cloud Capture (Jetson-Optimized)
================================================================================

DESCRIPTION:
    Jetson-optimized version of the RealSense point cloud visualizer.
    Uses OpenCV for visualization instead of Open3D for better ARM64 compatibility.
    Falls back to Open3D if available.

REQUIREMENTS:
    - pyrealsense2 (built from source for Jetson)
    - numpy
    - opencv-python (usually pre-installed on Jetson)
    - open3d (optional, for 3D visualization)

CONTROLS:
    Q / ESC  : Quit application
    S        : Save current point cloud to .ply file
    D        : Toggle depth colormap
    +/-      : Adjust depth range

================================================================================
"""

import numpy as np
import time
from datetime import datetime
import sys
import os

# Setup library paths
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib:' + os.environ.get('LD_LIBRARY_PATH', '')
sys.path.insert(0, '/usr/lib/python3.8/site-packages')

# Check for pyrealsense2
try:
    import pyrealsense2 as rs
    print("[OK] pyrealsense2 imported successfully")
except ImportError as e:
    print("[ERROR] pyrealsense2 not found!")
    print("Please run: ./setup_jetson_realsense.sh")
    print(f"Details: {e}")
    sys.exit(1)

# Check for OpenCV
try:
    import cv2
    print(f"[OK] OpenCV {cv2.__version__} imported")
    HAS_OPENCV = True
except ImportError:
    print("[WARN] OpenCV not found - installing...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "opencv-python"])
    import cv2
    HAS_OPENCV = True

# Check for Open3D (optional)
try:
    import open3d as o3d
    print(f"[OK] Open3D {o3d.__version__} imported")
    HAS_OPEN3D = True
except ImportError:
    print("[INFO] Open3D not available - using OpenCV visualization only")
    HAS_OPEN3D = False


# ============================================================================
# CONFIGURATION
# ============================================================================

# Stream Configuration (optimized for Jetson)
COLOR_WIDTH = 640
COLOR_HEIGHT = 480
COLOR_FPS = 30
DEPTH_WIDTH = 640
DEPTH_HEIGHT = 480
DEPTH_FPS = 30

# Depth Range (meters)
Z_MIN = 0.20  # Minimum depth (20 cm)
Z_MAX = 0.90  # Maximum depth (90 cm)

# Visualization
DEPTH_COLORMAP = cv2.COLORMAP_JET
WINDOW_NAME = "RealSense L515 - Jetson"

# Point Cloud Downsampling
VOXEL_SIZE = 0.005  # 5mm voxel grid


# ============================================================================
# RealSense Pipeline Setup
# ============================================================================

def setup_realsense():
    """Initialize RealSense pipeline with L515 configuration."""
    print("\n[INFO] Initializing Intel RealSense...")
    
    # Check for connected devices first
    ctx = rs.context()
    devices = ctx.query_devices()
    
    if len(devices) == 0:
        print("\n[ERROR] No RealSense cameras detected!")
        print("\nTroubleshooting:")
        print("  1. Ensure camera is connected to USB 3.0 port (blue)")
        print("  2. Try: sudo udevadm control --reload-rules && sudo udevadm trigger")
        print("  3. Unplug and replug the camera")
        print("  4. Check: ls /dev/video*")
        print("  5. Run: realsense-viewer (if installed)")
        return None, None, None
    
    # Print device info
    for dev in devices:
        print(f"[OK] Found: {dev.get_info(rs.camera_info.name)}")
        print(f"     Serial: {dev.get_info(rs.camera_info.serial_number)}")
        print(f"     Firmware: {dev.get_info(rs.camera_info.firmware_version)}")
    
    # Create pipeline
    pipeline = rs.pipeline()
    config = rs.config()
    
    # Enable streams
    config.enable_stream(rs.stream.color, COLOR_WIDTH, COLOR_HEIGHT, 
                        rs.format.bgr8, COLOR_FPS)
    config.enable_stream(rs.stream.depth, DEPTH_WIDTH, DEPTH_HEIGHT, 
                        rs.format.z16, DEPTH_FPS)
    
    try:
        profile = pipeline.start(config)
        print("[OK] Pipeline started")
        
        # Get depth sensor and configure
        depth_sensor = profile.get_device().first_depth_sensor()
        
        # Set visual preset for L515 (if available)
        if depth_sensor.supports(rs.option.visual_preset):
            # 3 = Short Range, good for arm tracking
            depth_sensor.set_option(rs.option.visual_preset, 3)
            print("[OK] Set L515 visual preset to Short Range")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to start pipeline: {e}")
        return None, None, None
    
    # Create align object
    align = rs.align(rs.stream.color)
    
    # Setup filters
    spatial = rs.spatial_filter()
    spatial.set_option(rs.option.filter_magnitude, 2)
    spatial.set_option(rs.option.filter_smooth_alpha, 0.5)
    
    temporal = rs.temporal_filter()
    temporal.set_option(rs.option.filter_smooth_alpha, 0.4)
    
    hole_filling = rs.hole_filling_filter()
    
    filters = (spatial, temporal, hole_filling)
    
    return pipeline, align, filters


def apply_filters(depth_frame, filters):
    """Apply depth filters for cleaner output."""
    spatial, temporal, hole_filling = filters
    
    depth_frame = spatial.process(depth_frame)
    depth_frame = temporal.process(depth_frame)
    depth_frame = hole_filling.process(depth_frame)
    
    return depth_frame


# ============================================================================
# Point Cloud Generation
# ============================================================================

def create_pointcloud(depth_frame, color_frame, pc):
    """Generate colored point cloud from depth and color frames."""
    pc.map_to(color_frame)
    points = pc.calculate(depth_frame)
    
    # Get vertices
    vertices = np.asanyarray(points.get_vertices()).view(np.float32).reshape(-1, 3)
    
    # Get texture coordinates
    tex_coords = np.asanyarray(points.get_texture_coordinates()).view(np.float32).reshape(-1, 2)
    
    # Get color image
    color_image = np.asanyarray(color_frame.get_data())
    h, w = color_image.shape[:2]
    
    # Map texture coords to pixel coords
    u = np.clip((tex_coords[:, 0] * (w - 1)).astype(np.int32), 0, w - 1)
    v = np.clip((tex_coords[:, 1] * (h - 1)).astype(np.int32), 0, h - 1)
    
    # Sample colors (BGR -> RGB, normalize)
    colors = color_image[v, u, ::-1].astype(np.float32) / 255.0
    
    # Filter by depth range
    valid = (vertices[:, 2] >= Z_MIN) & (vertices[:, 2] <= Z_MAX)
    valid &= np.isfinite(vertices).all(axis=1)
    
    return vertices[valid], colors[valid]


def save_pointcloud_ply(vertices, colors, filename=None):
    """Save point cloud to PLY file."""
    if len(vertices) == 0:
        print("[WARN] No points to save")
        return
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pointcloud_{timestamp}.ply"
    
    # Convert colors to 0-255 range
    colors_255 = (colors * 255).astype(np.uint8)
    
    # Write PLY file
    with open(filename, 'w') as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {len(vertices)}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("end_header\n")
        
        for v, c in zip(vertices, colors_255):
            f.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f} {c[0]} {c[1]} {c[2]}\n")
    
    print(f"[OK] Saved: {filename} ({len(vertices)} points)")


# ============================================================================
# OpenCV Visualization
# ============================================================================

def run_opencv_visualizer(pipeline, align, filters):
    """Run visualization using OpenCV (2D depth + color views)."""
    global Z_MIN, Z_MAX, DEPTH_COLORMAP
    
    print("\n[INFO] Starting OpenCV visualization...")
    print("Controls:")
    print("  Q/ESC : Quit")
    print("  S     : Save point cloud")
    print("  D     : Toggle depth colormap")
    print("  +/-   : Adjust depth range")
    print("")
    
    pc = rs.pointcloud()
    colormap_idx = 0
    colormaps = [cv2.COLORMAP_JET, cv2.COLORMAP_TURBO, cv2.COLORMAP_VIRIDIS, 
                 cv2.COLORMAP_PLASMA, cv2.COLORMAP_INFERNO]
    
    # FPS tracking
    frame_count = 0
    fps_timer = time.time()
    fps = 0
    
    try:
        while True:
            # Get frames
            frames = pipeline.wait_for_frames(timeout_ms=5000)
            aligned = align.process(frames)
            
            depth_frame = aligned.get_depth_frame()
            color_frame = aligned.get_color_frame()
            
            if not depth_frame or not color_frame:
                continue
            
            # Apply filters
            depth_frame = apply_filters(depth_frame, filters)
            
            # Get numpy arrays
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            
            # Convert depth to meters
            depth_scale = pipeline.get_active_profile().get_device().first_depth_sensor().get_depth_scale()
            depth_meters = depth_image * depth_scale
            
            # Clip to range and normalize for visualization
            depth_clipped = np.clip(depth_meters, Z_MIN, Z_MAX)
            depth_normalized = ((depth_clipped - Z_MIN) / (Z_MAX - Z_MIN) * 255).astype(np.uint8)
            
            # Apply colormap
            depth_colormap = cv2.applyColorMap(depth_normalized, colormaps[colormap_idx])
            
            # Mask out-of-range pixels
            mask = (depth_meters < Z_MIN) | (depth_meters > Z_MAX) | (depth_meters == 0)
            depth_colormap[mask] = [0, 0, 0]
            
            # Create side-by-side display
            display = np.hstack([color_image, depth_colormap])
            
            # Add info overlay
            cv2.putText(display, f"FPS: {fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display, f"Depth: {Z_MIN:.2f}m - {Z_MAX:.2f}m", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display, "Q:Quit  S:Save  D:Colormap  +/-:Range", (10, display.shape[0]-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show
            cv2.imshow(WINDOW_NAME, display)
            
            # FPS calculation
            frame_count += 1
            elapsed = time.time() - fps_timer
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                frame_count = 0
                fps_timer = time.time()
            
            # Handle keyboard
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == 27:  # Q or ESC
                break
            elif key == ord('s'):
                # Save point cloud
                vertices, colors = create_pointcloud(depth_frame, color_frame, pc)
                save_pointcloud_ply(vertices, colors)
            elif key == ord('d'):
                colormap_idx = (colormap_idx + 1) % len(colormaps)
                print(f"[INFO] Colormap: {colormap_idx}")
            elif key == ord('+') or key == ord('='):
                Z_MAX = min(Z_MAX + 0.1, 3.0)
                print(f"[INFO] Depth range: {Z_MIN:.2f}m - {Z_MAX:.2f}m")
            elif key == ord('-'):
                Z_MAX = max(Z_MAX - 0.1, Z_MIN + 0.1)
                print(f"[INFO] Depth range: {Z_MIN:.2f}m - {Z_MAX:.2f}m")
    
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted")
    
    finally:
        cv2.destroyAllWindows()


# ============================================================================
# Open3D Visualization (if available)
# ============================================================================

def run_open3d_visualizer(pipeline, align, filters):
    """Run 3D visualization using Open3D."""
    if not HAS_OPEN3D:
        print("[ERROR] Open3D not available")
        return
    
    print("\n[INFO] Starting Open3D 3D visualization...")
    print("Controls:")
    print("  Q/ESC : Quit")
    print("  S     : Save point cloud")
    print("  M     : Generate mesh")
    print("")
    
    pc = rs.pointcloud()
    
    # Wait for first valid frame
    print("[INFO] Waiting for camera to stabilize...")
    for _ in range(30):
        pipeline.wait_for_frames()
    
    # Get initial point cloud
    frames = pipeline.wait_for_frames()
    aligned = align.process(frames)
    depth_frame = apply_filters(aligned.get_depth_frame(), filters)
    color_frame = aligned.get_color_frame()
    
    vertices, colors = create_pointcloud(depth_frame, color_frame, pc)
    
    if len(vertices) == 0:
        print("[ERROR] No points captured. Check depth range settings.")
        return
    
    # Create Open3D point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(vertices)
    pcd.colors = o3d.utility.Vector3dVector(colors)
    
    if VOXEL_SIZE > 0:
        pcd = pcd.voxel_down_sample(voxel_size=VOXEL_SIZE)
    
    # Setup visualizer
    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window(window_name="RealSense L515 - 3D View", width=1280, height=720)
    
    # Global state for callbacks
    state = {'quit': False, 'pcd': pcd}
    
    def quit_callback(vis):
        state['quit'] = True
        return False
    
    def save_callback(vis):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pointcloud_{timestamp}.ply"
        o3d.io.write_point_cloud(filename, state['pcd'])
        print(f"[OK] Saved: {filename}")
        return False
    
    vis.register_key_callback(ord('Q'), quit_callback)
    vis.register_key_callback(256, quit_callback)  # ESC
    vis.register_key_callback(ord('S'), save_callback)
    
    vis.add_geometry(pcd)
    
    render_opt = vis.get_render_option()
    render_opt.point_size = 2.0
    render_opt.background_color = np.array([0.1, 0.1, 0.1])
    
    # FPS tracking
    frame_count = 0
    fps_timer = time.time()
    
    try:
        while not state['quit']:
            frames = pipeline.wait_for_frames(timeout_ms=5000)
            aligned = align.process(frames)
            
            depth_frame = apply_filters(aligned.get_depth_frame(), filters)
            color_frame = aligned.get_color_frame()
            
            if not depth_frame or not color_frame:
                continue
            
            vertices, colors = create_pointcloud(depth_frame, color_frame, pc)
            
            if len(vertices) == 0:
                continue
            
            # Update point cloud
            new_pcd = o3d.geometry.PointCloud()
            new_pcd.points = o3d.utility.Vector3dVector(vertices)
            new_pcd.colors = o3d.utility.Vector3dVector(colors)
            
            if VOXEL_SIZE > 0:
                new_pcd = new_pcd.voxel_down_sample(voxel_size=VOXEL_SIZE)
            
            state['pcd'] = new_pcd
            pcd.points = new_pcd.points
            pcd.colors = new_pcd.colors
            
            vis.update_geometry(pcd)
            
            if not vis.poll_events():
                break
            vis.update_renderer()
            
            # FPS
            frame_count += 1
            elapsed = time.time() - fps_timer
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                print(f"FPS: {fps:.1f} | Points: {len(pcd.points):,}")
                frame_count = 0
                fps_timer = time.time()
    
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted")
    
    finally:
        vis.destroy_window()


# ============================================================================
# Main
# ============================================================================

def main():
    print("\n" + "=" * 60)
    print("Intel RealSense L515 - Jetson Point Cloud Capture")
    print("=" * 60)
    
    # Setup RealSense
    result = setup_realsense()
    if result[0] is None:
        return 1
    
    pipeline, align, filters = result
    
    print("\n[INFO] Camera ready!")
    print(f"[INFO] Depth range: {Z_MIN:.2f}m - {Z_MAX:.2f}m")
    
    # Choose visualization mode
    if HAS_OPEN3D:
        print("\nVisualization modes available:")
        print("  1. OpenCV (2D depth + color)")
        print("  2. Open3D (3D point cloud)")
        print("")
        
        choice = input("Select mode [1/2, default=1]: ").strip()
        
        if choice == '2':
            run_open3d_visualizer(pipeline, align, filters)
        else:
            run_opencv_visualizer(pipeline, align, filters)
    else:
        print("\n[INFO] Using OpenCV visualization (Open3D not available)")
        run_opencv_visualizer(pipeline, align, filters)
    
    # Cleanup
    print("\n[INFO] Shutting down...")
    pipeline.stop()
    print("[OK] Done!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
