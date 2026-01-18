#!/usr/bin/env python3
"""
Simple WebSocket test client to debug connection issues.
"""

import json
import sys

try:
    from websocket import create_connection
except ImportError:
    print("[ERROR] websocket-client not installed")
    print("Install with: pip3 install --break-system-packages websocket-client")
    sys.exit(1)

# Change this to your Pi's IP if testing from another device
WS_URL = "ws://localhost:5000/ws/stream"

print(f"Connecting to: {WS_URL}")
print("-" * 60)

try:
    ws = create_connection(WS_URL, timeout=5)
    print("✅ Connected successfully!")
    print("Waiting for data...")
    
    # Receive one frame
    result = ws.recv()
    data = json.loads(result)
    
    print("\n📊 Received thermal data:")
    print(f"  Max temp:  {data['max_temp']:.2f}°C")
    print(f"  Min temp:  {data['min_temp']:.2f}°C")
    print(f"  Mean temp: {data['mean_temp']:.2f}°C")
    print(f"  Timestamp: {data['timestamp']}")
    print(f"  Thermal array length: {len(data['thermal'])} values")
    
    print("\n✅ WebSocket is working correctly!")
    ws.close()
    
except ConnectionRefusedError:
    print("❌ Connection refused. Is the server running?")
    print("   Start server: python3 tests/test_mlx90640_http.py")
except TimeoutError:
    print("❌ Connection timed out. Check network/firewall.")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()


