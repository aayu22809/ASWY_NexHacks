# Run RealSense Tests

## Quick Test (Simple)
```bash
cd /home/sam/ASWY_NexHacks-main
python3 test_realsense.py
```

## Comprehensive Test (Detailed)
```bash
cd /home/sam/ASWY_NexHacks-main
python3 comprehensive_test.py
```

## What the Tests Check:

1. ✓ **pyrealsense2 import** - Verifies library is installed
2. ✓ **Context creation** - Tests basic API
3. ✓ **Device enumeration** - Checks if camera is detected
4. ✓ **Pipeline creation** - Tests stream setup
5. ✓ **Stream configuration** - Tests depth/color streams
6. ✓ **Frame capture** - Tests actual camera operation

## Expected Results:

### If Camera is Connected:
```
✓✓✓ ALL TESTS PASSED - REAL SENSE IS FULLY WORKING! ✓✓✓
```

### If Camera Not Connected:
```
✓ pyrealsense2 library: WORKING
⚠ Camera detection: NO CAMERA FOUND
Status: LIBRARY READY (connect camera to use)
```

## Next Steps:

1. **If all tests pass**: Run the visualizer
   ```bash
   python3 live_arm_pointcloud_jetson.py
   ```

2. **If camera not detected**:
   - Connect RealSense to USB 3.0 port
   - Run: `sudo ./finish_realsense_setup.sh`
   - Log out and log back in
   - Run tests again
