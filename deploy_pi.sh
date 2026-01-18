#!/bin/bash
# Update system
sudo apt update && sudo apt install -y python3-venv libgl1-mesa-glx i2c-tools libatlas-base-dev

# Navigate to project
cd ~/ASWY_NexHacks

# Setup Python environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install dependencies (ignoring errors for demo)
pip install -r backend/requirements.txt || echo "Warning: Some requirements failed install"

# Start server
echo "Starting backend server..."
uvicorn backend.api:app --host 0.0.0.0 --port 8000

