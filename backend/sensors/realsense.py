"""RealSense camera wrapper for single capture mode."""

import asyncio
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import open3d as o3d
import pyrealsense2 as rs

from backend.config import (
    REALSENSE_CAPTURE_DIR,
    REALSENSE_DEPTH_MIN,
    REALSENSE_DEPTH_MAX,
)


class RealSenseCapture:
    """Wrapper for RealSense single capture functionality."""
    
    def __init__(self):
        """Initialize RealSense pipeline."""
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        
        # Enable streams
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        
        # Start pipeline
        try:
            self.profile = self.pipeline.start(self.config)
            print("[OK] RealSense pipeline started")
        except Exception as e:
            raise RuntimeError(f"Failed to start RealSense pipeline: {e}")
        
        # Create align object
        self.align = rs.align(rs.stream.color)
        
        # Create point cloud object
        self.pc = rs.pointcloud()
        
        # Setup filters
        self.spatial_filter = rs.spatial_filter()
        self.spatial_filter.set_option(rs.option.filter_magnitude, 2)
        self.spatial_filter.set_option(rs.option.filter_smooth_alpha, 0.5)
        
        self.temporal_filter = rs.temporal_filter()
        self.temporal_filter.set_option(rs.option.filter_smooth_alpha, 0.4)
        self.temporal_filter.set_option(rs.option.filter_smooth_delta, 20)
        
        self.hole_filter = rs.hole_filling_filter(1)
    
    async def single_capture(self) -> tuple[str, int]:
        """
        Capture a single frame and save as PLY file.
        
        Returns:
            Tuple of (ply_file_path, num_points)
        """
        # Wait for frames to stabilize
        for _ in range(30):
            self.pipeline.wait_for_frames()
        
        # Capture frame
        frames = self.pipeline.wait_for_frames()
        
        # Align depth to color
        aligned_frames = self.align.process(frames)
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        
        if not depth_frame or not color_frame:
            raise RuntimeError("Failed to capture valid frames")
        
        # Apply filters
        depth_frame = self.spatial_filter.process(depth_frame)
        depth_frame = self.temporal_filter.process(depth_frame)
        depth_frame = self.hole_filter.process(depth_frame)
        
        # Generate point cloud
        self.pc.map_to(color_frame)
        points = self.pc.calculate(depth_frame)
        
        # Extract vertices and texture coordinates
        vertices = np.asanyarray(points.get_vertices()).view(np.float32).reshape(-1, 3)
        tex_coords = np.asanyarray(points.get_texture_coordinates()).view(np.float32).reshape(-1, 2)
        
        # Get color data
        color_image = np.asanyarray(color_frame.get_data())
        width = color_frame.get_width()
        height = color_frame.get_height()
        
        # Map texture coordinates to colors
        u = (tex_coords[:, 0] * (width - 1)).astype(np.int32)
        v = (tex_coords[:, 1] * (height - 1)).astype(np.int32)
        u = np.clip(u, 0, width - 1)
        v = np.clip(v, 0, height - 1)
        
        # Sample colors (BGR -> RGB) and normalize
        colors = color_image[v, u, :].astype(np.float32) / 255.0
        colors = colors[:, ::-1]  # BGR to RGB
        
        # Filter points
        valid_mask = np.isfinite(vertices).all(axis=1)
        depth_mask = (vertices[:, 2] >= REALSENSE_DEPTH_MIN) & (vertices[:, 2] <= REALSENSE_DEPTH_MAX)
        
        # ROI filter (center 60%)
        roi_mask = (
            (tex_coords[:, 0] >= 0.2) & (tex_coords[:, 0] <= 0.8) &
            (tex_coords[:, 1] >= 0.2) & (tex_coords[:, 1] <= 0.8)
        )
        
        final_mask = valid_mask & depth_mask & roi_mask
        filtered_vertices = vertices[final_mask]
        filtered_colors = colors[final_mask]
        
        if len(filtered_vertices) == 0:
            raise RuntimeError("No valid points captured")
        
        # Create Open3D point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(filtered_vertices)
        pcd.colors = o3d.utility.Vector3dVector(filtered_colors)
        
        # Downsample
        pcd = pcd.voxel_down_sample(voxel_size=0.003)
        
        # Save PLY file
        Path(REALSENSE_CAPTURE_DIR).mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ply_path = os.path.join(REALSENSE_CAPTURE_DIR, f"capture_{timestamp}.ply")
        
        o3d.io.write_point_cloud(ply_path, pcd)
        
        num_points = len(pcd.points)
        print(f"[OK] Captured {num_points} points, saved to {ply_path}")
        
        return ply_path, num_points
    
    def close(self):
        """Stop pipeline."""
        self.pipeline.stop()
