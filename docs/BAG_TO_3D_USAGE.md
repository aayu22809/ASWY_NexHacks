# Converting .bag Files to 3D Models

This guide explains how to convert a RealSense .bag file into a 3D mesh model.

## Quick Start

The easiest way is to use the unified script:

```bash
python3 bag_to_3d_model.py --bag your_recording.bag
```

This will:
1. Extract color and depth frames from the .bag file
2. Reconstruct a 3D mesh using TSDF volume integration
3. Save the mesh as `<bag_name>_mesh.ply` in the same directory as the .bag file
4. Clean up temporary PNG files (unless `--keep_frames` is used)

## Detailed Usage

### Unified Script (`bag_to_3d_model.py`)

**Basic usage:**
```bash
python3 bag_to_3d_model.py --bag recording.bag
```

**With custom output:**
```bash
python3 bag_to_3d_model.py --bag recording.bag --out_dir ./output --mesh_name my_model.ply
```

**Process every 5th frame, max 200 frames:**
```bash
python3 bag_to_3d_model.py --bag recording.bag --stride 5 --max_frames 200
```

**Keep extracted frames for inspection:**
```bash
python3 bag_to_3d_model.py --bag recording.bag --keep_frames
```

**Full options:**
```bash
python3 bag_to_3d_model.py \
    --bag recording.bag \
    --out_dir ./output \
    --mesh_name model.ply \
    --prefix my_export \
    --stride 1 \
    --max_frames 0 \
    --depth_unit raw \
    --voxel_length 0.003 \
    --sdf_trunc 0.02 \
    --depth_trunc 1.0 \
    --keep_frames
```

### Two-Step Process

You can also run the steps separately:

#### Step 1: Extract frames (`bagtopng.py`)

```bash
python3 bagtopng.py --bag recording.bag --out_dir ./frames --prefix my_export
```

Options:
- `--bag`: Path to .bag file (required)
- `--out_dir`: Output directory (default: ~/Documents)
- `--prefix`: Filename prefix (default: hand_export)
- `--stride`: Save every Nth frame (default: 1 = all frames)
- `--max_frames`: Maximum frames to extract (default: 0 = no limit)
- `--depth_unit`: "raw" (sensor units) or "mm" (millimeters), default: "raw"

#### Step 2: Reconstruct mesh (`reconstruct_tsdf.py`)

```bash
python3 reconstruct_tsdf.py --data_dir ./frames --prefix my_export --out_mesh model.ply
```

Options:
- `--data_dir`: Directory containing PNG files (default: ~/Documents)
- `--prefix`: Filename prefix (default: hand_export)
- `--out_mesh`: Output mesh file (default: <data_dir>/<prefix>_mesh.ply)
- `--voxel_length`: TSDF voxel size in meters (default: 0.003)
- `--sdf_trunc`: TSDF truncation distance in meters (default: 0.02)
- `--depth_trunc`: Maximum depth in meters (default: 1.0)

## How It Works

1. **Frame Extraction** (`bagtopng.py`):
   - Reads the .bag file using pyrealsense2
   - Aligns depth frames to color resolution
   - Saves color and depth frames as PNG images
   - Creates a metadata file with depth scale information

2. **Mesh Reconstruction** (`reconstruct_tsdf.py`):
   - Finds matching color/depth pairs by timestamp
   - Creates RGBD images using Open3D
   - Performs RGBD odometry to track camera motion
   - Integrates frames into a TSDF volume
   - Extracts and cleans the triangle mesh
   - Saves as PLY file

## Parameters Explained

- **voxel_length** (0.003m = 3mm): Smaller = higher detail but slower and more memory
- **sdf_trunc** (0.02m = 2cm): Distance threshold for TSDF integration
- **depth_trunc** (1.0m): Maximum depth to consider (filters far objects)
- **stride**: Process every Nth frame (useful for long recordings)
- **depth_unit**: "raw" preserves original sensor units (recommended), "mm" converts to millimeters

## Output Files

- `<prefix>_Color_<timestamp>.png`: Color frames
- `<prefix>_Depth_<timestamp>.png`: Depth frames  
- `<prefix>_meta.txt`: Metadata with depth scale
- `<prefix>_mesh.ply`: Final 3D mesh (can be opened in MeshLab, Blender, etc.)

## Troubleshooting

**"Could not find both color and depth frames"**
- Make sure the .bag file contains both color and depth streams
- Check that frames were extracted successfully in step 1

**Mesh looks distorted or wrong scale**
- The script automatically reads depth scale from metadata
- If issues persist, try adjusting `--depth_trunc` or `--voxel_length`

**Out of memory errors**
- Reduce `--max_frames` or increase `--stride` to process fewer frames
- Increase `--voxel_length` to use less memory (lower resolution)

**Poor mesh quality**
- Try smaller `--voxel_length` (e.g., 0.001) for higher detail
- Ensure good camera motion during recording (not too fast, not too slow)
- Check that depth frames are valid (not all zeros or max values)

## Viewing the Mesh

You can view the PLY file with:
- **MeshLab**: `meshlab model.ply`
- **Blender**: Import PLY file
- **Open3D**: `python3 -c "import open3d as o3d; o3d.visualization.draw_geometries([o3d.io.read_triangle_mesh('model.ply')])"`
