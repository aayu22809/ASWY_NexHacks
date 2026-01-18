#!/usr/bin/env python3
"""Simplest possible WebSocket test."""
import sys
from websocket import create_connection

try:
    print("Attempting connection...")
    ws = create_connection("ws://localhost:5000/ws/stream", timeout=3)
    print("✅ CONNECTED!")
    
    print("Receiving first message...")
    msg = ws.recv()
    print(f"✅ RECEIVED: {len(msg)} bytes")
    print(f"First 100 chars: {msg[:100]}")
    
    ws.close()
    print("✅ SUCCESS!")
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

