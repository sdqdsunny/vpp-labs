"""
Phase 1 API Integration Routes for VPP Phase 2 Simulation Framework.

Provides endpoints for synchronizing data with Phase 1 (VPP Master) API.
Handles bidirectional communication, data mapping, and error recovery.
"""

import json
import logging
from bottle import Bottle, request, response
from datetime import datetime
from typing import Dict, Any, Optional, List

from services.phase1_integration import Phase1IntegrationService
from utils.structured_logger import get_structured_logger


def create_phase1_integration_routes(app: Bottle) -> None:
    """
    Register Phase 1 integration routes.
    
    Args:
        app: Bottle application instance
    """
    
    service = Phase1IntegrationService()
    
    @app.route("/api/phase1/health", method="GET")
    def phase1_health():
        """
        Check Phase 1 API connection health.
        
        Returns:
            JSON with connection status and details
        """
        request_id = getattr(request, "request_id", "unknown")
        logger = get_structured_logger("vpp_phase2_sim.phase1", request_id)
        
        try:
            health_status = service.check_health()
            response.content_type = "application/json"
            
            logger.info(
                "Phase 1 health check completed",
                status=health_status.get("status"),
                tags={"component": "phase1_integration", "operation": "health_check"}
            )
            
            return json.dumps(health_status)
        except Exception as e:
            logger.error(
                f"Phase 1 health check failed: {str(e)}",
                tags={"component": "phase1_integration", "operation": "health_check", "error": True}
            )
            response.status = 503
            response.content_type = "application/json"
            return json.dumps({
                "status": "unavailable",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    @app.route("/api/phase1/status", method="GET")
    def phase1_status():
        """
        Get Phase 1 integration status.
        
        Returns:
            JSON with integration status, last sync time, and statistics
        """
        request_id = getattr(request, "request_id", "unknown")
        logger = get_structured_logger("vpp_phase2_sim.phase1", request_id)
        
        try:
            status = service.get_integration_status()
            response.content_type = "application/json"
            
            logger.info(
                "Phase 1 status retrieved",
                last_sync=status.get("last_sync_time"),
                tags={"component": "phase1_integration", "operation": "get_status"}
            )
            
            return json.dumps(status)
        except Exception as e:
            logger.error(
                f"Failed to get Phase 1 status: {str(e)}",
                tags={"component": "phase1_integration", "operation": "get_status", "error": True}
            )
            response.status = 500
            response.content_type = "application/json"
            return json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    @app.route("/api/phase1/sync", method="POST")
    def phase1_sync():
        """
        Synchronize Phase 2 data with Phase 1 API.
        
        Request body (optional):
            {
                "sync_type": "full|incremental|devices|scenarios",
                "force": false
            }
        
        Returns:
            JSON with sync results and statistics
        """
        request_id = getattr(request, "request_id", "unknown")
        logger = get_structured_logger("vpp_phase2_sim.phase1", request_id)
        
        try:
            # Parse request body
            body = request.json or {}
            sync_type = body.get("sync_type", "incremental")
            force = body.get("force", False)
            
            logger.info(
                "Phase 1 sync started",
                sync_type=sync_type,
                force=force,
                tags={"component": "phase1_integration", "operation": "sync_start"}
            )
            
            # Execute sync
            result = service.sync_data(sync_type=sync_type, force=force)
            
            response.content_type = "application/json"
            response.status = 200
            
            logger.info(
                "Phase 1 sync completed",
                synced_items=result.get("synced_count"),
                errors=result.get("error_count"),
                tags={"component": "phase1_integration", "operation": "sync_complete"}
            )
            
            return json.dumps(result)
        except ValueError as e:
            logger.warning(
                f"Invalid sync request: {str(e)}",
                tags={"component": "phase1_integration", "operation": "sync", "error": True}
            )
            response.status = 400
            response.content_type = "application/json"
            return json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(
                f"Phase 1 sync failed: {str(e)}",
                tags={"component": "phase1_integration", "operation": "sync", "error": True}
            )
            response.status = 500
            response.content_type = "application/json"
            return json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    @app.route("/api/phase1/sync/devices", method="POST")
    def phase1_sync_devices():
        """
        Synchronize devices with Phase 1 API.
        
        Returns:
            JSON with device sync results
        """
        request_id = getattr(request, "request_id", "unknown")
        logger = get_structured_logger("vpp_phase2_sim.phase1", request_id)
        
        try:
            logger.info(
                "Device sync started",
                tags={"component": "phase1_integration", "operation": "sync_devices_start"}
            )
            
            result = service.sync_devices()
            
            response.content_type = "application/json"
            
            logger.info(
                "Device sync completed",
                synced_count=result.get("synced_count"),
                tags={"component": "phase1_integration", "operation": "sync_devices_complete"}
            )
            
            return json.dumps(result)
        except Exception as e:
            logger.error(
                f"Device sync failed: {str(e)}",
                tags={"component": "phase1_integration", "operation": "sync_devices", "error": True}
            )
            response.status = 500
            response.content_type = "application/json"
            return json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    @app.route("/api/phase1/sync/scenarios", method="POST")
    def phase1_sync_scenarios():
        """
        Synchronize scenarios with Phase 1 API.
        
        Returns:
            JSON with scenario sync results
        """
        request_id = getattr(request, "request_id", "unknown")
        logger = get_structured_logger("vpp_phase2_sim.phase1", request_id)
        
        try:
            logger.info(
                "Scenario sync started",
                tags={"component": "phase1_integration", "operation": "sync_scenarios_start"}
            )
            
            result = service.sync_scenarios()
            
            response.content_type = "application/json"
            
            logger.info(
                "Scenario sync completed",
                synced_count=result.get("synced_count"),
                tags={"component": "phase1_integration", "operation": "sync_scenarios_complete"}
            )
            
            return json.dumps(result)
        except Exception as e:
            logger.error(
                f"Scenario sync failed: {str(e)}",
                tags={"component": "phase1_integration", "operation": "sync_scenarios", "error": True}
            )
            response.status = 500
            response.content_type = "application/json"
            return json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    @app.route("/api/phase1/sync/metrics", method="POST")
    def phase1_sync_metrics():
        """
        Synchronize metrics with Phase 1 API.
        
        Returns:
            JSON with metrics sync results
        """
        request_id = getattr(request, "request_id", "unknown")
        logger = get_structured_logger("vpp_phase2_sim.phase1", request_id)
        
        try:
            logger.info(
                "Metrics sync started",
                tags={"component": "phase1_integration", "operation": "sync_metrics_start"}
            )
            
            result = service.sync_metrics()
            
            response.content_type = "application/json"
            
            logger.info(
                "Metrics sync completed",
                synced_count=result.get("synced_count"),
                tags={"component": "phase1_integration", "operation": "sync_metrics_complete"}
            )
            
            return json.dumps(result)
        except Exception as e:
            logger.error(
                f"Metrics sync failed: {str(e)}",
                tags={"component": "phase1_integration", "operation": "sync_metrics", "error": True}
            )
            response.status = 500
            response.content_type = "application/json"
            return json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    @app.route("/api/phase1/sync/history", method="GET")
    def phase1_sync_history():
        """
        Get Phase 1 synchronization history.
        
        Query parameters:
            limit: Maximum number of records (default: 50)
            offset: Pagination offset (default: 0)
        
        Returns:
            JSON with sync history records
        """
        request_id = getattr(request, "request_id", "unknown")
        logger = get_structured_logger("vpp_phase2_sim.phase1", request_id)
        
        try:
            limit = int(request.query.get("limit", 50))
            offset = int(request.query.get("offset", 0))
            
            history = service.get_sync_history(limit=limit, offset=offset)
            
            response.content_type = "application/json"
            
            logger.info(
                "Sync history retrieved",
                record_count=len(history.get("records", [])),
                tags={"component": "phase1_integration", "operation": "get_history"}
            )
            
            return json.dumps(history)
        except Exception as e:
            logger.error(
                f"Failed to get sync history: {str(e)}",
                tags={"component": "phase1_integration", "operation": "get_history", "error": True}
            )
            response.status = 500
            response.content_type = "application/json"
            return json.dumps({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
