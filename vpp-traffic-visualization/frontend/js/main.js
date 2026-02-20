/**
 * VPP Traffic Visualization Engine - Main JavaScript
 * 
 * This is the main entry point for the frontend application.
 * It handles WebSocket connections, 3D scene management, and UI interactions.
 */

// Global state
const state = {
    connected: false,
    paused: false,
    animationSpeed: 1.0,
    statistics: {
        totalPackets: 0,
        totalBytes: 0,
        controlCount: 0,
        telemetryCount: 0
    }
};

// Global managers
let socket = null;
let sceneManager = null;
let cameraController = null;
let particleSystem = null;

/**
 * Initialize the application
 */
function init() {
    console.log('Initializing VPP Traffic Visualization Engine...');
    
    // Initialize 3D scene first
    const canvas = document.getElementById('visualization-canvas');
    sceneManager = new SceneManager(canvas);
    sceneManager.initializeTopology();
    sceneManager.startRender();
    
    // Initialize particle system
    particleSystem = new ParticleSystem(sceneManager.scene, 10000);
    
    // Initialize camera controller
    cameraController = new CameraController(sceneManager, canvas);
    
    // Initialize WebSocket connection
    initWebSocket();
    
    // Initialize UI event listeners
    initUIListeners();
    
    // Start animation loop
    startAnimationLoop();
    
    console.log('Application initialized successfully');
}

/**
 * Initialize WebSocket connection
 */
function initWebSocket() {
    socket = io();
    
    socket.on('connect', () => {
        console.log('Connected to server');
        state.connected = true;
        updateConnectionStatus(true);
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        state.connected = false;
        updateConnectionStatus(false);
    });
    
    socket.on('traffic_event', (data) => {
        console.log('Received traffic event:', data);
        handleTrafficEvent(data);
    });
    
    socket.on('connection_response', (data) => {
        console.log('Connection response:', data);
    });
    
    socket.on('pong', (data) => {
        console.log('Pong received:', data);
    });
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const indicator = document.getElementById('connection-indicator');
    const text = document.getElementById('connection-text');
    
    if (connected) {
        indicator.classList.remove('disconnected');
        indicator.classList.add('connected');
        text.textContent = '已连接';
    } else {
        indicator.classList.remove('connected');
        indicator.classList.add('disconnected');
        text.textContent = '未连接';
    }
}

/**
 * Initialize UI event listeners
 */
function initUIListeners() {
    // Pause button
    document.getElementById('pause-btn').addEventListener('click', () => {
        state.paused = true;
        console.log('Animation paused');
    });
    
    // Resume button
    document.getElementById('resume-btn').addEventListener('click', () => {
        state.paused = false;
        console.log('Animation resumed');
    });
    
    // Reset button
    document.getElementById('reset-btn').addEventListener('click', () => {
        resetStatistics();
        sceneManager.resetCamera();
        console.log('Statistics reset and camera reset');
    });
    
    // Speed slider
    document.getElementById('speed-slider').addEventListener('input', (e) => {
        state.animationSpeed = parseFloat(e.target.value);
        document.getElementById('speed-value').textContent = state.animationSpeed.toFixed(1) + 'x';
        console.log('Animation speed changed to:', state.animationSpeed);
    });
    
    // Close info panel button
    document.getElementById('close-info').addEventListener('click', () => {
        document.getElementById('info-panel').classList.remove('show');
    });
    
    // Canvas click for component selection
    document.getElementById('visualization-canvas').addEventListener('click', (e) => {
        const rect = e.target.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width * 2 - 1;
        const y = -(e.clientY - rect.top) / rect.height * 2 + 1;
        
        const intersects = sceneManager.getIntersectedObjects(x, y);
        if (intersects.length > 0) {
            // Find which component was clicked
            for (const [name, comp] of Object.entries(sceneManager.components)) {
                if (comp.mesh === intersects[0].object) {
                    showComponentInfo(name, comp);
                    break;
                }
            }
        }
    });
}

/**
 * Initialize 3D scene (placeholder)
 */
function initScene() {
    const canvas = document.getElementById('visualization-canvas');
    
    // Placeholder: Just fill with dark background
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    
    ctx.fillStyle = '#0a0e27';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw placeholder text
    ctx.fillStyle = '#4ecdc4';
    ctx.font = '20px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('3D 拓扑图 (Three.js 将在后续实现)', canvas.width / 2, canvas.height / 2);
    
    console.log('Scene initialized (placeholder)');
}

/**
 * Initialize 3D scene (placeholder)
 */
