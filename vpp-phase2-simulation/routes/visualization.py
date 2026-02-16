"""
Visualization and Monitoring Dashboard Routes

Provides real-time dashboard endpoints with WebSocket support for live updates,
device status display, power flow visualization, and alert management.

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from bottle import Bottle, request, response

from utils.database import get_session
from models.device_state import DeviceState
from models.scenario import Scenario
from models.metrics import Metric
from models.power_flow_result import PowerFlowResult
from services.metrics_collector import MetricsCollector
from services.scenario_engine import ScenarioEngine
from services.power_flow_engine import PowerFlowEngine

logger = logging.getLogger(__name__)


def create_visualization_routes(app: Bottle) -> None:
    """
    Create visualization and monitoring dashboard routes.
    
    Args:
        app: Bottle application instance
    """
    
    @app.route("/api/dashboard/status", method="GET")
    def get_dashboard_status():
        """
        Get current dashboard status with device states and power flows.
        
        Returns:
            JSON with device status, power flows, and alerts
            
        Requirement: 12.2 - Dashboard Display Completeness
        """
        try:
            session = request.db
            
            # Get active scenarios
            active_scenarios = session.query(Scenario).filter(
                Scenario.status.in_(["running", "pending"])
            ).all()
            
            if not active_scenarios:
                response.content_type = "application/json"
                return json.dumps({
                    "status": "idle",
                    "device_count": 0,
                    "devices": [],
                    "power_flows": [],
                    "alerts": [],
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            scenario_id = active_scenarios[0].id
            
            # Get device states
            device_states = session.query(DeviceState).filter(
                DeviceState.scenario_id == scenario_id
            ).all()
            
            devices = []
            for state in device_states:
                devices.append({
                    "device_id": state.device_id,
                    "device_type": state.device_type,
                    "state": state.state_data,
                    "timestamp": state.timestamp.isoformat()
                })
            
            # Get power flow results
            power_flows = []
            latest_pf = session.query(PowerFlowResult).filter(
                PowerFlowResult.scenario_id == scenario_id
            ).order_by(PowerFlowResult.timestamp.desc()).first()
            
            if latest_pf:
                power_flows = latest_pf.power_flows
                violations = latest_pf.violations
            else:
                violations = []
            
            # Get alerts (violations and stability issues)
            alerts = []
            for violation in violations:
                alerts.append({
                    "type": "violation",
                    "severity": "warning",
                    "message": violation.get("message", "Violation detected"),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            response.content_type = "application/json"
            return json.dumps({
                "status": "running",
                "scenario_id": scenario_id,
                "device_count": len(devices),
                "devices": devices,
                "power_flows": power_flows,
                "alerts": alerts,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting dashboard status: {str(e)}")
            response.status = 500
            response.content_type = "application/json"
            return json.dumps({
                "error": "Failed to get dashboard status",
                "details": str(e)
            })
    
    
    @app.route("/api/dashboard/metrics", method="GET")
    def get_dashboard_metrics():
        """
        Get real-time metrics for dashboard display.
        
        Query Parameters:
            scenario_id: Scenario ID (optional, uses active scenario if not provided)
            metric_names: Comma-separated metric names to retrieve
            
        Returns:
            JSON with current metrics and aggregated statistics
            
        Requirement: 12.1 - Real-Time Dashboard Updates
        """
        try:
            session = request.db
            metric_names = request.query.get("metric_names", "").split(",")
            scenario_id = request.query.get("scenario_id")
            
            # Get active scenario if not specified
            if not scenario_id:
                active = session.query(Scenario).filter(
                    Scenario.status.in_(["running", "pending"])
                ).first()
                if not active:
                    response.content_type = "application/json"
                    return json.dumps({"metrics": [], "timestamp": datetime.utcnow().isoformat()})
                scenario_id = active.id
            
            # Get recent metrics
            metrics_query = session.query(Metric).filter(
                Metric.scenario_id == scenario_id
            )
            
            if metric_names and metric_names[0]:
                metrics_query = metrics_query.filter(
                    Metric.metric_name.in_(metric_names)
                )
            
            # Get metrics from last 5 minutes
            five_min_ago = datetime.utcnow() - timedelta(minutes=5)
            metrics_query = metrics_query.filter(
                Metric.timestamp >= five_min_ago
            ).order_by(Metric.timestamp.desc())
            
            metrics = metrics_query.all()
            
            # Aggregate metrics by name
            aggregated = {}
            for metric in metrics:
                if metric.metric_name not in aggregated:
                    aggregated[metric.metric_name] = {
                        "values": [],
                        "tags": metric.tags,
                        "latest": metric.value,
                        "timestamp": metric.timestamp.isoformat()
                    }
                aggregated[metric.metric_name]["values"].append(metric.value)
            
            # Calculate statistics
            for name, data in aggregated.items():
                values = data["values"]
                if values:
                    data["min"] = min(values)
                    data["max"] = max(values)
                    data["avg"] = sum(values) / len(values)
                    data["count"] = len(values)
            
            response.content_type = "application/json"
            return json.dumps({
                "metrics": aggregated,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {str(e)}")
            response.status = 500
            response.content_type = "application/json"
            return json.dumps({
                "error": "Failed to get metrics",
                "details": str(e)
            })
    
    
    @app.route("/api/dashboard/devices", method="GET")
    def get_dashboard_devices():
        """
        Get device status for dashboard display.
        
        Query Parameters:
            scenario_id: Scenario ID (optional)
            device_type: Filter by device type (optional)
            
        Returns:
            JSON with device status and state information
            
        Requirement: 12.2 - Dashboard Display Completeness
        """
        try:
            session = request.db
            scenario_id = request.query.get("scenario_id")
            device_type = request.query.get("device_type")
            
            # Get active scenario if not specified
            if not scenario_id:
                active = session.query(Scenario).filter(
                    Scenario.status.in_(["running", "pending"])
                ).first()
                if not active:
                    response.content_type = "application/json"
                    return json.dumps({
                        "devices": [],
                        "count": 0,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                scenario_id = active.id
            
            # Query device states
            query = session.query(DeviceState).filter(
                DeviceState.scenario_id == scenario_id
            )
            
            if device_type:
                query = query.filter(DeviceState.device_type == device_type)
            
            device_states = query.all()
            
            devices = []
            for state in device_states:
                devices.append({
                    "device_id": state.device_id,
                    "device_type": state.device_type,
                    "state": state.state_data,
                    "timestamp": state.timestamp.isoformat()
                })
            
            response.content_type = "application/json"
            return json.dumps({
                "devices": devices,
                "count": len(devices),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting dashboard devices: {str(e)}")
            response.status = 500
            response.content_type = "application/json"
            return json.dumps({
                "error": "Failed to get devices",
                "details": str(e)
            })
    
    
    @app.route("/api/dashboard/power-flows", method="GET")
    def get_dashboard_power_flows():
        """
        Get power flow visualization data.
        
        Query Parameters:
            scenario_id: Scenario ID (optional)
            
        Returns:
            JSON with power flow data for visualization
            
        Requirement: 12.2 - Dashboard Display Completeness
        """
        try:
            session = request.db
            scenario_id = request.query.get("scenario_id")
            
            # Get active scenario if not specified
            if not scenario_id:
                active = session.query(Scenario).filter(
                    Scenario.status.in_(["running", "pending"])
                ).first()
                if not active:
                    response.content_type = "application/json"
                    return json.dumps({"power_flows": [], "violations": []})
                scenario_id = active.id
            
            # Get latest power flow result
            pf_result = session.query(PowerFlowResult).filter(
                PowerFlowResult.scenario_id == scenario_id
            ).order_by(PowerFlowResult.timestamp.desc()).first()
            
            if not pf_result:
                response.content_type = "application/json"
                return json.dumps({
                    "power_flows": [],
                    "violations": [],
                    "stability": {},
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            response.content_type = "application/json"
            return json.dumps({
                "power_flows": pf_result.power_flows,
                "violations": pf_result.violations,
                "stability": pf_result.stability_assessment,
                "timestamp": pf_result.timestamp.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting power flows: {str(e)}")
            response.status = 500
            response.content_type = "application/json"
            return json.dumps({
                "error": "Failed to get power flows",
                "details": str(e)
            })
    
    
    @app.route("/api/dashboard/alerts", method="GET")
    def get_dashboard_alerts():
        """
        Get active alerts for dashboard display.
        
        Query Parameters:
            scenario_id: Scenario ID (optional)
            severity: Filter by severity (warning, critical)
            
        Returns:
            JSON with active alerts
            
        Requirement: 12.2 - Dashboard Display Completeness
        """
        try:
            session = request.db
            scenario_id = request.query.get("scenario_id")
            severity = request.query.get("severity")
            
            # Get active scenario if not specified
            if not scenario_id:
                active = session.query(Scenario).filter(
                    Scenario.status.in_(["running", "pending"])
                ).first()
                if not active:
                    response.content_type = "application/json"
                    return json.dumps({"alerts": []})
                scenario_id = active.id
            
            # Get power flow violations
            pf_result = session.query(PowerFlowResult).filter(
                PowerFlowResult.scenario_id == scenario_id
            ).order_by(PowerFlowResult.timestamp.desc()).first()
            
            alerts = []
            if pf_result:
                for violation in pf_result.violations:
                    alert = {
                        "type": "violation",
                        "severity": "warning",
                        "message": violation.get("message", "Violation detected"),
                        "timestamp": pf_result.timestamp.isoformat()
                    }
                    if not severity or alert["severity"] == severity:
                        alerts.append(alert)
                
                # Check stability
                stability = pf_result.stability_assessment
                if stability.get("is_stable") is False:
                    alert = {
                        "type": "stability",
                        "severity": "critical",
                        "message": "System instability detected",
                        "timestamp": pf_result.timestamp.isoformat()
                    }
                    if not severity or alert["severity"] == severity:
                        alerts.append(alert)
            
            response.content_type = "application/json"
            return json.dumps({
                "alerts": alerts,
                "count": len(alerts),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting alerts: {str(e)}")
            response.status = 500
            response.content_type = "application/json"
            return json.dumps({
                "error": "Failed to get alerts",
                "details": str(e)
            })
    
    
    @app.route("/api/dashboard/results", method="GET")
    def get_dashboard_results():
        """
        Get final results and analysis for completed scenarios.
        
        Query Parameters:
            scenario_id: Scenario ID (required)
            
        Returns:
            JSON with final results and analysis
            
        Requirement: 12.5 - Final Results Display
        """
        try:
            session = request.db
            scenario_id = request.query.get("scenario_id")
            
            if not scenario_id:
                response.status = 400
                response.content_type = "application/json"
                return json.dumps({"error": "scenario_id is required"})
            
            # Get scenario
            scenario = session.query(Scenario).filter(
                Scenario.id == scenario_id
            ).first()
            
            if not scenario:
                response.status = 404
                response.content_type = "application/json"
                return json.dumps({"error": "Scenario not found"})
            
            # Get metrics for analysis
            metrics = session.query(Metric).filter(
                Metric.scenario_id == scenario_id
            ).all()
            
            # Aggregate metrics
            metric_summary = {}
            for metric in metrics:
                if metric.metric_name not in metric_summary:
                    metric_summary[metric.metric_name] = {
                        "values": [],
                        "tags": metric.tags
                    }
                metric_summary[metric.metric_name]["values"].append(metric.value)
            
            # Calculate statistics
            for name, data in metric_summary.items():
                values = data["values"]
                if values:
                    data["min"] = min(values)
                    data["max"] = max(values)
                    data["avg"] = sum(values) / len(values)
                    data["count"] = len(values)
            
            # Get final power flow result
            final_pf = session.query(PowerFlowResult).filter(
                PowerFlowResult.scenario_id == scenario_id
            ).order_by(PowerFlowResult.timestamp.desc()).first()
            
            response.content_type = "application/json"
            return json.dumps({
                "scenario_id": scenario_id,
                "status": scenario.status,
                "start_time": scenario.start_time.isoformat(),
                "end_time": scenario.end_time.isoformat() if scenario.end_time else None,
                "metrics_summary": metric_summary,
                "power_flow_analysis": {
                    "violations": final_pf.violations if final_pf else [],
                    "stability": final_pf.stability_assessment if final_pf else {}
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting results: {str(e)}")
            response.status = 500
            response.content_type = "application/json"
            return json.dumps({
                "error": "Failed to get results",
                "details": str(e)
            })
    
    
    logger.info("Visualization routes created successfully")
