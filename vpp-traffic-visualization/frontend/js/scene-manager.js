/**
 * Scene Manager for VPP Traffic Visualization
 * 
 * Manages Three.js scene, camera, renderer, and topology rendering
 */

class SceneManager {
    /**
     * Initialize the scene manager
     * 
     * @param {HTMLCanvasElement} canvas - The canvas element to render to
     */
    constructor(canvas) {
        this.canvas = canvas;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.components = {};
        this.connections = [];
        this.animationId = null;
        
        this.initScene();
        this.initCamera();
        this.initRenderer();
        this.initLighting();
        this.setupEventListeners();
        
        console.log('SceneManager initialized');
    }
    
    /**
     * Initialize Three.js scene
     */
    initScene() {
        this.scene = new THREE.Scene();
        // Set dark background color
        this.scene.background = new THREE.Color(0x0a0e27);
        this.scene.fog = new THREE.Fog(0x0a0e27, 100, 500);
    }
    
    /**
     * Initialize camera
     */
    initCamera() {
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;
        const aspect = width / height;
        
        this.camera = new THREE.PerspectiveCamera(
            75,           // Field of view
            aspect,       // Aspect ratio
            0.1,          // Near clipping plane
            1000          // Far clipping plane
        );
        
        // Position camera to view the topology
        this.camera.position.set(0, 20, 30);
        this.camera.lookAt(0, 0, 0);
    }
    