function initScene() {
    const canvas = document.getElementById('visualization-canvas');
    
    // Placeholder: Just fill with dark background
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    
    ctx.fillStyle = '#0a0e27';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw placeholder text
    ctx.fillStyle = '#4ecdc4';
    ctx.font = '20px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('3D 拓扑图 (Three.js 将在后续实现)', canvas.width / 2, canvas.height / 2);
    
    console.log('Scene initialized (placeholder)');
}

/**
 * Update statistics display
 */
function updateStatistics() {
    document.getElementById('total-packets').textContent = state.statistics.totalPackets;
    document.getElementById('total-bytes').textContent = state.statistics.totalBytes;
    document.getElementById('control-count').textContent = state.statistics.controlCount;
    document.getElementById('telemetry-count').textContent = state.statistics.telemetryCount;
}

/**
 * Handle incoming traffic event
 */
function handleTrafficEvent(data) {
    // Update statistics
    state.statistics.totalPackets++;
    state.statistics.totalBytes += data.packet_size || 0;
    
    if (data.type === 'Control') {
        state.statistics.controlCount++;
    } else if (data.type === 'Telemetry') {
        state.statistics.telemetryCount++;
    }
    
    // Update UI
    updateStatistics();
    
    // Create particles for traffic visualization
    if (particleSystem && sceneManager) {
        const fromComponent = sceneManager.getComponent(data.from);
        const toComponent = sceneManager.getComponent(data.to);
        
        if (fromComponent && toComponent) {
            const fromPos = fromComponent.mesh.position;
            const toPos = toComponent.mesh.position;
            
            // Determine particle color based on traffic type
            let particleColor = 0x4ecdc4; // Default cyan
            if (data.type === 'Control') {
                particleColor = 0xFF6B6B; // Warm red for control
            } else if (data.type === 'Telemetry') {
                particleColor = 0x4ECDC4; // Cool cyan for telemetry
            }
            
            // Create particles - more particles for better visibility
            const particleCount = Math.max(3, Math.floor(data.intensity * 15));
            particleSystem.createParticles(fromPos, toPos, particleCount, {
                color: particleColor,
                intensity: data.intensity,
                lifetime: 3000 + (data.intensity * 2000),
                size: 0.5 + (data.intensity * 0.5)
            });
        }
    }
    
    // Show info panel with event details
    showEventInfo(data);
}

/**
 * Reset statistics
 */
function resetStatistics() {
    state.statistics = {
        totalPackets: 0,
        totalBytes: 0,
        controlCount: 0,
        telemetryCount: 0
    };
    updateStatistics();
}

/**
 * Show event information in info panel
 */
function showEventInfo(data) {
    const infoPanel = document.getElementById('info-panel');
    const infoContent = document.getElementById('info-content');
    
    const html = `
        <div class="event-info">
            <p><strong>源：</strong> ${data.from}</p>
            <p><strong>目标：</strong> ${data.to}</p>
            <p><strong>类型：</strong> ${data.type}</p>
            <p><strong>强度：</strong> ${(data.intensity * 100).toFixed(1)}%</p>
            <p><strong>报文大小：</strong> ${data.packet_size} 字节</p>
            <p><strong>时间戳：</strong> ${data.timestamp}</p>
        </div>
    `;
    
    infoContent.innerHTML = html;
    infoPanel.classList.add('show');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        infoPanel.classList.remove('show');
    }, 5000);
}

/**
 * Show component information in info panel
 */
function showComponentInfo(name, component) {
    const infoPanel = document.getElementById('info-panel');
    const infoContent = document.getElementById('info-content');
    
    const html = `
        <div class="component-info">
            <p><strong>组件名称：</strong> ${name}</p>
            <p><strong>类型：</strong> ${component.type}</p>
            <p><strong>状态：</strong> ${component.status}</p>
            <p><strong>位置：</strong> (${component.position.x.toFixed(1)}, ${component.position.y.toFixed(1)}, ${component.position.z.toFixed(1)})</p>
            <p><strong>颜色：</strong> #${component.color.toString(16).padStart(6, '0').toUpperCase()}</p>
        </div>
    `;
    
    infoContent.innerHTML = html;
    infoPanel.classList.add('show');
    
    // Highlight component
    sceneManager.highlightComponent(name, true);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        infoPanel.classList.remove('show');
        sceneManager.highlightComponent(name, false);
    }, 5000);
}

/**
 * Send ping to server
 */
function sendPing() {
    if (socket && state.connected) {
        socket.emit('ping');
    }
}

/**
 * Start animation loop
 */
function startAnimationLoop() {
    const animate = () => {
        requestAnimationFrame(animate);
        
        // Update particle system
        if (particleSystem && !state.paused) {
            particleSystem.update();
        }
    };
    
    animate();
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', init);

// Send ping every 30 seconds to keep connection alive
setInterval(sendPing, 30000);
