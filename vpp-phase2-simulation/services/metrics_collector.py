"""
Metrics Collector for VPP Phase 2 Simulation Framework.

Collects, aggregates, and manages performance metrics during simulation.
Supports time-based aggregation (1s, 1m, 1h) and historical retention.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import json

from sqlalchemy import and_, func
from models.metrics import Metric
from models.scenario import Scenario
from utils.database import get_session, close_session

logger = logging.getLogger(__name__)


class AggregationPeriod(Enum):
    """Aggregation period types."""
    ONE_SECOND = "1s"
    ONE_MINUTE = "1m"
    ONE_HOUR = "1h"


@dataclass
class AggregatedMetric:
    """Aggregated metric data."""
    metric_name: str
    period: str
    timestamp: datetime
    count: int
    min_value: float
    max_value: float
    avg_value: float
    sum_value: float
    tags: Dict


@dataclass
class PerformanceReport:
    """Performance report for a scenario."""
    scenario_id: str
    scenario_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    metrics_summary: Dict
    aggregated_metrics: List[AggregatedMetric]
    error_count: int
    warning_count: int


class MetricsCollector:
    """
    Collects and manages performance metrics during simulation.
    
    Responsibilities:
    - Record metrics with tags and timestamps
    - Aggregate metrics by time period
    - Query metrics with time range filtering
    - Generate performance reports
    - Maintain historical metrics retention
    """

    # Retention policy: 30 days
    RETENTION_DAYS = 30

    def __init__(self):
        """Initialize metrics collector."""
        self.session = None

    def record_metric(
        self,
        scenario_id: str,
        metric_name: str,
        value: float,
        tags: Optional[Dict] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Record a single metric.

        Args:
            scenario_id: ID of the scenario
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for the metric
            timestamp: Optional timestamp (defaults to now)

        Raises:
            ValueError: If scenario_id or metric_name is empty
        """
        if not scenario_id or not metric_name:
            raise ValueError("scenario_id and metric_name are required")

        if value is None:
            raise ValueError("metric value cannot be None")

        session = get_session()
        try:
            metric = Metric(
                scenario_id=scenario_id,
                metric_name=metric_name,
                value=float(value),
                tags=tags or {},
                timestamp=timestamp or datetime.utcnow()
            )
            session.add(metric)
            session.commit()
            logger.debug(
                f"Recorded metric: {metric_name}={value} for scenario {scenario_id}"
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to record metric: {e}")
            raise
        finally:
            close_session(session)

    def record_metrics_batch(
        self,
        scenario_id: str,
        metrics: List[Tuple[str, float, Optional[Dict]]]
    ) -> None:
        """
        Record multiple metrics in a batch.

        Args:
            scenario_id: ID of the scenario
            metrics: List of (metric_name, value, tags) tuples

        Raises:
            ValueError: If scenario_id is empty or metrics list is empty
        """
        if not scenario_id:
            raise ValueError("scenario_id is required")

        if not metrics:
            raise ValueError("metrics list cannot be empty")

        session = get_session()
        try:
            metric_objects = []
            for metric_name, value, tags in metrics:
                if not metric_name or value is None:
                    continue

                metric = Metric(
                    scenario_id=scenario_id,
                    metric_name=metric_name,
                    value=float(value),
                    tags=tags or {},
                    timestamp=datetime.utcnow()
                )
                metric_objects.append(metric)

            if metric_objects:
                session.add_all(metric_objects)
                session.commit()
                logger.debug(
                    f"Recorded {len(metric_objects)} metrics for scenario {scenario_id}"
                )
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to record metrics batch: {e}")
            raise
        finally:
            close_session(session)

    def get_metrics(
        self,
        scenario_id: str,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        tags_filter: Optional[Dict] = None
    ) -> List[Metric]:
        """
        Get metrics for a scenario with optional filtering.

        Args:
            scenario_id: ID of the scenario
            metric_name: Optional metric name filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            tags_filter: Optional tags filter

        Returns:
            List of metrics matching the criteria

        Raises:
            ValueError: If scenario_id is empty
        """
        if not scenario_id:
            raise ValueError("scenario_id is required")

        session = get_session()
        try:
            query = session.query(Metric).filter(
                Metric.scenario_id == scenario_id
            )

            if metric_name:
                query = query.filter(Metric.metric_name == metric_name)

            if start_time:
                query = query.filter(Metric.timestamp >= start_time)

            if end_time:
                query = query.filter(Metric.timestamp <= end_time)

            metrics = query.order_by(Metric.timestamp).all()

            # Filter by tags if provided
            if tags_filter:
                filtered_metrics = []
                for metric in metrics:
                    if self._tags_match(metric.tags, tags_filter):
                        filtered_metrics.append(metric)
                metrics = filtered_metrics

            return metrics
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            raise
        finally:
            close_session(session)

    def aggregate_metrics(
        self,
        scenario_id: str,
        metric_name: Optional[str] = None,
        period: AggregationPeriod = AggregationPeriod.ONE_MINUTE,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AggregatedMetric]:
        """
        Aggregate metrics by time period.

        Args:
            scenario_id: ID of the scenario
            metric_name: Optional metric name filter
            period: Aggregation period (1s, 1m, 1h)
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of aggregated metrics

        Raises:
            ValueError: If scenario_id is empty
        """
        if not scenario_id:
            raise ValueError("scenario_id is required")

        session = get_session()
        try:
            # Get metrics for the time range
            metrics = self.get_metrics(
                scenario_id=scenario_id,
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time
            )

            if not metrics:
                return []

            # Group metrics by period
            aggregated = self._group_by_period(metrics, period)

            return aggregated
        except Exception as e:
            logger.error(f"Failed to aggregate metrics: {e}")
            raise
        finally:
            close_session(session)

    def generate_report(self, scenario_id: str) -> PerformanceReport:
        """
        Generate a performance report for a scenario.

        Args:
            scenario_id: ID of the scenario

        Returns:
            PerformanceReport with metrics summary and analysis

        Raises:
            ValueError: If scenario_id is empty or scenario not found
        """
        if not scenario_id:
            raise ValueError("scenario_id is required")

        session = get_session()
        try:
            # Get scenario
            scenario = session.query(Scenario).filter(
                Scenario.id == scenario_id
            ).first()

            if not scenario:
                raise ValueError(f"Scenario {scenario_id} not found")

            # Get all metrics for the scenario
            metrics = session.query(Metric).filter(
                Metric.scenario_id == scenario_id
            ).all()

            # Calculate duration
            if scenario.end_time and scenario.start_time:
                duration = (scenario.end_time - scenario.start_time).total_seconds()
            else:
                duration = 0

            # Generate metrics summary
            metrics_summary = self._generate_metrics_summary(metrics)

            # Generate aggregated metrics
            aggregated_metrics = self.aggregate_metrics(
                scenario_id=scenario_id,
                period=AggregationPeriod.ONE_MINUTE,
                start_time=scenario.start_time,
                end_time=scenario.end_time
            )

            # Count errors and warnings
            error_count = len([m for m in metrics if m.metric_name == "error"])
            warning_count = len([m for m in metrics if m.metric_name == "warning"])

            report = PerformanceReport(
                scenario_id=scenario_id,
                scenario_name=scenario.name,
                start_time=scenario.start_time,
                end_time=scenario.end_time or datetime.utcnow(),
                duration_seconds=duration,
                metrics_summary=metrics_summary,
                aggregated_metrics=aggregated_metrics,
                error_count=error_count,
                warning_count=warning_count
            )

            logger.info(f"Generated performance report for scenario {scenario_id}")
            return report
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise
        finally:
            close_session(session)

    def cleanup_old_metrics(self, retention_days: int = RETENTION_DAYS) -> int:
        """
        Clean up metrics older than retention period.

        Args:
            retention_days: Number of days to retain (default: 30)

        Returns:
            Number of metrics deleted

        Raises:
            ValueError: If retention_days is negative
        """
        if retention_days < 0:
            raise ValueError("retention_days cannot be negative")

        session = get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            deleted_count = session.query(Metric).filter(
                Metric.timestamp < cutoff_date
            ).delete()

            session.commit()
            logger.info(f"Deleted {deleted_count} metrics older than {retention_days} days")
            return deleted_count
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to cleanup old metrics: {e}")
            raise
        finally:
            close_session(session)

    def get_metrics_statistics(
        self,
        scenario_id: str,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        """
        Get statistics for a specific metric.

        Args:
            scenario_id: ID of the scenario
            metric_name: Name of the metric
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Dictionary with statistics (min, max, avg, sum, count)

        Raises:
            ValueError: If scenario_id or metric_name is empty
        """
        if not scenario_id or not metric_name:
            raise ValueError("scenario_id and metric_name are required")

        session = get_session()
        try:
            query = session.query(Metric).filter(
                and_(
                    Metric.scenario_id == scenario_id,
                    Metric.metric_name == metric_name
                )
            )

            if start_time:
                query = query.filter(Metric.timestamp >= start_time)

            if end_time:
                query = query.filter(Metric.timestamp <= end_time)

            metrics = query.all()

            if not metrics:
                return {
                    "count": 0,
                    "min": None,
                    "max": None,
                    "avg": None,
                    "sum": None
                }

            values = [m.value for m in metrics]
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "sum": sum(values)
            }
        except Exception as e:
            logger.error(f"Failed to get metrics statistics: {e}")
            raise
        finally:
            close_session(session)

    # Private helper methods

    def _tags_match(self, metric_tags: Dict, filter_tags: Dict) -> bool:
        """Check if metric tags match filter tags."""
        for key, value in filter_tags.items():
            if metric_tags.get(key) != value:
                return False
        return True

    def _group_by_period(
        self,
        metrics: List[Metric],
        period: AggregationPeriod
    ) -> List[AggregatedMetric]:
        """Group metrics by time period and aggregate."""
        if not metrics:
            return []

        # Group metrics by period
        groups = {}
        for metric in metrics:
            # Calculate period bucket based on timestamp
            if period == AggregationPeriod.ONE_SECOND:
                # Round to nearest second
                bucket_time = metric.timestamp.replace(microsecond=0)
            elif period == AggregationPeriod.ONE_MINUTE:
                # Round to nearest minute
                bucket_time = metric.timestamp.replace(second=0, microsecond=0)
            else:  # ONE_HOUR
                # Round to nearest hour
                bucket_time = metric.timestamp.replace(minute=0, second=0, microsecond=0)

            key = (metric.metric_name, bucket_time)
            if key not in groups:
                groups[key] = []
            groups[key].append(metric)

        # Aggregate each group
        aggregated = []
        for (metric_name, bucket_time), group_metrics in sorted(groups.items()):
            values = [m.value for m in group_metrics]
            agg_metric = AggregatedMetric(
                metric_name=metric_name,
                period=period.value,
                timestamp=bucket_time,
                count=len(values),
                min_value=min(values),
                max_value=max(values),
                avg_value=sum(values) / len(values),
                sum_value=sum(values),
                tags=group_metrics[0].tags if group_metrics else {}
            )
            aggregated.append(agg_metric)

        return aggregated

    def _get_period_seconds(self, period: AggregationPeriod) -> int:
        """Get period in seconds."""
        if period == AggregationPeriod.ONE_SECOND:
            return 1
        elif period == AggregationPeriod.ONE_MINUTE:
            return 60
        elif period == AggregationPeriod.ONE_HOUR:
            return 3600
        else:
            return 60

    def _generate_metrics_summary(self, metrics: List[Metric]) -> Dict:
        """Generate summary statistics for all metrics."""
        if not metrics:
            return {}

        summary = {}
        metric_groups = {}

        # Group metrics by name
        for metric in metrics:
            if metric.metric_name not in metric_groups:
                metric_groups[metric.metric_name] = []
            metric_groups[metric.metric_name].append(metric.value)

        # Calculate statistics for each metric
        for metric_name, values in metric_groups.items():
            summary[metric_name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "sum": sum(values)
            }

        return summary
