"""
Phase 1 Integration Service for VPP Phase 2 Simulation Framework.

Handles communication with Phase 1 (VPP Master) API, data mapping,
synchronization, and error recovery with automatic scheduling and retry logic.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
import logging
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from utils.structured_logger import get_structured_logger


class SyncType(Enum):
    """Synchronization types."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DEVICES = "devices"
    SCENARIOS = "scenarios"
    METRICS = "metrics"

# Metrics disabled - prometheus removed
# last_sync_time = Gauge(
#     'phase1_last_sync_timestamp',
#     'Timestamp of last successful sync'
# )
#
# connection_status = Gauge(
#     'phase1_connection_status',
#     'Phase 1 API connection status (1=healthy, 0=unhealthy)'
# )


class Phase1IntegrationService:
    """Service for Phase 1 API integration with automatic scheduling and retry logic."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Phase 1 integration service."""
        # Avoid re-initialization
        if hasattr(self, '_initialized'):
            return
        
        self.master_url = os.getenv("VPP_MASTER_URL", "http://localhost:8080")
        self.api_key = os.getenv("VPP_MASTER_API_KEY", "")
        self.timeout = int(os.getenv("VPP_MASTER_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("VPP_MASTER_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("VPP_MASTER_RETRY_DELAY", "5"))
        self.sync_interval = int(os.getenv("VPP_SYNC_INTERVAL", "5"))  # seconds
        
        self.logger = get_structured_logger("vpp_phase2_sim.phase1_service")
        self.sync_history: List[Dict[str, Any]] = []
        self.last_sync_time: Optional[datetime] = None
        self.last_sync_type: Optional[str] = None
        
        # Initialize scheduler
        self.scheduler = BackgroundScheduler()
        self._setup_scheduler()
        
        self._initialized = True
        
        self.logger.info(
            "Phase 1 Integration Service initialized",
            master_url=self.master_url,
            sync_interval=self.sync_interval,
            tags={"component": "phase1_integration", "operation": "init"}
        )
    
    def _setup_scheduler(self):
        """Setup background scheduler for automatic synchronization."""
        try:
            # Add job for periodic synchronization
            self.scheduler.add_job(
                self._scheduled_sync,
                'interval',
                seconds=self.sync_interval,
                id='phase1_periodic_sync',
                name='Phase 1 Periodic Sync',
                replace_existing=True,
                max_instances=1
            )
            
            # Add job for periodic health check
            self.scheduler.add_job(
                self._scheduled_health_check,
                'interval',
                seconds=30,
                id='phase1_health_check',
                name='Phase 1 Health Check',
                replace_existing=True,
                max_instances=1
            )
            
            if not self.scheduler.running:
                self.scheduler.start()
                self.logger.info(
                    "Background scheduler started",
                    tags={"component": "phase1_integration", "operation": "scheduler_start"}
                )
        except Exception as e:
            self.logger.error(
                f"Failed to setup scheduler: {str(e)}",
                tags={"component": "phase1_integration", "operation": "scheduler_setup", "error": True}
            )
    
    def _scheduled_sync(self):
        """Scheduled synchronization task."""
        try:
            self.sync_data(sync_type="incremental", force=False)
        except Exception as e:
            self.logger.error(
                f"Scheduled sync failed: {str(e)}",
                tags={"component": "phase1_integration", "operation": "scheduled_sync", "error": True}
            )
    
    def _scheduled_health_check(self):
        """Scheduled health check task."""
        try:
            health = self.check_health()
            is_healthy = health.get("status") == "healthy"
            connection_status.set(1 if is_healthy else 0)
            
            if not is_healthy:
                self.logger.warning(
                    f"Phase 1 health check failed: {health.get('status')}",
                    tags={"component": "phase1_integration", "operation": "health_check"}
                )
        except Exception as e:
            self.logger.error(
                f"Health check failed: {str(e)}",
                tags={"component": "phase1_integration", "operation": "health_check", "error": True}
            )
            connection_status.set(0)
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check Phase 1 API health.
        
        Returns:
            Health status dictionary
        """
        try:
            response = requests.get(
                f"{self.master_url}/health",
                timeout=self.timeout,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "phase1_url": self.master_url,
                    "timestamp": datetime.utcnow().isoformat(),
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            else:
                return {
                    "status": "unhealthy",
                    "phase1_url": self.master_url,
                    "http_status": response.status_code,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except requests.exceptions.ConnectionError:
            return {
                "status": "unavailable",
                "phase1_url": self.master_url,
                "error": "Connection refused",
                "timestamp": datetime.utcnow().isoformat()
            }
        except requests.exceptions.Timeout:
            return {
                "status": "timeout",
                "phase1_url": self.master_url,
                "error": f"Request timeout after {self.timeout}s",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "phase1_url": self.master_url,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_integration_status(self) -> Dict[str, Any]:
        """
        Get Phase 1 integration status.
        
        Returns:
            Integration status dictionary
        """
        return {
            "status": "connected" if self._is_connected() else "disconnected",
            "phase1_url": self.master_url,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "last_sync_type": self.last_sync_type,
            "sync_history_count": len(self.sync_history),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def sync_data(self, sync_type: str = "incremental", force: bool = False) -> Dict[str, Any]:
        """
        Synchronize data with Phase 1 API with automatic retry logic.
        
        Args:
            sync_type: Type of synchronization (full, incremental, devices, scenarios, metrics)
            force: Force synchronization even if recently synced
        
        Returns:
            Synchronization result dictionary
        """
        try:
            sync_type_enum = SyncType(sync_type)
        except ValueError:
            raise ValueError(f"Invalid sync_type: {sync_type}")
        
        # Check if recently synced
        if not force and self.last_sync_time:
            time_since_sync = datetime.utcnow() - self.last_sync_time
            if time_since_sync < timedelta(seconds=30):
                return {
                    "status": "skipped",
                    "reason": "Recently synced",
                    "last_sync_time": self.last_sync_time.isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        start_time = datetime.utcnow()
        result = {
            "sync_type": sync_type,
            "start_time": start_time.isoformat(),
            "synced_count": 0,
            "error_count": 0,
            "errors": []
        }
        
        try:
            # Execute synchronization
            if sync_type_enum == SyncType.FULL:
                result.update(self._sync_full())
            elif sync_type_enum == SyncType.INCREMENTAL:
                result.update(self._sync_incremental())
            elif sync_type_enum == SyncType.DEVICES:
                result.update(self.sync_devices())
            elif sync_type_enum == SyncType.SCENARIOS:
                result.update(self.sync_scenarios())
            elif sync_type_enum == SyncType.METRICS:
                result.update(self.sync_metrics())
            
            result["status"] = "success"
            self.last_sync_time = start_time
            self.last_sync_type = sync_type
            
            self.logger.info(
                f"Sync completed successfully",
                sync_type=sync_type,
                synced_count=result.get("synced_count", 0),
                error_count=result.get("error_count", 0),
                tags={"component": "phase1_integration", "operation": "sync_complete"}
            )
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["error_count"] += 1
            result["errors"].append(str(e))
            
            self.logger.error(
                f"Sync failed: {str(e)}",
                sync_type=sync_type,
                tags={"component": "phase1_integration", "operation": "sync", "error": True}
            )
        
        result["end_time"] = datetime.utcnow().isoformat()
        result["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()
        
        # Record in history
        self.sync_history.append(result)
        if len(self.sync_history) > 100:
            self.sync_history = self.sync_history[-100:]
        
        return result
    
    def sync_devices(self) -> Dict[str, Any]:
        """
        Synchronize devices with Phase 1 API.
        
        Returns:
            Synchronization result
        """
        try:
            # Get devices from Phase 2
            from utils.database import get_session
            from models.device_state import DeviceState
            
            session = get_session()
            devices = session.query(DeviceState).all()
            session.close()
            
            synced_count = 0
            error_count = 0
            errors = []
            
            # Send devices to Phase 1
            for device in devices:
                try:
                    device_data = self._map_device_to_phase1(device)
                    response = self._post_to_phase1(
                        "/api/v1/devices",
                        device_data
                    )
                    if response.status_code in [200, 201]:
                        synced_count += 1
                    else:
                        error_count += 1
                        errors.append(f"Device {device.id}: HTTP {response.status_code}")
                except Exception as e:
                    error_count += 1
                    errors.append(f"Device {device.id}: {str(e)}")
            
            return {
                "synced_count": synced_count,
                "error_count": error_count,
                "errors": errors
            }
        except Exception as e:
            self.logger.error(
                f"Device sync failed: {str(e)}",
                tags={"component": "phase1_integration", "operation": "sync_devices", "error": True}
            )
            raise
    
    def sync_scenarios(self) -> Dict[str, Any]:
        """
        Synchronize scenarios with Phase 1 API.
        
        Returns:
            Synchronization result
        """
        try:
            # Note: vpp-master does not have a scenarios endpoint yet
            # Return success with 0 items synced
            return {
                "synced_count": 0,
                "error_count": 0,
                "errors": ["Scenarios endpoint not available in Phase 1"]
            }
        except Exception as e:
            self.logger.error(
                f"Scenario sync failed: {str(e)}",
                tags={"component": "phase1_integration", "operation": "sync_scenarios", "error": True}
            )
            raise
    
    def sync_metrics(self) -> Dict[str, Any]:
        """
        Synchronize metrics with Phase 1 API.
        
        Returns:
            Synchronization result
        """
        try:
            # Note: vpp-master does not have a metrics endpoint yet
            # Return success with 0 items synced
            return {
                "synced_count": 0,
                "error_count": 0,
                "errors": ["Metrics endpoint not available in Phase 1"]
            }
        except Exception as e:
            self.logger.error(
                f"Metrics sync failed: {str(e)}",
                tags={"component": "phase1_integration", "operation": "sync_metrics", "error": True}
            )
            raise
    
    def get_sync_history(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get synchronization history.
        
        Args:
            limit: Maximum number of records
            offset: Pagination offset
        
        Returns:
            History records
        """
        records = self.sync_history[offset:offset + limit]
        return {
            "records": records,
            "total_count": len(self.sync_history),
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _is_connected(self) -> bool:
        """Check if Phase 1 API is connected."""
        health = self.check_health()
        return health.get("status") == "healthy"
    
    def _sync_full(self) -> Dict[str, Any]:
        """Perform full synchronization."""
        result = {
            "synced_count": 0,
            "error_count": 0,
            "errors": []
        }
        
        # Sync devices
        devices_result = self.sync_devices()
        result["synced_count"] += devices_result.get("synced_count", 0)
        result["error_count"] += devices_result.get("error_count", 0)
        result["errors"].extend(devices_result.get("errors", []))
        
        # Sync scenarios
        scenarios_result = self.sync_scenarios()
        result["synced_count"] += scenarios_result.get("synced_count", 0)
        result["error_count"] += scenarios_result.get("error_count", 0)
        result["errors"].extend(scenarios_result.get("errors", []))
        
        # Sync metrics
        metrics_result = self.sync_metrics()
        result["synced_count"] += metrics_result.get("synced_count", 0)
        result["error_count"] += metrics_result.get("error_count", 0)
        result["errors"].extend(metrics_result.get("errors", []))
        
        return result
    
    def _sync_incremental(self) -> Dict[str, Any]:
        """Perform incremental synchronization."""
        # For now, same as full sync
        # In production, would track changes and only sync modified items
        return self._sync_full()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for Phase 1 API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "VPP-Phase2-Simulation/1.0"
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        else:
            # Use default API key for phase2 service
            headers["X-API-Key"] = "vpp-vcc-key-dev"
        return headers
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True
    )
    def _post_to_phase1(self, endpoint: str, data: Dict[str, Any]) -> requests.Response:
        """
        POST data to Phase 1 API with automatic retry logic using exponential backoff.
        
        Args:
            endpoint: API endpoint
            data: Data to send
        
        Returns:
            Response object
        
        Raises:
            requests.exceptions.RequestException: If all retries fail
        """
        url = f"{self.master_url}{endpoint}"
        
        try:
            response = requests.post(
                url,
                json=data,
                timeout=self.timeout,
                headers=self._get_headers()
            )
            
            if response.status_code >= 500:
                # Retry on server errors
                raise requests.exceptions.HTTPError(f"HTTP {response.status_code}")
            
            return response
        except requests.exceptions.RequestException as e:
            self.logger.warning(
                f"POST to {endpoint} failed (will retry): {str(e)}",
                endpoint=endpoint,
                tags={"component": "phase1_integration", "operation": "post_retry"}
            )
            raise
    
    def start(self):
        """Start the background scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info(
                "Phase 1 Integration Service started",
                tags={"component": "phase1_integration", "operation": "start"}
            )
    
    def stop(self):
        """Stop the background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info(
                "Phase 1 Integration Service stopped",
                tags={"component": "phase1_integration", "operation": "stop"}
            )
    
    def _map_device_to_phase1(self, device: Any) -> Dict[str, Any]:
        """
        Map Phase 2 device to Phase 1 format.
        
        Args:
            device: Phase 2 device object
        
        Returns:
            Phase 1 device format
        """
        return {
            "id": str(device.id),
            "name": device.name,
            "type": device.device_type,
            "status": device.status,
            "capacity": device.capacity,
            "current_output": device.current_output,
            "location": device.location,
            "metadata": device.metadata or {}
        }
    
    def _map_scenario_to_phase1(self, scenario: Any) -> Dict[str, Any]:
        """
        Map Phase 2 scenario to Phase 1 format.
        
        Args:
            scenario: Phase 2 scenario object
        
        Returns:
            Phase 1 scenario format
        """
        return {
            "id": str(scenario.id),
            "name": scenario.name,
            "description": scenario.description,
            "status": scenario.status,
            "start_time": scenario.start_time.isoformat() if scenario.start_time else None,
            "end_time": scenario.end_time.isoformat() if scenario.end_time else None,
            "configuration": scenario.configuration or {}
        }
