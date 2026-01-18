"""
Embedded HTML template for the unified demo interface.
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
        
        .status-badge {
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 600;
            background: var(--success);
            color: var(--bg-primary);
        }
        
        .status-badge.error {
            background: var(--danger);
        }
        
        .main-container {
            display: grid;
            grid-template-columns: 1fr 400px 350px;
            grid-template-rows: 1fr 1fr;
            gap: 1rem;
            padding: 1rem;
            height: calc(100vh - 80px);
        }
        
        .viewer-section {
            grid-column: 1;
            grid-row: 1 / 3;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .viz-image-container {
            flex: 1;
            background: #000;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            min-height: 300px;
        }
        
        #toolpathViz {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        
        .viz-controls {
            display: flex;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }
        
        .viz-controls .btn {
            flex: 1;
            margin-bottom: 0;
            padding: 0.5rem;
            font-size: 0.75rem;
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
        
        .colorbar {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 20px;
            height: 150px;
            border-radius: 2px;
            border: 1px solid rgba(255,255,255,0.3);
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
        
        /* Controls Panel */
        .controls-section {
            margin-bottom: 1.5rem;
        }
        
        .section-title {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-bottom: 0.75rem;
            letter-spacing: 0.05em;
        }
        
        .file-input-wrapper {
            position: relative;
            margin-bottom: 0.75rem;
        }
        
        .file-input-wrapper input[type="file"] {
            display: none;
        }
        
        .file-input-label {
            display: block;
            padding: 0.75rem;
            background: var(--bg-elevated);
            border: 1px dashed var(--border);
            border-radius: 4px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.875rem;
        }
        
        .file-input-label:hover {
            border-color: var(--accent);
            background: var(--bg-panel);
        }
        
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: var(--accent);
            color: var(--bg-primary);
            border: none;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 0.5rem;
        }
        
        .btn:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: var(--bg-elevated);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }
        
        .btn-secondary:hover {
            background: var(--bg-panel);
        }
        
        .slider-group {
            margin-bottom: 1rem;
        }
        
        .slider-label {
            display: flex;
            justify-content: space-between;
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
        }
        
        .slider-label span:first-child {
            color: var(--text-muted);
        }
        
        .slider-label span:last-child {
            color: var(--accent);
            font-weight: 600;
        }
        
        input[type="range"] {
            width: 100%;
            height: 4px;
            background: var(--bg-elevated);
            border-radius: 2px;
            outline: none;
            -webkit-appearance: none;
        }
        
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 16px;
            height: 16px;
            background: var(--accent);
            border-radius: 50%;
            cursor: pointer;
        }
        
        input[type="range"]::-moz-range-thumb {
            width: 16px;
            height: 16px;
            background: var(--accent);
            border-radius: 50%;
            cursor: pointer;
            border: none;
        }
        
        .bounds-display {
            background: var(--bg-elevated);
            padding: 0.75rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 1rem;
        }
        
        .bounds-display div {
            margin-bottom: 0.25rem;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: var(--bg-elevated);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--accent);
            transition: width 0.3s;
            width: 0%;
        }
        
        .progress-status {
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        
        .info-display {
            background: var(--bg-elevated);
            padding: 0.75rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .info-display div {
            margin-bottom: 0.25rem;
            color: var(--text-muted);
        }
        
        .info-display div strong {
            color: var(--text-primary);
        }
        
        /* Event Log */
        .event-log {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--bg-panel);
            border-top: 1px solid var(--border);
            padding: 0.75rem 1rem;
            max-height: 150px;
            overflow-y: auto;
            font-size: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .event-log-entry {
            margin-bottom: 0.25rem;
            padding: 0.25rem 0;
            border-bottom: 1px solid var(--border);
        }
        
        .event-log-entry:last-child {
            border-bottom: none;
        }
        
        .event-time {
            color: var(--text-muted);
            margin-right: 0.5rem;
        }
        
        .event-message {
            color: var(--text-primary);
        }
        
        .event-success {
            color: var(--success);
        }
        
        .event-error {
            color: var(--danger);
        }
        
        .event-warning {
            color: var(--warning);
        }
        
        @media (max-width: 1400px) {
            .main-container {
                grid-template-columns: 1fr;
                grid-template-rows: auto auto auto;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>COLD PLASMA TREATMENT SYSTEM</h1>
        <div class="status-badge" id="systemStatus">INITIALIZING</div>
    </div>
    
    <div class="main-container">
        <!-- 3D Viewer Section (spans 2 rows) -->
        <div class="viewer-section">
            <!-- 3D Model Viewer Panel -->
            <div class="panel">
                <div class="panel-title">3D Model Viewer</div>
                <div id="viewer-container"></div>
            </div>
            
            <!-- Toolpath Visualizer Panel -->
            <div class="panel">
                <div class="panel-title">Toolpath Visualizer</div>
                <div class="viz-image-container">
                    <img id="toolpathViz" src="/api/visualizer/image?view=3d" alt="Toolpath Visualization">
                </div>
                <div class="viz-controls">
                    <button class="btn btn-secondary" onclick="refreshViz('3d')">3D View</button>
                    <button class="btn btn-secondary" onclick="refreshViz('top')">Top View</button>
                    <button class="btn btn-secondary" onclick="refreshViz('side')">Side View</button>
                    <button class="btn btn-secondary" onclick="refreshViz()">Refresh</button>
                </div>
            </div>
        </div>
        
        <!-- Thermal Panel -->
        <div class="panel">
            <div class="panel-title">Thermal Camera</div>
            <div class="thermal-container">
                <div class="heatmap-wrapper">
                    <canvas id="thermalCanvas" width="400" height="300"></canvas>
                    <canvas id="colorbarCanvas" class="colorbar"></canvas>
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
        
        <!-- Controls Panel -->
        <div class="panel">
            <div class="panel-title">Controls</div>
            
            <!-- Upload Section -->
            <div class="controls-section">
                <div class="section-title">Model Upload</div>
                <div class="file-input-wrapper">
                    <input type="file" id="modelFile" accept=".ply,.obj">
                    <label for="modelFile" class="file-input-label">Choose PLY/OBJ File</label>
                </div>
                <button class="btn btn-secondary" onclick="loadDemoHand()">Load Demo Hand</button>
            </div>
            
            <!-- Generation Section -->
            <div class="controls-section">
                <div class="section-title">Path Generation</div>
                <div class="bounds-display" id="boundsDisplay">
                    <div>No model loaded</div>
                </div>
                
                <div class="slider-group">
                    <div class="slider-label">
                        <span>Standoff Distance</span>
                        <span id="standoffValue">5.0 mm</span>
                    </div>
                    <input type="range" id="standoffSlider" min="1" max="20" step="0.5" value="5" oninput="updateStandoff(this.value)">
                </div>
                
                <div class="slider-group">
                    <div class="slider-label">
                        <span>Line Spacing</span>
                        <span id="lineSpacingValue">3.0 mm</span>
                    </div>
                    <input type="range" id="lineSpacingSlider" min="1" max="10" step="0.5" value="3" oninput="updateLineSpacing(this.value)">
                </div>
                
                <div class="slider-group">
                    <div class="slider-label">
                        <span>Feed Rate</span>
                        <span id="feedRateValue">50 mm/s</span>
                    </div>
                    <input type="range" id="feedRateSlider" min="10" max="200" step="10" value="50" oninput="updateFeedRate(this.value)">
                </div>
                
                <div class="progress-bar" id="progressBar" style="display: none;">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="progress-status" id="progressStatus"></div>
                
                <button class="btn" id="generateBtn" onclick="generatePath()" disabled>Generate Path</button>
            </div>
            
            <!-- Export Section -->
            <div class="controls-section">
                <div class="section-title">Export</div>
                <button class="btn btn-secondary" id="exportGcodeBtn" onclick="exportGcode()" disabled>Export G-code</button>
                <button class="btn btn-secondary" id="exportCsvBtn" onclick="exportCsv()" disabled>Export CSV</button>
            </div>
            
            <!-- Info Display -->
            <div class="controls-section">
                <div class="section-title">Info</div>
                <div class="info-display" id="infoDisplay">
                    <div>Waiting for model upload...</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Event Log -->
    <div class="event-log" id="eventLog"></div>
    
    <!-- Three.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/PLYLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/OBJLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    
    <script>
        // Global state
        let currentModelId = null;
        let currentBounds = null;
        let currentResultId = null;
        let scene, camera, renderer, controls;
        let modelMesh = null;
        let toolpathLines = null;
        let boundingBox = null;
        let boundingBoxHandles = [];
        let isDragging = false;
        let dragHandle = null;
        let raycaster = new THREE.Raycaster();
        let mouse = new THREE.Vector2();
        let dragPlane = null;
        let dragOffset = null;
        
        // Thermal state
        let thermalWs = null;
        let frameCount = 0;
        let startTime = Date.now();
        
        // Initialize
        init();
        
        function init() {
            init3DViewer();
            initThermal();
            initFileUpload();
            addEvent('System initialized', 'success');
        }
        
        function init3DViewer() {
            const container = document.getElementById('viewer-container');
            
            // Scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0f14);
            
            // Camera
            camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 10000);
            camera.position.set(200, 200, 200);
            
            // Renderer
            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(container.clientWidth, container.clientHeight);
            container.appendChild(renderer.domElement);
            
            // Controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            // Lighting
            const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
            scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(200, 200, 200);
            scene.add(directionalLight);
            
            // Grid helper
            const gridHelper = new THREE.GridHelper(500, 50, 0x1e2832, 0x0f1419);
            scene.add(gridHelper);
            
            // Axes helper
            const axesHelper = new THREE.AxesHelper(100);
            scene.add(axesHelper);
            
            // Handle resize
            window.addEventListener('resize', () => {
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            });
            
            // Animation loop
            animate();
        }
        
        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }
        
        function initThermal() {
            const canvas = document.getElementById('thermalCanvas');
            const ctx = canvas.getContext('2d');
            const colorbarCanvas = document.getElementById('colorbarCanvas');
            const colorbarCtx = colorbarCanvas.getContext('2d');
            
            // Draw colorbar
            drawColorbar(colorbarCtx, colorbarCanvas);
            
            // Connect WebSocket
            connectThermal();
        }
        
        function connectThermal() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/thermal`;
            
            thermalWs = new WebSocket(wsUrl);
            frameCount = 0;
            startTime = Date.now();
            
            thermalWs.onopen = () => {
                addEvent('Thermal camera connected', 'success');
            };
            
            thermalWs.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.error) {
                    console.error('Thermal error:', data.error);
                    return;
                }
                
                // Update stats
                frameCount++;
                const elapsed = (Date.now() - startTime) / 1000;
                const frameRate = frameCount / elapsed;
                
                document.getElementById('maxTemp').textContent = data.max_temp.toFixed(1) + '°C';
                document.getElementById('minTemp').textContent = data.min_temp.toFixed(1) + '°C';
                document.getElementById('meanTemp').textContent = data.mean_temp.toFixed(1) + '°C';
                document.getElementById('frameRate').textContent = frameRate.toFixed(1) + ' Hz';
                
                // Draw heatmap
                drawHeatmap(data.thermal, data.min_temp, data.max_temp);
            };
            
            thermalWs.onerror = (error) => {
                console.error('Thermal WebSocket error:', error);
                addEvent('Thermal camera connection error', 'error');
            };
            
            thermalWs.onclose = () => {
                addEvent('Thermal camera disconnected', 'warning');
                // Reconnect after 2 seconds
                setTimeout(connectThermal, 2000);
            };
        }
        
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
        
        function drawColorbar(ctx, canvas) {
            const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
            for (let i = 0; i <= 10; i++) {
                const value = i / 10;
                const [r, g, b] = jetColormap(value);
                gradient.addColorStop(value, `rgb(${r},${g},${b})`);
            }
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }
        
        function drawHeatmap(thermalData, minTemp, maxTemp) {
            const canvas = document.getElementById('thermalCanvas');
            const ctx = canvas.getContext('2d');
            const width = 32;
            const height = 24;
            const tempRange = maxTemp - minTemp;
            
            // Create ImageData
            const imageData = ctx.createImageData(width, height);
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
            ctx.imageSmoothingEnabled = true;
            ctx.imageSmoothingQuality = 'high';
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(offscreen, 0, 0, canvas.width, canvas.height);
        }
        
        function initFileUpload() {
            document.getElementById('modelFile').addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (file) {
                    await uploadModel(file);
                }
            });
        }
        
        async function uploadModel(file) {
            addEvent(`Uploading ${file.name}...`, 'info');
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Upload failed');
                }
                
                const result = await response.json();
                currentModelId = result.model_id;
                currentBounds = result.bounds;
                
                // Load model in 3D viewer
                await loadModel3D(result.model_id);
                
                // Update UI
                updateBoundsDisplay(result.bounds);
                updateInfoDisplay(result);
                document.getElementById('generateBtn').disabled = false;
                
                // Create bounding box
                createBoundingBox(result.bounds);
                
                addEvent(`Model loaded: ${result.point_count} points`, 'success');
            } catch (error) {
                addEvent(`Upload failed: ${error.message}`, 'error');
            }
        }
        
        async function loadModel3D(modelId) {
            const url = `/api/models/${modelId}`;
            
            // Try PLY loader first (most common)
            const plyLoader = new THREE.PLYLoader();
            const objLoader = new THREE.OBJLoader();
            
            // Function to handle successful geometry load
            function onGeometryLoaded(geometry) {
                // Remove old model
                if (modelMesh) {
                    scene.remove(modelMesh);
                    if (modelMesh.geometry) modelMesh.geometry.dispose();
                    if (modelMesh.material) modelMesh.material.dispose();
                }
                
                // Create material
                const material = new THREE.MeshStandardMaterial({
                    color: 0x6b7a8a,
                    wireframe: false,
                    side: THREE.DoubleSide
                });
                
                // Create mesh (model is already normalized and centered by backend)
                modelMesh = new THREE.Mesh(geometry, material);
                scene.add(modelMesh);
                
                // Model is already centered at origin, just position camera
                geometry.computeBoundingBox();
                const box = geometry.boundingBox;
                const size = box.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);
                
                if (maxDim > 0) {
                    // Position camera to view the model (already centered at origin)
                    const cameraDistance = maxDim * 2.5;
                    camera.position.set(cameraDistance, cameraDistance, cameraDistance);
                    controls.target.set(0, 0, 0);
                    controls.update();
                }
            }
            
            // Try PLY first
            plyLoader.load(
                url,
                (geometry) => {
                    addEvent('Model loaded successfully (PLY)', 'success');
                    onGeometryLoaded(geometry);
                },
                (progress) => {
                    // Loading progress
                    if (progress.lengthComputable) {
                        const percent = (progress.loaded / progress.total) * 100;
                        console.log('Loading progress: ' + percent.toFixed(0) + '%');
                    }
                },
                (error) => {
                    console.error('PLY loader error:', error);
                    addEvent('PLY load failed, trying OBJ...', 'warning');
                    
                    // Fallback to OBJ loader
                    objLoader.load(
                        url,
                        (object) => {
                            // OBJLoader returns a Group, extract geometry from first child
                            if (object.children && object.children.length > 0) {
                                const firstChild = object.children[0];
                                if (firstChild.geometry) {
                                    addEvent('Model loaded successfully (OBJ)', 'success');
                                    onGeometryLoaded(firstChild.geometry);
                                } else {
                                    addEvent('OBJ loaded but no geometry found', 'error');
                                }
                            } else {
                                addEvent('OBJ file appears empty', 'error');
                            }
                        },
                        (progress) => {
                            // Loading progress
                            if (progress.lengthComputable) {
                                const percent = (progress.loaded / progress.total) * 100;
                                console.log('OBJ loading progress: ' + percent.toFixed(0) + '%');
                            }
                        },
                        (error) => {
                            console.error('OBJ loader error:', error);
                            addEvent(`Failed to load model: ${error.message || 'Unknown error'}`, 'error');
                        }
                    );
                }
            );
        }
        
        async function loadDemoHand() {
            addEvent('Loading demo hand model...', 'info');
            // Try to load demo hand OBJ file
            try {
                const response = await fetch('/api/load-demo-hand');
                if (response.ok) {
                    const result = await response.json();
                    currentModelId = result.model_id;
                    currentBounds = result.bounds;
                    
                    // Load model in 3D viewer
                    await loadModel3D(result.model_id);
                    
                    // Update UI
                    updateBoundsDisplay(result.bounds);
                    updateInfoDisplay(result);
                    document.getElementById('generateBtn').disabled = false;
                    
                    // Create bounding box
                    createBoundingBox(result.bounds);
                    
                    addEvent(`Demo hand loaded: ${result.point_count} points`, 'success');
                } else {
                    const error = await response.json();
                    addEvent(`Demo hand load failed: ${error.detail || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                addEvent(`Failed to load demo hand: ${error.message}`, 'error');
            }
        }
        
        function createBoundingBox(bounds) {
            // Remove old bounding box and event listeners
            if (boundingBox) {
                scene.remove(boundingBox);
                boundingBoxHandles.forEach(h => scene.remove(h));
                boundingBoxHandles = [];
            }
            
            // Remove old event listeners
            renderer.domElement.removeEventListener('mousedown', handleMouseDown);
            renderer.domElement.removeEventListener('mousemove', handleMouseMove);
            renderer.domElement.removeEventListener('mouseup', handleMouseUp);
            
            const width = bounds.x_max - bounds.x_min;
            const height = bounds.y_max - bounds.y_min;
            const depth = bounds.z_max - bounds.z_min;
            const center = new THREE.Vector3(
                (bounds.x_min + bounds.x_max) / 2,
                (bounds.y_min + bounds.y_max) / 2,
                (bounds.z_min + bounds.z_max) / 2
            );
            
            // Store bounds for updates
            currentBounds = bounds;
            
            // Create wireframe box
            const boxGeometry = new THREE.BoxGeometry(width, height, depth);
            const edges = new THREE.EdgesGeometry(boxGeometry);
            const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0xffff00, linewidth: 2 }));
            line.position.copy(center);
            boundingBox = line;
            scene.add(boundingBox);
            
            // Create just 2 draggable handles (min and max corners) - simpler and more intuitive
            const handleGeometry = new THREE.SphereGeometry(8, 16, 16);
            const handleMaterial = new THREE.MeshBasicMaterial({ color: 0xffff00 });
            
            // Min corner handle
            const minHandle = new THREE.Mesh(handleGeometry, handleMaterial);
            minHandle.position.set(bounds.x_min, bounds.y_min, bounds.z_min);
            minHandle.userData.isMin = true;
            scene.add(minHandle);
            boundingBoxHandles.push(minHandle);
            
            // Max corner handle
            const maxHandle = new THREE.Mesh(handleGeometry, handleMaterial);
            maxHandle.position.set(bounds.x_max, bounds.y_max, bounds.z_max);
            maxHandle.userData.isMin = false;
            scene.add(maxHandle);
            boundingBoxHandles.push(maxHandle);
            
            // Add event listeners
            renderer.domElement.addEventListener('mousedown', handleMouseDown);
            renderer.domElement.addEventListener('mousemove', handleMouseMove);
            renderer.domElement.addEventListener('mouseup', handleMouseUp);
        }
        
        function handleMouseDown(event) {
            const rect = renderer.domElement.getBoundingClientRect();
            mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
            
            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObjects(boundingBoxHandles);
            
            if (intersects.length > 0) {
                isDragging = true;
                dragHandle = intersects[0].object;
                controls.enabled = false;
                
                // Create a plane perpendicular to camera for dragging
                const cameraDirection = new THREE.Vector3();
                camera.getWorldDirection(cameraDirection);
                dragPlane = new THREE.Plane();
                dragPlane.setFromNormalAndCoplanarPoint(cameraDirection, dragHandle.position);
                
                // Calculate offset from handle to intersection point
                const intersection = new THREE.Vector3();
                raycaster.ray.intersectPlane(dragPlane, intersection);
                dragOffset = new THREE.Vector3().subVectors(dragHandle.position, intersection);
            }
        }
        
        function handleMouseMove(event) {
            if (!isDragging || !dragHandle || !dragPlane) return;
            
            const rect = renderer.domElement.getBoundingClientRect();
            mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
            
            raycaster.setFromCamera(mouse, camera);
            
            // Get intersection with drag plane
            const intersection = new THREE.Vector3();
            if (raycaster.ray.intersectPlane(dragPlane, intersection)) {
                // Apply offset
                intersection.add(dragOffset);
                
                // Update handle position
                dragHandle.position.copy(intersection);
                
                // Update bounds
                updateBoundsFromHandles();
            }
        }
        
        function handleMouseUp() {
            if (isDragging) {
                isDragging = false;
                dragHandle = null;
                dragPlane = null;
                dragOffset = null;
                controls.enabled = true;
            }
        }
        
        function updateBoundsFromHandles() {
            if (boundingBoxHandles.length !== 2) return;
            
            const minHandle = boundingBoxHandles.find(h => h.userData.isMin);
            const maxHandle = boundingBoxHandles.find(h => !h.userData.isMin);
            
            if (!minHandle || !maxHandle) return;
            
            const minPos = minHandle.position;
            const maxPos = maxHandle.position;
            
            // Ensure min < max
            const xMin = Math.min(minPos.x, maxPos.x);
            const xMax = Math.max(minPos.x, maxPos.x);
            const yMin = Math.min(minPos.y, maxPos.y);
            const yMax = Math.max(minPos.y, maxPos.y);
            const zMin = Math.min(minPos.z, maxPos.z);
            const zMax = Math.max(minPos.z, maxPos.z);
            
            // Ensure minimum size
            const minSize = 5;
            if (xMax - xMin < minSize) {
                const centerX = (xMin + xMax) / 2;
                if (minHandle.userData.isMin) {
                    minHandle.position.x = centerX - minSize / 2;
                    maxHandle.position.x = centerX + minSize / 2;
                } else {
                    maxHandle.position.x = centerX + minSize / 2;
                    minHandle.position.x = centerX - minSize / 2;
                }
            }
            if (zMax - zMin < minSize) {
                const centerZ = (zMin + zMax) / 2;
                if (minHandle.userData.isMin) {
                    minHandle.position.z = centerZ - minSize / 2;
                    maxHandle.position.z = centerZ + minSize / 2;
                } else {
                    maxHandle.position.z = centerZ + minSize / 2;
                    minHandle.position.z = centerZ - minSize / 2;
                }
            }
            
            // Update current bounds
            currentBounds = {
                x_min: Math.min(minHandle.position.x, maxHandle.position.x),
                x_max: Math.max(minHandle.position.x, maxHandle.position.x),
                y_min: Math.min(minHandle.position.y, maxHandle.position.y),
                y_max: Math.max(minHandle.position.y, maxHandle.position.y),
                z_min: Math.min(minHandle.position.z, maxHandle.position.z),
                z_max: Math.max(minHandle.position.z, maxHandle.position.z)
            };
            
            // Update box geometry
            const width = currentBounds.x_max - currentBounds.x_min;
            const height = currentBounds.y_max - currentBounds.y_min;
            const depth = currentBounds.z_max - currentBounds.z_min;
            const center = new THREE.Vector3(
                (currentBounds.x_min + currentBounds.x_max) / 2,
                (currentBounds.y_min + currentBounds.y_max) / 2,
                (currentBounds.z_min + currentBounds.z_max) / 2
            );
            
            boundingBox.geometry.dispose();
            const boxGeometry = new THREE.BoxGeometry(width, height, depth);
            const edges = new THREE.EdgesGeometry(boxGeometry);
            boundingBox.geometry = edges;
            boundingBox.position.copy(center);
            
            // Update display
            updateBoundsDisplay(currentBounds);
        }
        
        function updateBoundsDisplay(bounds) {
            const display = document.getElementById('boundsDisplay');
            display.innerHTML = `
                <div><strong>X:</strong> ${bounds.x_min.toFixed(1)} to ${bounds.x_max.toFixed(1)} mm</div>
                <div><strong>Y:</strong> ${bounds.y_min.toFixed(1)} to ${bounds.y_max.toFixed(1)} mm</div>
                <div><strong>Z:</strong> ${bounds.z_min.toFixed(1)} to ${bounds.z_max.toFixed(1)} mm</div>
            `;
        }
        
        function updateInfoDisplay(result) {
            const display = document.getElementById('infoDisplay');
            display.innerHTML = `
                <div><strong>Model:</strong> ${result.filename}</div>
                <div><strong>Points:</strong> ${result.point_count.toLocaleString()}</div>
            `;
        }
        
        function updateStandoff(value) {
            document.getElementById('standoffValue').textContent = parseFloat(value).toFixed(1) + ' mm';
        }
        
        function updateLineSpacing(value) {
            document.getElementById('lineSpacingValue').textContent = parseFloat(value).toFixed(1) + ' mm';
        }
        
        function updateFeedRate(value) {
            document.getElementById('feedRateValue').textContent = parseInt(value) + ' mm/s';
        }
        
        async function generatePath() {
            if (!currentModelId || !currentBounds) {
                addEvent('Please load a model first', 'error');
                return;
            }
            
            const config = {
                standoff_distance: parseFloat(document.getElementById('standoffSlider').value),
                line_spacing: parseFloat(document.getElementById('lineSpacingSlider').value),
                feed_rate: parseFloat(document.getElementById('feedRateSlider').value),
                rapid_rate: 200.0,
                use_bidirectional: true,
                points_per_line: 80,
                name: 'generated_path'
            };
            
            // Show progress
            document.getElementById('progressBar').style.display = 'block';
            document.getElementById('generateBtn').disabled = true;
            
            // Connect to progress WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const progressWs = new WebSocket(`${protocol}//${window.location.host}/ws/progress`);
            
            progressWs.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'progress') {
                    document.getElementById('progressFill').style.width = data.progress + '%';
                    document.getElementById('progressStatus').textContent = data.status;
                }
            };
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model_id: currentModelId,
                        bounds: currentBounds,
                        config: config
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Generation failed');
                }
                
                const result = await response.json();
                currentResultId = result.result_id;
                
                // Render toolpath
                renderToolpath(result.toolpath);
                
                // Update info
                updateInfoDisplay({
                    filename: 'Generated Path',
                    point_count: result.stats.num_points,
                    treatment_length: result.stats.treatment_length_mm
                });
                
                // Enable export buttons
                document.getElementById('exportGcodeBtn').disabled = false;
                document.getElementById('exportCsvBtn').disabled = false;
                
                // Refresh visualizer
                refreshViz();
                
                addEvent(`Path generated: ${result.stats.num_points} points`, 'success');
            } catch (error) {
                addEvent(`Generation failed: ${error.message}`, 'error');
            } finally {
                document.getElementById('progressBar').style.display = 'none';
                document.getElementById('generateBtn').disabled = false;
                progressWs.close();
            }
        }
        
        function renderToolpath(toolpath) {
            // Remove old toolpath
            if (toolpathLines) {
                if (Array.isArray(toolpathLines)) {
                    toolpathLines.forEach(line => {
                        scene.remove(line);
                        if (line.geometry) line.geometry.dispose();
                        if (line.material) line.material.dispose();
                    });
                } else {
                    scene.remove(toolpathLines);
                    if (toolpathLines.geometry) toolpathLines.geometry.dispose();
                    if (toolpathLines.material) toolpathLines.material.dispose();
                }
            }
            
            toolpathLines = [];
            
            // Group points into continuous segments (raster lines)
            // Rapid moves separate segments
            let currentSegment = [];
            
            toolpath.forEach((pt, idx) => {
                const pos = new THREE.Vector3(...pt.position);
                
                if (pt.is_rapid) {
                    // End current segment if it has points
                    if (currentSegment.length > 1) {
                        const geometry = new THREE.BufferGeometry().setFromPoints(currentSegment);
                        const material = new THREE.LineBasicMaterial({ 
                            color: 0x00aaff, 
                            linewidth: 3 
                        });
                        const line = new THREE.Line(geometry, material);
                        scene.add(line);
                        toolpathLines.push(line);
                    }
                    currentSegment = [];
                } else {
                    // Add to current segment
                    currentSegment.push(pos);
                }
            });
            
            // Add final segment
            if (currentSegment.length > 1) {
                const geometry = new THREE.BufferGeometry().setFromPoints(currentSegment);
                const material = new THREE.LineBasicMaterial({ 
                    color: 0x00aaff, 
                    linewidth: 3 
                });
                const line = new THREE.Line(geometry, material);
                scene.add(line);
                toolpathLines.push(line);
            }
            
            // Render rapid moves as dashed lines between segments
            let rapidStart = null;
            toolpath.forEach((pt, idx) => {
                const pos = new THREE.Vector3(...pt.position);
                
                if (pt.is_rapid) {
                    if (rapidStart === null) {
                        rapidStart = pos;
                    } else {
                        // Draw rapid move line
                        const rapidGeometry = new THREE.BufferGeometry().setFromPoints([rapidStart, pos]);
                        const rapidMaterial = new THREE.LineDashedMaterial({ 
                            color: 0xff6600, 
                            dashSize: 3, 
                            gapSize: 3,
                            linewidth: 1
                        });
                        const rapidLine = new THREE.Line(rapidGeometry, rapidMaterial);
                        rapidLine.computeLineDistances();
                        scene.add(rapidLine);
                        toolpathLines.push(rapidLine);
                        rapidStart = null;
                    }
                } else {
                    rapidStart = null;
                }
            });
        }
        
        async function exportGcode() {
            if (!currentResultId) {
                addEvent('No path generated yet', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/export/gcode', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ result_id: currentResultId })
                });
                
                if (!response.ok) {
                    throw new Error('Export failed');
                }
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `toolpath_${Date.now()}.gcode`;
                a.click();
                window.URL.revokeObjectURL(url);
                
                addEvent('G-code exported', 'success');
            } catch (error) {
                addEvent(`Export failed: ${error.message}`, 'error');
            }
        }
        
        async function exportCsv() {
            if (!currentResultId) {
                addEvent('No path generated yet', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/export/csv', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ result_id: currentResultId })
                });
                
                if (!response.ok) {
                    throw new Error('Export failed');
                }
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `toolpath_${Date.now()}.csv`;
                a.click();
                window.URL.revokeObjectURL(url);
                
                addEvent('CSV exported', 'success');
            } catch (error) {
                addEvent(`Export failed: ${error.message}`, 'error');
            }
        }
        
        function refreshViz(view = '3d') {
            const img = document.getElementById('toolpathViz');
            // Add timestamp to force refresh
            const timestamp = new Date().getTime();
            img.src = `/api/visualizer/image?view=${view}&t=${timestamp}`;
        }
        
        function addEvent(message, type = 'info') {
            const log = document.getElementById('eventLog');
            const entry = document.createElement('div');
            entry.className = 'event-log-entry';
            
            const time = new Date().toLocaleTimeString();
            entry.innerHTML = `
                <span class="event-time">[${time}]</span>
                <span class="event-message event-${type}">${message}</span>
            `;
            
            log.insertBefore(entry, log.firstChild);
            
            // Keep only last 50 entries
            while (log.children.length > 50) {
                log.removeChild(log.lastChild);
            }
        }
        
        // Update system status
        setInterval(async () => {
            try {
                const response = await fetch('/api/health');
                const data = await response.json();
                const statusEl = document.getElementById('systemStatus');
                if (data.status === 'healthy') {
                    statusEl.textContent = 'OPERATIONAL';
                    statusEl.className = 'status-badge';
                } else {
                    statusEl.textContent = 'ERROR';
                    statusEl.className = 'status-badge error';
                }
            } catch (error) {
                document.getElementById('systemStatus').textContent = 'OFFLINE';
                document.getElementById('systemStatus').className = 'status-badge error';
            }
        }, 5000);
    </script>
</body>
</html>
"""
