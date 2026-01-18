"""
Embedded HTML template for the unified demo interface.
Simplified industrial UI with 3D viewer, thermal camera, config panel, and event log.
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cold Plasma Treatment System</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --bg-primary: #0a0f14;
            --bg-panel: #111820;
            --bg-elevated: #1a2332;
            --border: #1e2832;
            --text-primary: #e8edf3;
            --text-muted: #6b7a8a;
            --accent: #00d4aa;
            --accent-hover: #00b894;
            --warning: #f59e0b;
            --danger: #ef4444;
            --success: #10b981;
        }
        
        body {
            font-family: 'JetBrains Mono', monospace;
            background: var(--bg-primary);
            color: var(--text-primary);
            overflow-x: hidden;
        }
        
        .header {
            background: var(--bg-panel);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--accent);
        }
        
        .main-container {
            display: grid;
            grid-template-columns: 1fr 400px 350px;
            gap: 1rem;
            padding: 1rem;
            height: calc(100vh - 80px);
        }
        
        .panel {
            background: var(--bg-panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        .panel-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* 3D Viewer Panel */
        #viewer-container {
            flex: 1;
            background: #000;
            border-radius: 4px;
            position: relative;
            min-height: 400px;
        }
        
        /* Thermal Panel */
        .thermal-container {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .heatmap-wrapper {
            position: relative;
            background: #000;
            border-radius: 4px;
            overflow: hidden;
        }
        
        #thermalCanvas {
            width: 100%;
            height: auto;
            display: block;
            image-rendering: auto;
        }
        
        
        .thermal-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
        }
        
        .stat-box {
            background: var(--bg-elevated);
            padding: 0.75rem;
            border-radius: 4px;
            border-left: 3px solid var(--accent);
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }
        
        .stat-value {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        /* Config Panel */
        .config-section {
            margin-bottom: 1rem;
        }
        
        .config-row {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.75rem;
        }
        
        .config-label {
            min-width: 120px;
            font-size: 0.875rem;
            color: var(--text-muted);
        }
        
        .config-slider {
            flex: 1;
            height: 6px;
            background: var(--bg-elevated);
            border-radius: 3px;
            outline: none;
            -webkit-appearance: none;
        }
        
        .config-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 16px;
            height: 16px;
            background: var(--accent);
            border-radius: 50%;
            cursor: pointer;
        }
        
        .config-slider::-moz-range-thumb {
            width: 16px;
            height: 16px;
            background: var(--accent);
            border-radius: 50%;
            cursor: pointer;
            border: none;
        }
        
        .config-value {
            min-width: 60px;
            text-align: right;
            font-size: 0.875rem;
            color: var(--accent);
            font-weight: 600;
        }
        
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: var(--accent);
            color: var(--bg-primary);
            border: none;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 0.5rem;
        }
        
        .btn:hover {
            background: var(--accent-hover);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .btn-secondary {
            background: var(--bg-elevated);
            color: var(--text-primary);
        }
        
        .btn-secondary:hover {
            background: var(--border);
        }
        
        /* Event Log */
        #eventLog {
            flex: 1;
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 0.75rem;
            overflow-y: auto;
            font-size: 0.75rem;
            font-family: 'Courier New', monospace;
        }
        
        .log-entry {
            margin-bottom: 0.5rem;
            padding: 0.25rem 0.5rem;
            border-radius: 2px;
            border-left: 2px solid var(--border);
        }
        
        .log-entry.success {
            border-left-color: var(--success);
            color: var(--success);
        }
        
        .log-entry.error {
            border-left-color: var(--danger);
            color: var(--danger);
        }
        
        .log-entry.info {
            border-left-color: var(--accent);
            color: var(--accent);
        }
        
        .log-time {
            color: var(--text-muted);
            margin-right: 0.5rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Cold Plasma Treatment System</h1>
    </div>
    
    <div class="main-container">
        <!-- 3D Model Viewer -->
        <div class="panel">
            <div class="panel-title">3D Model Viewer</div>
            <div id="viewer-container"></div>
            <button class="btn btn-secondary" onclick="loadDemoModel()" style="margin-top: 1rem;">Load Demo Hand Model</button>
        </div>
        
        <!-- Thermal Camera -->
        <div class="panel">
            <div class="panel-title">Thermal Camera</div>
            <div class="thermal-container">
                <div class="heatmap-wrapper">
                    <canvas id="thermalCanvas" width="320" height="240"></canvas>
                </div>
                <div class="thermal-stats">
                    <div class="stat-box">
                        <div class="stat-label">Max Temp</div>
                        <div class="stat-value" id="maxTemp">--°C</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Min Temp</div>
                        <div class="stat-value" id="minTemp">--°C</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Mean Temp</div>
                        <div class="stat-value" id="meanTemp">--°C</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Frame Rate</div>
                        <div class="stat-value" id="frameRate">--Hz</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Config & Controls -->
        <div class="panel">
            <div class="panel-title">G-code Generation</div>
            
            <div class="config-section">
                <div class="config-row">
                    <span class="config-label">Standoff (mm)</span>
                    <input type="range" class="config-slider" id="standoffSlider" min="1" max="20" value="5" step="0.5" oninput="updateConfigValue('standoff', this.value)">
                    <span class="config-value" id="standoffValue">5.0</span>
                </div>
                <div class="config-row">
                    <span class="config-label">Line Spacing (mm)</span>
                    <input type="range" class="config-slider" id="spacingSlider" min="0.5" max="10" value="3" step="0.5" oninput="updateConfigValue('spacing', this.value)">
                    <span class="config-value" id="spacingValue">3.0</span>
                </div>
                <div class="config-row">
                    <span class="config-label">Feed Rate (mm/s)</span>
                    <input type="range" class="config-slider" id="feedRateSlider" min="10" max="200" value="50" step="5" oninput="updateConfigValue('feedRate', this.value)">
                    <span class="config-value" id="feedRateValue">50</span>
                </div>
            </div>
            
            <button class="btn" id="generateBtn" onclick="runGcodegen()">Generate Toolpath</button>
            <button class="btn btn-secondary" id="visualizerBtn" onclick="openVisualizer()">Open Visualizer</button>
            
            <div class="panel-title" style="margin-top: 1.5rem; margin-bottom: 0.5rem;">Event Log</div>
            <div id="eventLog"></div>
        </div>
    </div>
    
    <!-- Three.js for 3D viewer -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/PLYLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script>
        // Ensure PLYLoader is available (fallback if CDN fails)
        if (typeof THREE !== 'undefined' && !THREE.PLYLoader) {
            console.warn('PLYLoader not loaded, using fallback');
            // Try alternative CDN
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/three@0.128.0/examples/js/loaders/PLYLoader.js';
            document.head.appendChild(script);
        }
    </script>
    
    <script>
        // ===== 3D Model Viewer =====
        let scene, camera, renderer, controls, modelMesh = null;
        
        function init3DViewer() {
            const container = document.getElementById('viewer-container');
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0f14);
            
            camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
            camera.position.set(150, 150, 150);
            
            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(width, height);
            container.appendChild(renderer.domElement);
            
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.target.set(0, 0, 0);
            controls.update();
            
            // Add lights
            const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(100, 100, 100);
            scene.add(directionalLight);
            
            // Add axes helper
            const axesHelper = new THREE.AxesHelper(50);
            scene.add(axesHelper);
            
            animate();
        }
        
        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }
        
        function loadDemoModel() {
            addLog('Loading demo hand model...', 'info');
            
            fetch('/api/load-demo-hand')
                .then(res => res.json())
                .then(data => {
                    addLog(`Model loaded: ${data.filename}`, 'success');
                    loadModel3D(data.model_id);
                })
                .catch(err => {
                    addLog(`Failed to load model: ${err.message}`, 'error');
                });
        }
        
        function loadModel3D(modelId) {
            const loader = new THREE.PLYLoader();
            
            loader.load(
                `/api/models/${modelId}`,
                (geometry) => {
                    // Remove old model
                    if (modelMesh) {
                        scene.remove(modelMesh);
                        if (modelMesh.geometry) modelMesh.geometry.dispose();
                        if (modelMesh.material) modelMesh.material.dispose();
                    }
                    
                    // Create material
                    const material = new THREE.PointsMaterial({
                        color: 0x00d4aa,
                        size: 2,
                        vertexColors: false
                    });
                    
                    // Create mesh from geometry
                    modelMesh = new THREE.Points(geometry, material);
                    scene.add(modelMesh);
                    
                    // Center and scale (model is already normalized by backend)
                    geometry.computeBoundingBox();
                    const box = geometry.boundingBox;
                    const size = box.getSize(new THREE.Vector3());
                    const maxDim = Math.max(size.x, size.y, size.z);
                    
                    if (maxDim > 0) {
                        // Model is already centered at origin and scaled to 150mm
                        camera.position.set(150 * 2.5, 150 * 2.5, 150 * 2.5);
                        controls.target.set(0, 0, 0);
                        controls.update();
                    }
                    
                    addLog('3D model displayed', 'success');
                },
                undefined,
                (error) => {
                    addLog(`Failed to load 3D model: ${error}`, 'error');
                }
            );
        }
        
        // ===== Thermal Camera =====
        let thermalWs = null;
        let frameCount = 0;
        let startTime = Date.now();
        const thermalCanvas = document.getElementById('thermalCanvas');
        const thermalCtx = thermalCanvas.getContext('2d');
        
        // Jet colormap function (from test_mlx90640_http.py)
        function jetColormap(value) {
            value = Math.max(0, Math.min(1, value));
            let r, g, b;
            
            if (value < 0.125) {
                r = 0; g = 0; b = 0.5 + (value / 0.125) * 0.5;
            } else if (value < 0.375) {
                r = 0; g = (value - 0.125) / 0.25; b = 1;
            } else if (value < 0.625) {
                r = (value - 0.375) / 0.25; g = 1; b = 1 - (value - 0.375) / 0.25;
            } else if (value < 0.875) {
                r = 1; g = 1 - (value - 0.625) / 0.25; b = 0;
            } else {
                r = 1 - (value - 0.875) / 0.125 * 0.5; g = 0; b = 0;
            }
            
            return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
        }
        
        // Draw thermal heatmap (from test_mlx90640_http.py)
        function drawHeatmap(thermalData, minTemp, maxTemp) {
            const width = 32;
            const height = 24;
            const tempRange = maxTemp - minTemp;
            
            // Create ImageData
            const imageData = thermalCtx.createImageData(width, height);
            const data = imageData.data;
            
            for (let i = 0; i < thermalData.length; i++) {
                const temp = thermalData[i];
                const normalized = tempRange > 0 ? (temp - minTemp) / tempRange : 0.5;
                const [r, g, b] = jetColormap(normalized);
                
                const pixelIndex = i * 4;
                data[pixelIndex] = r;
                data[pixelIndex + 1] = g;
                data[pixelIndex + 2] = b;
                data[pixelIndex + 3] = 255;
            }
            
            // Draw to offscreen canvas first
            const offscreen = document.createElement('canvas');
            offscreen.width = width;
            offscreen.height = height;
            const offscreenCtx = offscreen.getContext('2d');
            offscreenCtx.putImageData(imageData, 0, 0);
            
            // Scale up with smooth interpolation
            thermalCtx.imageSmoothingEnabled = true;
            thermalCtx.imageSmoothingQuality = 'high';
            thermalCtx.clearRect(0, 0, thermalCanvas.width, thermalCanvas.height);
            thermalCtx.drawImage(offscreen, 0, 0, thermalCanvas.width, thermalCanvas.height);
        }
        
        // Connect to thermal WebSocket
        function connectThermal() {
            if (thermalWs) return;
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/thermal`;
            
            thermalWs = new WebSocket(wsUrl);
            frameCount = 0;
            startTime = Date.now();
            
            thermalWs.onopen = () => {
                addLog('Thermal camera connected', 'success');
            };
            
            thermalWs.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.error) {
                    addLog(`Thermal error: ${data.error}`, 'error');
                    return;
                }
                
                // Update frame count
                frameCount++;
                const elapsed = (Date.now() - startTime) / 1000;
                const frameRate = frameCount / elapsed;
                
                // Update statistics
                document.getElementById('maxTemp').textContent = data.max_temp.toFixed(1) + '°C';
                document.getElementById('minTemp').textContent = data.min_temp.toFixed(1) + '°C';
                document.getElementById('meanTemp').textContent = data.mean_temp.toFixed(1) + '°C';
                document.getElementById('frameRate').textContent = frameRate.toFixed(1) + ' Hz';
                
                // Draw heatmap
                drawHeatmap(data.thermal, data.min_temp, data.max_temp);
            };
            
            thermalWs.onerror = (error) => {
                addLog('Thermal WebSocket error', 'error');
            };
            
            thermalWs.onclose = () => {
                thermalWs = null;
                addLog('Thermal camera disconnected', 'info');
            };
        }
        
        // ===== Config Panel =====
        function updateConfigValue(name, value) {
            document.getElementById(name + 'Value').textContent = parseFloat(value).toFixed(1);
        }
        
        function getConfig() {
            return {
                standoff_distance: parseFloat(document.getElementById('standoffSlider').value),
                line_spacing: parseFloat(document.getElementById('spacingSlider').value),
                feed_rate: parseFloat(document.getElementById('feedRateSlider').value),
                rapid_rate: 200.0,
                use_bidirectional: true,
                points_per_line: 80
            };
        }
        
        // ===== G-code Generation =====
        function runGcodegen() {
            const btn = document.getElementById('generateBtn');
            btn.disabled = true;
            addLog('Starting gcodegen...', 'info');
            
            fetch('/api/run-gcodegen', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config: getConfig() })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    addLog(`G-code generation complete: ${data.message}`, 'success');
                } else {
                    addLog(`G-code generation failed: ${data.error}`, 'error');
                }
            })
            .catch(err => {
                addLog(`Error: ${err.message}`, 'error');
            })
            .finally(() => {
                btn.disabled = false;
            });
        }
        
        function openVisualizer() {
            const btn = document.getElementById('visualizerBtn');
            btn.disabled = true;
            addLog('Opening visualizer...', 'info');
            
            fetch('/api/open-visualizer', {
                method: 'POST'
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    addLog('Visualizer opened', 'success');
                } else {
                    addLog(`Failed to open visualizer: ${data.error}`, 'error');
                }
            })
            .catch(err => {
                addLog(`Error: ${err.message}`, 'error');
            })
            .finally(() => {
                btn.disabled = false;
            });
        }
        
        // ===== Event Log =====
        function addLog(message, type = 'info') {
            const log = document.getElementById('eventLog');
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            
            const time = new Date().toLocaleTimeString();
            entry.innerHTML = `<span class="log-time">[${time}]</span>${message}`;
            
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
        }
        
        // ===== Initialize =====
        window.addEventListener('load', () => {
            init3DViewer();
            setTimeout(connectThermal, 500);
            addLog('System initialized', 'success');
        });
    </script>
</body>
</html>
"""
