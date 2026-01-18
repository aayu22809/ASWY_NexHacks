#!/usr/bin/env python3
"""Debug WebSocket connection - shows raw data received."""

import sys
from websocket import create_connection

WS_URL = "ws://localhost:5000/ws/stream"

print(f"Connecting to: {WS_URL}")
print("-" * 60)

try:
    ws = create_connection(WS_URL, timeout=5)
    print("✅ Connected successfully!")
    print("Waiting for data...\n")
    
    # Receive multiple messages
    for i in range(3):
        print(f"Message {i+1}:")
        result = ws.recv()
        print(f"  Type: {type(result)}")
        print(f"  Length: {len(result) if result else 0}")
        print(f"  Raw (first 200 chars): {repr(result[:200] if result else result)}")
        print()
        
    ws.close()
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

