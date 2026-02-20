/**
 * Camera Controller for VPP Traffic Visualization
 * 
 * Handles camera interactions: rotation, zoom, pan, and reset
 */

class CameraController {
    /**
     * Initialize camera controller
     * 
     * @param {SceneManager} sceneManager - The scene manager instance
     * @param {HTMLElement} canvas - The canvas element
     */
    constructor(sceneManager, canvas) {
        this.sceneManager = sceneManager;
        this.canvas = canvas;
        
        this.isDragging = false;
        this.previousMousePosition = { x: 0, y: 0 };
        this.rotationSpeed = 1.0;
        this.zoomSpeed = 1.0;
        this.panSpeed = 1.0;
        
        this.setupEventListeners();
        
        console.log('CameraController initialized');
    }
    
    /**
     * Setup event listeners for mouse and keyboard interactions
     */
    setupEventListeners() {
        // Mouse events
        this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
        this.canvas.addEventListener('wheel', (e) => this.onMouseWheel(e));
        
        // Touch events for mobile
        this.canvas.addEventListener('touchstart', (e) => this.onTouchStart(e));
        this.canvas.addEventListener('touchmove', (e) => this.onTouchMove(e));
        this.canvas.addEventListener('touchend', (e) => this.onTouchEnd(e));
        
        // Keyboard events
        document.addEventListener('keydown', (e) => this.onKeyDown(e));
    }
    
    /**
     * Handle mouse down event
     */
    onMouseDown(event) {
        this.isDragging = true;
        this.previousMousePosition = { x: event.clientX, y: event.clientY };
    }
    
    /**
     * Handle mouse move event
     */
    onMouseMove(event) {
        if (!this.isDragging) return;
        
        const deltaX = event.clientX - this.previousMousePosition.x;
        const deltaY = event.clientY - this.previousMousePosition.y;
        
        // Determine interaction type based on mouse button
        if (event.buttons === 1) {
            // Left button: rotate
            this.sceneManager.rotateCamera(deltaX * this.rotationSpeed, deltaY * this.rotationSpeed);
        } else if (event.buttons === 2) {
            // Right button: pan
            this.sceneManager.panCamera(deltaX * this.panSpeed, deltaY * this.panSpeed);
        }
        
        this.previousMousePosition = { x: event.clientX, y: event.clientY };
    }
    
    /**
     * Handle mouse up event
     */
    onMouseUp(event) {
        this.isDragging = false;
    }
    
    /**
     * Handle mouse wheel event for zoom
     */
    onMouseWheel(event) {
        event.preventDefault();
        
        const delta = event.deltaY > 0 ? 1 : -1;
        this.sceneManager.zoomCamera(delta * this.zoomSpeed);
    }
    
    /**
     * Handle touch start event
     */
    onTouchStart(event) {
        if (event.touches.length === 1) {
            this.isDragging = true;
            this.previousMousePosition = {
                x: event.touches[0].clientX,
                y: event.touches[0].clientY
            };
        } else if (event.touches.length === 2) {
            // Store initial distance for pinch zoom
            this.initialTouchDistance = this.getTouchDistance(event.touches);
        }
    }
    
    /**
     * Handle touch move event
     */
    onTouchMove(event) {
        if (event.touches.length === 1 && this.isDragging) {
            const deltaX = event.touches[0].clientX - this.previousMousePosition.x;
            const deltaY = event.touches[0].clientY - this.previousMousePosition.y;
            
            this.sceneManager.rotateCamera(deltaX * this.rotationSpeed, deltaY * this.rotationSpeed);
            
            this.previousMousePosition = {
                x: event.touches[0].clientX,
                y: event.touches[0].clientY
            };
        } else if (event.touches.length === 2) {
            // Pinch zoom
            const currentDistance = this.getTouchDistance(event.touches);
            const delta = currentDistance - this.initialTouchDistance;
            this.sceneManager.zoomCamera(-delta * 0.01 * this.zoomSpeed);
            this.initialTouchDistance = currentDistance;
        }
    }
    
    /**
     * Handle touch end event
     */
    onTouchEnd(event) {
        if (event.touches.length === 0) {
            this.isDragging = false;
        }
    }
    
    /**
     * Get distance between two touch points
     */
    getTouchDistance(touches) {
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    /**
     * Handle keyboard events
     */
    onKeyDown(event) {
        switch (event.key) {
            case 'r':
            case 'R':
                // Reset camera
                this.sceneManager.resetCamera();
                break;
            case '+':
            case '=':
                // Zoom in
                this.sceneManager.zoomCamera(-1 * this.zoomSpeed);
                break;
            case '-':
            case '_':
                // Zoom out
                this.sceneManager.zoomCamera(1 * this.zoomSpeed);
                break;
            case 'ArrowUp':
                // Pan up
                this.sceneManager.panCamera(0, 1 * this.panSpeed);
                break;
            case 'ArrowDown':
                // Pan down
                this.sceneManager.panCamera(0, -1 * this.panSpeed);
                break;
            case 'ArrowLeft':
                // Pan left
                this.sceneManager.panCamera(1 * this.panSpeed, 0);
                break;
            case 'ArrowRight':
                // Pan right
                this.sceneManager.panCamera(-1 * this.panSpeed, 0);
                break;
        }
    }
    
    /**
     * Set rotation speed
     */
    setRotationSpeed(speed) {
        this.rotationSpeed = speed;
    }
    
    /**
     * Set zoom speed
     */
    setZoomSpeed(speed) {
        this.zoomSpeed = speed;
    }
    
    /**
     * Set pan speed
     */
    setPanSpeed(speed) {
        this.panSpeed = speed;
    }
    
    /**
     * Reset to default speeds
     */
    resetSpeeds() {
        this.rotationSpeed = 1.0;
        this.zoomSpeed = 1.0;
        this.panSpeed = 1.0;
    }
}
