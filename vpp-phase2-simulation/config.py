"""
Configuration management for VPP Phase 2 Simulation Framework.

Handles environment-based configuration for database, logging, and simulation parameters.
"""

import os
from typing import Optional


class Config:
    """Base configuration class."""

    # Application
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    TESTING = os.getenv("TESTING", "False").lower() == "true"
    ENV = os.getenv("ENV", "development")

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///vpp_phase2_sim.db"
    )
    DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "40"))
    DATABASE_POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "3600"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "json"  # JSON structured logging
    LOG_FILE = os.getenv("LOG_FILE", "logs/vpp_phase2_sim.log")

    # Simulation Parameters
    SIMULATION_TIME_STEP = float(os.getenv("SIMULATION_TIME_STEP", "1.0"))  # seconds
    MAX_DEVICES = int(os.getenv("MAX_DEVICES", "10000"))
    MAX_SCENARIOS = int(os.getenv("MAX_SCENARIOS", "100"))
    METRICS_RETENTION_DAYS = int(os.getenv("METRICS_RETENTION_DAYS", "30"))

    # Performance
    POWER_FLOW_TIMEOUT_MS = int(os.getenv("POWER_FLOW_TIMEOUT_MS", "500"))
    DASHBOARD_UPDATE_INTERVAL_MS = int(os.getenv("DASHBOARD_UPDATE_INTERVAL_MS", "500"))
    METRICS_AGGREGATION_INTERVAL_S = int(os.getenv("METRICS_AGGREGATION_INTERVAL_S", "60"))

    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8001"))
    API_WORKERS = int(os.getenv("API_WORKERS", "4"))

    # Prometheus Metrics
    PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "True").lower() == "true"
    PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "8002"))

    # VPP Master Integration
    VPP_MASTER_URL = os.getenv("VPP_MASTER_URL", "http://localhost:8000")
    VPP_MASTER_API_KEY = os.getenv("VPP_MASTER_API_KEY", "")

    # Network Simulation
    NETWORK_SIMULATION_ENABLED = os.getenv("NETWORK_SIMULATION_ENABLED", "True").lower() == "true"
    DEFAULT_LATENCY_MS = float(os.getenv("DEFAULT_LATENCY_MS", "20"))
    DEFAULT_PACKET_LOSS_RATE = float(os.getenv("DEFAULT_PACKET_LOSS_RATE", "0.01"))


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    ENV = "development"
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    ENV = "production"
    LOG_LEVEL = "INFO"


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    ENV = "testing"
    DATABASE_URL = "sqlite:///:memory:"
    REDIS_URL = "redis://localhost:6379/1"
    LOG_LEVEL = "DEBUG"


def get_config() -> Config:
    """Get configuration based on environment."""
    env = os.getenv("ENV", "development").lower()

    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()


# Export current config
config = get_config()