    /**
     * Initialize WebGL renderer
     */
    initRenderer() {
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
            alpha: true
        });
        
        this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFShadowShadowMap;
    }
    
    /**
     * Initialize lighting
     */
    initLighting() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);
        
        // Directional light (sun)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(50, 50, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.left = -100;
        directionalLight.shadow.camera.right = 100;
        directionalLight.shadow.camera.top = 100;
        directionalLight.shadow.camera.bottom = -100;
        this.scene.add(directionalLight);
        
        // Point light for accent
        const pointLight = new THREE.PointLight(0x4ecdc4, 0.5);
        pointLight.position.set(0, 30, 0);
        this.scene.add(pointLight);
    }
    
    /**
     * Setup event listeners for window resize and interactions
     */
    setupEventListeners() {
        window.addEventListener('resize', () => this.onWindowResize());
    }
    
    /**
     * Handle window resize
     */
    onWindowResize() {
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }
    
    /**
     * Add a component node to the scene
     * 
     * @param {string} name - Component name
     * @param {Object} position - Position {x, y, z}
     * @param {string} color - Component color (hex)
     * @param {string} type - Component type
     */
    addComponent(name, position, color, type = 'default') {
        // Create component geometry
        const geometry = new THREE.SphereGeometry(2, 32, 32);
        const material = new THREE.MeshStandardMaterial({
            color: color,
            metalness: 0.3,
            roughness: 0.4,
            emissive: color,
            emissiveIntensity: 0.2
        });
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(position.x, position.y, position.z);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        
        // Add label
        const label = this.createLabel(name);
        label.position.copy(mesh.position);
        label.position.y += 4;
        
        // Store component info
        this.components[name] = {
            mesh: mesh,
            label: label,
            position: position,
            color: color,
            type: type,
            status: 'online'
        };
        
        this.scene.add(mesh);
        this.scene.add(label);
        
        console.log(`Added component: ${name} at (${position.x}, ${position.y}, ${position.z})`);
    }
    
    /**
     * Create a text label for a component
     * 
     * @param {string} text - Label text
     * @returns {THREE.Group} - Group containing the label
     */
    createLabel(text) {
        const canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 64;
        
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#4ecdc4';
        ctx.font = 'bold 32px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text, 128, 32);
        
        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.MeshBasicMaterial({ map: texture });
        const geometry = new THREE.PlaneGeometry(4, 1);
        const mesh = new THREE.Mesh(geometry, material);
        
        return mesh;
    }
    
    /**
     * Add a connection line between two components
     * 
     * @param {string} fromName - Source component name
     * @param {string} toName - Target component name
     * @param {string} color - Line color (hex)
     */
    addConnection(fromName, toName, color = 0x4ecdc4) {
        const fromComponent = this.components[fromName];
        const toComponent = this.components[toName];
        
        if (!fromComponent || !toComponent) {
            console.warn(`Cannot create connection: ${fromName} -> ${toName}`);
            return;
        }
        
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array([
            fromComponent.mesh.position.x, fromComponent.mesh.position.y, fromComponent.mesh.position.z,
            toComponent.mesh.position.x, toComponent.mesh.position.y, toComponent.mesh.position.z
        ]);
        
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        
        const material = new THREE.LineBasicMaterial({
            color: color,
            linewidth: 2,
            transparent: true,
            opacity: 0.6
        });
        
        const line = new THREE.Line(geometry, material);
        
        this.connections.push({
            line: line,
            from: fromName,
            to: toName,
            color: color
        });
        
        this.scene.add(line);
        
        console.log(`Added connection: ${fromName} -> ${toName}`);
    }
    
    /**
     * Initialize default topology with VPP components
     */
    initializeTopology() {
        // Define component positions in a circular layout
        const components = [
            {
                name: 'Master',
                position: { x: 0, y: 0, z: 0 },
                color: 0xFF6B6B,
                type: 'coordinator'
            },
            {
                name: 'Power_01',
                position: { x: 15, y: 0, z: 0 },
                color: 0xFFA500,
                type: 'power'
            },
            {
                name: 'Storage_01',
                position: { x: -7.5, y: 0, z: 13 },
                color: 0x4ECDC4,
                type: 'storage'
            },
            {
                name: 'Demand_01',
                position: { x: -7.5, y: 0, z: -13 },
                color: 0x95E1D3,
                type: 'demand'
            }
        ];
        
        // Add all components
        components.forEach(comp => {
            this.addComponent(comp.name, comp.position, comp.color, comp.type);
        });
        
        // Add connections
        this.addConnection('Master', 'Power_01', 0x4ecdc4);
        this.addConnection('Master', 'Storage_01', 0x4ecdc4);
        this.addConnection('Master', 'Demand_01', 0x4ecdc4);
        this.addConnection('Power_01', 'Storage_01', 0x95E1D3);
        this.addConnection('Storage_01', 'Demand_01', 0x95E1D3);
        
        console.log('Topology initialized with 4 components');
    }
    
    /**
     * Get component by name
     * 
     * @param {string} name - Component name
     * @returns {Object} - Component object or null
     */
    getComponent(name) {
        return this.components[name] || null;
    }
    
    /**
     * Update component status
     * 
     * @param {string} name - Component name
     * @param {string} status - New status ('online' or 'offline')
     */
    updateComponentStatus(name, status) {
        const component = this.components[name];
        if (!component) return;
        
        component.status = status;
        
        if (status === 'offline') {
            component.mesh.material.emissiveIntensity = 0;
            component.mesh.material.opacity = 0.5;
        } else {
            component.mesh.material.emissiveIntensity = 0.2;
            component.mesh.material.opacity = 1;
        }
    }
    
    /**
     * Highlight a component
     * 
     * @param {string} name - Component name
     * @param {boolean} highlight - Whether to highlight
     */
    highlightComponent(name, highlight = true) {
        const component = this.components[name];
        if (!component) return;
        
        if (highlight) {
            component.mesh.material.emissiveIntensity = 0.5;
            component.mesh.scale.set(1.2, 1.2, 1.2);
        } else {
            component.mesh.material.emissiveIntensity = 0.2;
            component.mesh.scale.set(1, 1, 1);
        }
    }
    
    /**
     * Reset camera to default position
     */
    resetCamera() {
        this.camera.position.set(0, 20, 30);
        this.camera.lookAt(0, 0, 0);
    }
    
    /**
     * Rotate camera around the scene
     * 
     * @param {number} deltaX - Horizontal rotation delta
     * @param {number} deltaY - Vertical rotation delta
     */
    rotateCamera(deltaX, deltaY) {
        const radius = Math.sqrt(
            this.camera.position.x ** 2 +
            this.camera.position.y ** 2 +
            this.camera.position.z ** 2
        );
        
        let theta = Math.atan2(this.camera.position.z, this.camera.position.x);
        let phi = Math.acos(this.camera.position.y / radius);
        
        theta += deltaX * 0.01;
        phi += deltaY * 0.01;
        
        // Clamp phi to avoid flipping
        phi = Math.max(0.1, Math.min(Math.PI - 0.1, phi));
        
        this.camera.position.x = radius * Math.sin(phi) * Math.cos(theta);
        this.camera.position.y = radius * Math.cos(phi);
        this.camera.position.z = radius * Math.sin(phi) * Math.sin(theta);
        
        this.camera.lookAt(0, 0, 0);
    }
    
    /**
     * Zoom camera
     * 
     * @param {number} delta - Zoom delta (positive = zoom in, negative = zoom out)
     */
    zoomCamera(delta) {
        const direction = this.camera.position.clone().normalize();
        const distance = this.camera.position.length();
        const newDistance = Math.max(10, Math.min(100, distance - delta * 2));
        
        this.camera.position.copy(direction.multiplyScalar(newDistance));
        this.camera.lookAt(0, 0, 0);
    }
    
    /**
     * Pan camera
     * 
     * @param {number} deltaX - Horizontal pan
     * @param {number} deltaY - Vertical pan
     */
    panCamera(deltaX, deltaY) {
        const right = new THREE.Vector3();
        const up = new THREE.Vector3(0, 1, 0);
        
        this.camera.getWorldDirection(right);
        right.cross(up).normalize();
        
        up.crossVectors(right, this.camera.getWorldDirection(new THREE.Vector3()));
        
        this.camera.position.addScaledVector(right, -deltaX * 0.1);
        this.camera.position.addScaledVector(up, deltaY * 0.1);
    }
    
    /**
     * Start rendering loop
     */
    startRender() {
        const animate = () => {
            this.animationId = requestAnimationFrame(animate);
            
            // Rotate components slightly for visual effect
            Object.values(this.components).forEach(comp => {
                comp.mesh.rotation.x += 0.001;
                comp.mesh.rotation.y += 0.002;
            });
            
            this.renderer.render(this.scene, this.camera);
        };
        
        animate();
    }
    
    /**
     * Stop rendering loop
     */
    stopRender() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }
    
    /**
     * Get raycaster for mouse picking
     * 
     * @param {number} mouseX - Normalized mouse X (-1 to 1)
     * @param {number} mouseY - Normalized mouse Y (-1 to 1)
     * @returns {THREE.Raycaster} - Raycaster object
     */
    getRaycaster(mouseX, mouseY) {
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2(mouseX, mouseY);
        raycaster.setFromCamera(mouse, this.camera);
        return raycaster;
    }
    
    /**
     * Get intersected objects at mouse position
     * 
     * @param {number} mouseX - Normalized mouse X (-1 to 1)
     * @param {number} mouseY - Normalized mouse Y (-1 to 1)
     * @returns {Array} - Array of intersected objects
     */
    getIntersectedObjects(mouseX, mouseY) {
        const raycaster = this.getRaycaster(mouseX, mouseY);
        const objects = Object.values(this.components).map(comp => comp.mesh);
        return raycaster.intersectObjects(objects);
    }
    
    /**
     * Dispose of resources
     */
    dispose() {
        this.stopRender();
        
        // Dispose geometries and materials
        Object.values(this.components).forEach(comp => {
            comp.mesh.geometry.dispose();
            comp.mesh.material.dispose();
            comp.label.geometry.dispose();
            comp.label.material.dispose();
        });
        
        this.connections.forEach(conn => {
            conn.line.geometry.dispose();
            conn.line.material.dispose();
        });
        
        this.renderer.dispose();
    }
}
