"""
Metrics API routes for VPP Phase 2 Simulation Framework.

Provides endpoints for querying metrics, generating reports, and managing metrics data.
"""

from bottle import Bottle, request, response
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import logging

from services.metrics_collector import MetricsCollector, AggregationPeriod
from utils.errors import SimulatorError, ValidationError

logger = logging.getLogger(__name__)

app = Bottle()
metrics_collector = MetricsCollector()


@app.get("/metrics/<scenario_id>")
def get_metrics(scenario_id: str):
    """
    Get metrics for a scenario.

    Query parameters:
    - metric_name: Optional metric name filter
    - start_time: Optional start time (ISO format)
    - end_time: Optional end time (ISO format)

    Returns:
        List of metrics matching the criteria
    """
    try:
        metric_name = request.query.get("metric_name")
        start_time_str = request.query.get("start_time")
        end_time_str = request.query.get("end_time")

        # Parse timestamps
        start_time = None
        end_time = None
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str)
        if end_time_str:
            end_time = datetime.fromisoformat(end_time_str)

        # Get metrics
        metrics = metrics_collector.get_metrics(
            scenario_id=scenario_id,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time
        )

        # Convert to JSON-serializable format
        result = [
            {
                "id": m.id,
                "scenario_id": m.scenario_id,
                "metric_name": m.metric_name,
                "value": m.value,
                "tags": m.tags,
                "timestamp": m.timestamp.isoformat()
            }
            for m in metrics
        ]

        response.status = 200
        return {"metrics": result, "count": len(result)}

    except ValueError as e:
        response.status = 400
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        response.status = 500
        return {"error": "Internal server error"}


@app.get("/metrics/<scenario_id>/aggregated")
def get_aggregated_metrics(scenario_id: str):
    """
    Get aggregated metrics for a scenario.

    Query parameters:
    - metric_name: Optional metric name filter
    - period: Aggregation period (1s, 1m, 1h) - default: 1m
    - start_time: Optional start time (ISO format)
    - end_time: Optional end time (ISO format)

    Returns:
        List of aggregated metrics
    """
    try:
        metric_name = request.query.get("metric_name")
        period_str = request.query.get("period", "1m")
        start_time_str = request.query.get("start_time")
        end_time_str = request.query.get("end_time")

        # Parse period
        try:
            period = AggregationPeriod(period_str)
        except ValueError:
            response.status = 400
            return {"error": f"Invalid period: {period_str}. Must be 1s, 1m, or 1h"}

        # Parse timestamps
        start_time = None
        end_time = None
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str)
        if end_time_str:
            end_time = datetime.fromisoformat(end_time_str)

        # Get aggregated metrics
        aggregated = metrics_collector.aggregate_metrics(
            scenario_id=scenario_id,
            metric_name=metric_name,
            period=period,
            start_time=start_time,
            end_time=end_time
        )

        # Convert to JSON-serializable format
        result = [
            {
                "metric_name": m.metric_name,
                "period": m.period,
                "timestamp": m.timestamp.isoformat(),
                "count": m.count,
                "min": m.min_value,
                "max": m.max_value,
                "avg": m.avg_value,
                "sum": m.sum_value,
                "tags": m.tags
            }
            for m in aggregated
        ]

        response.status = 200
        return {"aggregated_metrics": result, "count": len(result)}

    except ValueError as e:
        response.status = 400
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Failed to get aggregated metrics: {e}")
        response.status = 500
        return {"error": "Internal server error"}


@app.get("/metrics/<scenario_id>/statistics")
def get_metrics_statistics(scenario_id: str):
    """
    Get statistics for a specific metric.

    Query parameters:
    - metric_name: Required metric name
    - start_time: Optional start time (ISO format)
    - end_time: Optional end time (ISO format)

    Returns:
        Statistics (min, max, avg, sum, count)
    """
    try:
        metric_name = request.query.get("metric_name")
        if not metric_name:
            response.status = 400
            return {"error": "metric_name is required"}

        start_time_str = request.query.get("start_time")
        end_time_str = request.query.get("end_time")

        # Parse timestamps
        start_time = None
        end_time = None
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str)
        if end_time_str:
            end_time = datetime.fromisoformat(end_time_str)

        # Get statistics
        stats = metrics_collector.get_metrics_statistics(
            scenario_id=scenario_id,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time
        )

        response.status = 200
        return {
            "metric_name": metric_name,
            "statistics": stats
        }

    except ValueError as e:
        response.status = 400
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Failed to get metrics statistics: {e}")
        response.status = 500
        return {"error": "Internal server error"}


