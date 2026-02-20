/**
 * Particle System for VPP Traffic Visualization
 * 
 * Manages particle creation, animation, and rendering
 */

class Particle {
    /**
     * Create a particle
     * 
     * @param {THREE.Vector3} startPos - Starting position
     * @param {THREE.Vector3} endPos - Ending position
     * @param {Object} options - Particle options
     */
    constructor(startPos, endPos, options = {}) {
        this.startPos = startPos.clone();
        this.endPos = endPos.clone();
        this.currentPos = startPos.clone();
        
        this.size = options.size || 0.5;
        this.color = options.color || 0x4ecdc4;
        this.intensity = options.intensity || 0.5;
        this.lifetime = options.lifetime || 2000; // milliseconds
        this.createdAt = Date.now();
        this.speed = options.speed || 1.0;
        
        this.mesh = null;
        this.isActive = true;
        this.progress = 0; // 0 to 1
        
        this.createMesh();
    }
    
    /**
     * Create the mesh for this particle
     */
    createMesh() {
        const geometry = new THREE.SphereGeometry(this.size, 8, 8);
        const material = new THREE.MeshBasicMaterial({
            color: this.color,
            transparent: true,
            opacity: 1.0
        });
        
        this.mesh = new THREE.Mesh(geometry, material);
        this.mesh.position.copy(this.currentPos);
    }
    
    /**
     * Update particle position and state
     * 
     * @param {number} deltaTime - Time elapsed since last update (ms)     */
    update(deltaTime) {
        if (!this.isActive) return;
        
        const elapsed = Date.now() - this.createdAt;
        this.progress = Math.min(elapsed / this.lifetime, 1.0);
        
        // Linear interpolation along the path
        this.currentPos.lerpVectors(this.startPos, this.endPos, this.progress);
        this.mesh.position.copy(this.currentPos);
        
        // Fade out as particle reaches end
        const opacity = Math.max(0, 1.0 - this.progress);
        this.mesh.material.opacity = opacity;
        
        // Scale down as particle fades
        const scale = Math.max(0.1, 1.0 - this.progress * 0.5);
        this.mesh.scale.set(scale, scale, scale);
        
        // Mark as inactive when lifetime expires
        if (this.progress >= 1.0) {
            this.isActive = false;
        }
    }
    
    /**
     * Reset particle for reuse
     */
    reset(startPos, endPos, options = {}) {
        this.startPos.copy(startPos);
        this.endPos.copy(endPos);
        this.currentPos.copy(startPos);
        
        this.size = options.size || 0.5;
        this.color = options.color || 0x4ecdc4;
        this.intensity = options.intensity || 0.5;
        this.lifetime = options.lifetime || 2000;
        this.createdAt = Date.now();
        this.speed = options.speed || 1.0;
        
        this.isActive = true;
        this.progress = 0;
        
        // Update mesh
        this.mesh.material.color.setHex(this.color);
        this.mesh.material.opacity = 1.0;
        this.mesh.scale.set(1, 1, 1);
        this.mesh.position.copy(this.currentPos);
    }
    
    /**
     * Dispose of particle resources
     */
    dispose() {
        if (this.mesh) {
            this.mesh.geometry.dispose();
            this.mesh.material.dispose();
        }
    }
}

class ParticlePool {
    /**
     * Create a particle pool
     * 
     * @param {number} maxSize - Maximum number of particles in pool
     */
    constructor(maxSize = 10000) {
        this.maxSize = maxSize;
        this.particles = [];
        this.activeParticles = [];
        this.inactiveParticles = [];
        
        // Pre-allocate particles
        for (let i = 0; i < Math.min(maxSize, 1000); i++) {
            const particle = new Particle(
                new THREE.Vector3(0, 0, 0),
                new THREE.Vector3(0, 0, 0)
            );
            this.particles.push(particle);
            this.inactiveParticles.push(particle);
        }
        
        console.log(`ParticlePool initialized with ${this.particles.length} particles`);
    }
    
