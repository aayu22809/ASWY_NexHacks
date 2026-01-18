# Cold Plasma Robot Arm - Smart Wound Healing System

**NexHacks 2026 Submission**

An autonomous robotic system for cold plasma wound therapy, featuring real-time 3D scanning, thermal safety monitoring, and AI-driven path planning.

## 🚀 Instant Demo

We've created a single script to launch the entire system (Backend API + Frontend Dashboard).

**Prerequisites:**
- Python 3.8+
- Node.js 18+

**Run the Demo:**

```bash
./demo.sh
```

This will:
1. Set up the Python environment and install dependencies.
2. Install frontend packages.
3. Launch the FastAPI backend (Port 8000).
4. Launch the React Dashboard (Port 5173).
5. Open your browser automatically.

---

## 🎯 What to Look For

Once the dashboard opens:

1.  **3D Visualization**:
    *   Click **"Load Demo Data"** to load a sample scan.
    *   Or upload a `.ply` file to see the 3D wound model.
    *   Upload a Toolpath JSON (from `gcodegen/results_*.json`) to see the generated treatment path.

2.  **Live Sensor Data**:
    *   **Thermal Camera**: Shows real-time heatmap (32x24 grid) from the MLX90640.
    *   **Safety Status**: automatically switches to "STOP" if temperature > 40°C or if an obstacle is detected.

3.  **Path Planning**:
    *   The system calculates optimal raster paths for plasma treatment, maintaining constant standoff distance on curved surfaces.
    *   Blue lines = Active treatment.
    *   Red dashed lines = Rapid movements.

---

## 🛠️ System Architecture

*   **Hardware**: Jetson Orin Nano / Raspberry Pi 5, Intel RealSense D435, MLX90640 Thermal Camera.
*   **Backend**: Python FastAPI, NumPy, SciPy (Path Planning), Open3D.
*   **Frontend**: React, TypeScript, Tailwind CSS, Three.js (React Three Fiber).
*   **Communication**: WebSockets for real-time sensor streaming.

---

## 📂 Project Structure

*   `backend/`: FastAPI server and sensor drivers.
*   `gcodegen/`: Core path planning and G-code generation logic.
*   `plasma-path-planner/`: Modern React frontend dashboard.
*   `tests/`: Hardware validation scripts.

---

## ❓ Troubleshooting

*   **Port Conflicts**: Ensure ports 8000 and 5173 are free.
*   **Missing Dependencies**: If the script fails, try running `pip install -r backend/requirements.txt` and `npm install` in the `plasma-path-planner` directory manually.
*   **Sensor Errors**: The system will run in "Simulation Mode" if physical sensors are not detected.