@app.get("/metrics/<scenario_id>/report")
def get_performance_report(scenario_id: str):
    """
    Get performance report for a scenario.

    Returns:
        Performance report with metrics summary and analysis
    """
    try:
        report = metrics_collector.generate_report(scenario_id)

        # Convert to JSON-serializable format
        result = {
            "scenario_id": report.scenario_id,
            "scenario_name": report.scenario_name,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat(),
            "duration_seconds": report.duration_seconds,
            "metrics_summary": report.metrics_summary,
            "aggregated_metrics": [
                {
                    "metric_name": m.metric_name,
                    "period": m.period,
                    "timestamp": m.timestamp.isoformat(),
                    "count": m.count,
                    "min": m.min_value,
                    "max": m.max_value,
                    "avg": m.avg_value,
                    "sum": m.sum_value,
                    "tags": m.tags
                }
                for m in report.aggregated_metrics
            ],
            "error_count": report.error_count,
            "warning_count": report.warning_count
        }

        response.status = 200
        return result

    except ValueError as e:
        response.status = 400
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Failed to get performance report: {e}")
        response.status = 500
        return {"error": "Internal server error"}


@app.post("/metrics/<scenario_id>/record")
def record_metric(scenario_id: str):
    """
    Record a single metric.

    Request body:
    {
        "metric_name": "string",
        "value": float,
        "tags": {optional object}
    }

    Returns:
        Success confirmation
    """
    try:
        data = request.json

        if not data:
            response.status = 400
            return {"error": "Request body is required"}

        metric_name = data.get("metric_name")
        value = data.get("value")

        if not metric_name or value is None:
            response.status = 400
            return {"error": "metric_name and value are required"}

        tags = data.get("tags", {})

        # Record metric
        metrics_collector.record_metric(
            scenario_id=scenario_id,
            metric_name=metric_name,
            value=value,
            tags=tags
        )

        response.status = 201
        return {"message": "Metric recorded successfully"}

    except ValueError as e:
        response.status = 400
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Failed to record metric: {e}")
        response.status = 500
        return {"error": "Internal server error"}


@app.post("/metrics/<scenario_id>/record-batch")
def record_metrics_batch(scenario_id: str):
    """
    Record multiple metrics in a batch.

    Request body:
    {
        "metrics": [
            {"metric_name": "string", "value": float, "tags": {optional}},
            ...
        ]
    }

    Returns:
        Success confirmation with count
    """
    try:
        data = request.json

        if not data:
            response.status = 400
            return {"error": "Request body is required"}

        metrics_data = data.get("metrics", [])

        if not metrics_data:
            response.status = 400
            return {"error": "metrics array is required"}

        # Convert to tuples
        metrics = [
            (m.get("metric_name"), m.get("value"), m.get("tags"))
            for m in metrics_data
        ]

        # Record metrics
        metrics_collector.record_metrics_batch(
            scenario_id=scenario_id,
            metrics=metrics
        )

        response.status = 201
        return {
            "message": "Metrics recorded successfully",
            "count": len(metrics)
        }

    except ValueError as e:
        response.status = 400
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Failed to record metrics batch: {e}")
        response.status = 500
        return {"error": "Internal server error"}


@app.delete("/metrics/cleanup")
def cleanup_old_metrics():
    """
    Clean up metrics older than retention period.

    Query parameters:
    - retention_days: Number of days to retain (default: 30)

    Returns:
        Number of metrics deleted
    """
    try:
        retention_days_str = request.query.get("retention_days", "30")

        try:
            retention_days = int(retention_days_str)
        except ValueError:
            response.status = 400
            return {"error": "retention_days must be an integer"}

        # Cleanup old metrics
        deleted_count = metrics_collector.cleanup_old_metrics(retention_days)

        response.status = 200
        return {
            "message": "Cleanup completed",
            "deleted_count": deleted_count
        }

    except ValueError as e:
        response.status = 400
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Failed to cleanup metrics: {e}")
        response.status = 500
        return {"error": "Internal server error"}