    /**
     * Get a particle from the pool
     * 
     * @param {THREE.Vector3} startPos - Starting position
     * @param {THREE.Vector3} endPos - Ending position
     * @param {Object} options - Particle options
     * @returns {Particle} - Particle object
     */
    acquire(startPos, endPos, options = {}) {
        let particle;
        
        if (this.inactiveParticles.length > 0) {
            // Reuse inactive particle
            particle = this.inactiveParticles.pop();
            particle.reset(startPos, endPos, options);
        } else if (this.particles.length < this.maxSize) {
            // Create new particle if under limit
            particle = new Particle(startPos, endPos, options);
            this.particles.push(particle);
        } else {
            // Pool is full, reuse oldest active particle
            particle = this.activeParticles.shift();
            particle.reset(startPos, endPos, options);
        }
        
        this.activeParticles.push(particle);
        return particle;
    }
    
    /**
     * Release a particle back to the pool
     * 
     * @param {Particle} particle - Particle to release
     */
    release(particle) {
        const index = this.activeParticles.indexOf(particle);
        if (index > -1) {
            this.activeParticles.splice(index, 1);
            this.inactiveParticles.push(particle);
        }
    }
    
    /**
     * Update all active particles
     * 
     * @param {number} deltaTime - Time elapsed since last update (ms)
     */
    update(deltaTime) {
        for (let i = this.activeParticles.length - 1; i >= 0; i--) {
            const particle = this.activeParticles[i];
            particle.update(deltaTime);
            
            if (!particle.isActive) {
                this.release(particle);
            }
        }
    }
    
    /**
     * Get all active particle meshes
     * 
     * @returns {Array} - Array of THREE.Mesh objects
     */
    getActiveMeshes() {
        return this.activeParticles.map(p => p.mesh);
    }
    
    /**
     * Get number of active particles
     * 
     * @returns {number} - Number of active particles
     */
    getActiveCount() {
        return this.activeParticles.length;
    }
    
    /**
     * Clear all particles
     */
    clear() {
        this.activeParticles = [];
        this.inactiveParticles = this.particles.slice();
    }
    
    /**
     * Dispose of all particles
     */
    dispose() {
        this.particles.forEach(p => p.dispose());
        this.particles = [];
        this.activeParticles = [];
        this.inactiveParticles = [];
    }
}

class ParticleSystem {
    /**
     * Initialize particle system
     * 
     * @param {THREE.Scene} scene - Three.js scene
     * @param {number} maxParticles - Maximum number of particles
     */
    constructor(scene, maxParticles = 10000) {
        this.scene = scene;
        this.pool = new ParticlePool(maxParticles);
        this.lastUpdateTime = Date.now();
        
        // Add all particle meshes to scene
        this.pool.particles.forEach(p => {
            this.scene.add(p.mesh);
        });
        
        console.log('ParticleSystem initialized');
    }
    
    /**
     * Create a particle
     * 
     * @param {THREE.Vector3} fromPos - Starting position
     * @param {THREE.Vector3} toPos - Ending position
     * @param {Object} options - Particle options
     * @returns {Particle} - Created particle
     */
    createParticle(fromPos, toPos, options = {}) {
        return this.pool.acquire(fromPos, toPos, options);
    }
    
    /**
     * Create multiple particles
     * 
     * @param {THREE.Vector3} fromPos - Starting position
     * @param {THREE.Vector3} toPos - Ending position
     * @param {number} count - Number of particles to create
     * @param {Object} options - Particle options
     */
    createParticles(fromPos, toPos, count = 1, options = {}) {
        for (let i = 0; i < count; i++) {
            // Add slight randomness to particle positions
            const randomOffset = new THREE.Vector3(
                (Math.random() - 0.5) * 2,
                (Math.random() - 0.5) * 2,
                (Math.random() - 0.5) * 2
            );
            
            const startPos = fromPos.clone().add(randomOffset);
            const endPos = toPos.clone().add(randomOffset);
            
            this.createParticle(startPos, endPos, options);
        }
    }
    
    /**
     * Update particle system
     */
    update() {
        const now = Date.now();
        const deltaTime = now - this.lastUpdateTime;
        this.lastUpdateTime = now;
        
        this.pool.update(deltaTime);
    }
    
    /**
     * Get number of active particles
     * 
     * @returns {number} - Number of active particles
     */
    getActiveParticleCount() {
        return this.pool.getActiveCount();
    }
    
    /**
     * Clear all particles
     */
    clear() {
        this.pool.clear();
    }
    
    /**
     * Dispose of particle system
     */
    dispose() {
        this.pool.dispose();
    }
}
