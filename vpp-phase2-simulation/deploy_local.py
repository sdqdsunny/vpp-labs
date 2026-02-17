#!/usr/bin/env python3
"""
Local deployment script for VPP Phase 2 Simulation Framework.

This script:
1. Initializes the database
2. Installs dependencies
3. Starts the application
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(cmd, description):
    """Run a shell command and log the result."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"✓ {description} completed successfully")
        if result.stdout:
            logger.debug(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed")
        logger.error(f"Error: {e.stderr}")
        return False


def check_database_connection():
    """Check if database is accessible."""
    logger.info("Checking database connection...")
    
    try:
        import psycopg2
        from config import config
        
        # Parse connection string
        conn_str = config.DATABASE_URL
        if conn_str.startswith("postgresql://"):
            conn_str = conn_str.replace("postgresql://", "")
        
        # Try to connect
        conn = psycopg2.connect(conn_str)
        conn.close()
        logger.info("✓ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def check_redis_connection():
    """Check if Redis is accessible."""
    logger.info("Checking Redis connection...")
    
    try:
        import redis
        from config import config
        
        r = redis.from_url(config.REDIS_URL)
        r.ping()
        logger.info("✓ Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        return False


def install_dependencies():
    """Install Python dependencies."""
    logger.info("Installing Python dependencies...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    if not requirements_file.exists():
        logger.error(f"Requirements file not found: {requirements_file}")
        return False
    
    # Use --break-system-packages flag for macOS Homebrew Python
    cmd = [sys.executable, "-m", "pip", "install", "--break-system-packages", "-r", str(requirements_file)]
    return run_command(cmd, "Install dependencies")


def initialize_database():
    """Initialize database tables."""
    logger.info("Initializing database...")
    
    try:
        from utils.database import init_db
        init_db()
        logger.info("✓ Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return False


def create_logs_directory():
    """Create logs directory if it doesn't exist."""
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    logger.info(f"✓ Logs directory ready: {logs_dir}")


def main():
    """Main deployment function."""
    logger.info("=" * 60)
    logger.info("VPP Phase 2 Simulation Framework - Local Deployment")
    logger.info("=" * 60)
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Step 1: Create logs directory
    logger.info("\n[Step 1/5] Creating logs directory...")
    create_logs_directory()
    
    # Step 2: Install dependencies
    logger.info("\n[Step 2/5] Installing dependencies...")
    if not install_dependencies():
        logger.error("Failed to install dependencies")
        return False
    
    # Step 3: Check database connection
    logger.info("\n[Step 3/5] Checking database connection...")
    if not check_database_connection():
        logger.error("Database is not accessible. Make sure PostgreSQL is running.")
        return False
    
    # Step 4: Check Redis connection
    logger.info("\n[Step 4/5] Checking Redis connection...")
    if not check_redis_connection():
        logger.error("Redis is not accessible. Make sure Redis is running.")
        return False
    
    # Step 5: Initialize database
    logger.info("\n[Step 5/5] Initializing database...")
    if not initialize_database():
        logger.error("Failed to initialize database")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ Deployment preparation completed successfully!")
    logger.info("=" * 60)
    logger.info("\nYou can now start the application with:")
    logger.info("  python3 app.py")
    logger.info("\nOr run tests with:")
    logger.info("  python3 -m pytest tests/ -v")
    logger.info("=" * 60)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
