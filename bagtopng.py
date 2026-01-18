import os
import argparse
import numpy as np
import cv2
import pyrealsense2 as rs


def safe_mkdir(p: str):
    os.makedirs(p, exist_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bag", required=True, help="Path to .bag file")
    ap.add_argument("--out_dir", default=os.path.expanduser("~/Documents"),
                    help="Where to write PNGs (default: ~/Documents)")
    ap.add_argument("--prefix", default="hand_export",
                    help="Filename prefix (default: hand_export)")
    ap.add_argument("--stride", type=int, default=1,
                    help="Save every Nth frame (default: 1 = save all)")
    ap.add_argument("--max_frames", type=int, default=0,
                    help="0 = no limit")
    ap.add_argument("--depth_unit", choices=["raw", "mm"], default="raw",
                    help=("raw = save uint16 depth in sensor units (recommended), "
                          "mm = save uint16 depth in millimeters"))
    args = ap.parse_args()

    out_dir = os.path.expanduser(args.out_dir)
    safe_mkdir(out_dir)

    # Expand bag file path
    bag_path = os.path.expanduser(args.bag)
    if not os.path.exists(bag_path):
        raise FileNotFoundError(f"Bag file not found: {bag_path}")
    
    # Setup RealSense playback pipeline
    # Create context explicitly to avoid config file issues
    try:
        ctx = rs.context()
    except Exception as e:
        print(f"Warning: Context creation issue: {e}")
        ctx = None
    
    pipeline = rs.pipeline(ctx) if ctx else rs.pipeline()
    config = rs.config()
    
    # Enable device from file - use absolute path
    config.enable_device_from_file(bag_path, repeat_playback=False)

    try:
        profile = pipeline.start(config)
    except RuntimeError as e:
        error_msg = str(e)
        if "config-file" in error_msg or "context" in error_msg.lower():
            print(f"\nError: RealSense SDK configuration issue: {error_msg}")
            print("\nTroubleshooting steps:")
            print("1. Try deleting ~/.realsense-config.json and run again")
            print("2. Check if the .bag file is valid: realsense-viewer can open it")
            print("3. Verify pyrealsense2 installation: pip3 show pyrealsense2")
            raise
        else:
            raise

    # Make playback offline / non-real-time
    dev = profile.get_device()
    playback = dev.as_playback()
    playback.set_real_time(False)

    # Alignment: make depth match color resolution
    align = rs.align(rs.stream.color)

    # Depth scale: sensor units -> meters
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale_m_per_unit = depth_sensor.get_depth_scale()

    saved = 0
    frame_idx = 0

    try:
        while True:
            frames = pipeline.wait_for_frames()
            frames = align.process(frames)

            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            if not depth_frame or not color_frame:
                continue

            if frame_idx % args.stride != 0:
                frame_idx += 1
                continue

            # Timestamp (milliseconds -> seconds float)
            # Using the FRAME timestamp is nice because it becomes the number your other script parses.
            ts_ms = color_frame.get_timestamp()
            ts_s = ts_ms / 1000.0

            # Color: RealSense gives RGB; OpenCV typically uses BGR
            color = np.asanyarray(color_frame.get_data())  # HxWx3, uint8, RGB
            color_bgr = cv2.cvtColor(color, cv2.COLOR_RGB2BGR)

            # Depth: uint16 in sensor units
            depth_raw = np.asanyarray(depth_frame.get_data()).astype(np.uint16)

            if args.depth_unit == "mm":
                # Convert sensor units -> meters -> millimeters
                depth_m = depth_raw.astype(np.float32) * float(depth_scale_m_per_unit)
                depth_mm = np.round(depth_m * 1000.0).astype(np.uint16)
                depth_to_save = depth_mm
            else:
                # Save raw sensor units (most consistent)
                depth_to_save = depth_raw

            color_path = os.path.join(out_dir, f"{args.prefix}_Color_{ts_s:.6f}.png")
            depth_path = os.path.join(out_dir, f"{args.prefix}_Depth_{ts_s:.6f}.png")

            cv2.imwrite(color_path, color_bgr)
            cv2.imwrite(depth_path, depth_to_save)

            saved += 1
            frame_idx += 1

            if args.max_frames > 0 and saved >= args.max_frames:
                break

    except RuntimeError:
        # End-of-file when playback finishes
        pass
    finally:
        pipeline.stop()

    # Write a tiny note about depth scale (useful later)
    meta_path = os.path.join(out_dir, f"{args.prefix}_meta.txt")
    with open(meta_path, "w") as f:
        f.write(f"depth_scale_m_per_unit={depth_scale_m_per_unit}\n")
        f.write(f"depth_saved_as={args.depth_unit}\n")
        f.write("depth_aligned_to_color=1\n")

    print(f"Done. Saved {saved} frame pairs to: {out_dir}")
    print(f"Wrote metadata: {meta_path}")
    print("Example files:")
    print(f"  {args.prefix}_Color_<timestamp>.png")
    print(f"  {args.prefix}_Depth_<timestamp>.png")


if __name__ == "__main__":
    main()
