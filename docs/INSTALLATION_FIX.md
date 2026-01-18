# Installation Fix for "externally-managed-environment" Error

If you get this error when trying to install Python packages:

```
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.
```

## Solution

Newer Raspberry Pi OS versions (Bookworm and later) protect the system Python installation using PEP 668. Here's how to handle it:

### For Flask HTTP Server Dependencies (RECOMMENDED)

Use system packages instead of pip:

```bash
sudo apt-get install python3-flask python3-flask-cors python3-flask-sockets
```

✅ This is the best solution - no environment conflicts!

### For MLX90640 Sensor Libraries

These aren't available as system packages, so you have 3 options:

#### Option 1: Use --break-system-packages (Quick & Easy)

```bash
pip3 install --break-system-packages adafruit-circuitpython-mlx90640 adafruit-blinka numpy
```

⚠️ This works but bypasses the safety mechanism.

#### Option 2: Use Virtual Environment (RECOMMENDED for Development)

```bash
# Create virtual environment
cd /home/aayushya/ASWY_NexHacks
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install packages
pip install adafruit-circuitpython-mlx90640 adafruit-blinka numpy

# Run the script
python3 tests/test_mlx90640_http.py

# When done, deactivate
deactivate
```

✅ Clean, isolated, no system conflicts!

#### Option 3: Install to User Directory

```bash
pip3 install --user adafruit-circuitpython-mlx90640 adafruit-blinka numpy
```

✅ Safe, but packages only available for your user.

## Quick Install Script

Run this to set everything up:

```bash
#!/bin/bash
cd /home/aayushya/ASWY_NexHacks

# Install Flask dependencies via apt (system-wide)
echo "Installing Flask dependencies..."
sudo apt-get update
sudo apt-get install -y python3-flask python3-flask-cors python3-flask-sockets

# Install MLX90640 dependencies via pip (user directory)
echo "Installing MLX90640 sensor libraries..."
pip3 install --user adafruit-circuitpython-mlx90640 adafruit-blinka numpy

echo "✅ Installation complete!"
echo ""
echo "Test it:"
echo "  python3 tests/test_mlx90640_http.py"
```

Save as `install_deps.sh`, make executable, and run:

```bash
chmod +x install_deps.sh
./install_deps.sh
```

## Why This Happens

- **Raspberry Pi OS Bookworm** (2023+) uses PEP 668 to prevent pip from breaking system Python packages
- System packages (via `apt`) are managed by Debian package manager
- User packages (via `pip --user` or venv) don't interfere with system

## Best Practice

1. **System tools** (Flask, nginx, etc.) → Use `apt`
2. **Development libraries** (sensor libs, etc.) → Use virtual environment
3. **Quick testing** → Use `--user` flag
4. **Last resort** → Use `--break-system-packages` (but be careful!)

## Already Installed Packages

The following were successfully installed via `apt`:
- ✅ python3-flask
- ✅ python3-flask-cors
- ✅ python3-flask-sockets
- ✅ python3-gevent
- ✅ python3-gevent-websocket

You only need to install the MLX90640 sensor libraries now!


