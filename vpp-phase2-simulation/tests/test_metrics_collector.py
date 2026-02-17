"""
Unit tests for Metrics Collector.

Tests metric recording, aggregation, querying, and report generation.
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from services.metrics_collector import (
    MetricsCollector,
    AggregationPeriod,
    AggregatedMetric,
    PerformanceReport
)
from models.metrics import Metric
from models.scenario import Scenario, ScenarioStatus
from utils.database import get_session, close_session


@pytest.fixture
def collector():
    """Create metrics collector instance."""
    return MetricsCollector()


@pytest.fixture
def scenario(test_scenario):
    """Create test scenario."""
    return test_scenario


class TestMetricsCollectorBasic:
    """Test basic metrics collector functionality."""

    def test_collector_initialization(self, collector):
        """Test metrics collector initialization."""
        assert collector is not None
        assert collector.RETENTION_DAYS == 30

    def test_record_single_metric(self, collector, scenario):
        """Test recording a single metric."""
        collector.record_metric(
            scenario_id=scenario.id,
            metric_name="latency",
            value=100.5,
            tags={"device": "solar-1"}
        )

        metrics = collector.get_metrics(
            scenario_id=scenario.id,
            metric_name="latency"
        )

        assert len(metrics) == 1
        assert metrics[0].metric_name == "latency"
        assert metrics[0].value == 100.5
        assert metrics[0].tags["device"] == "solar-1"

    def test_record_metric_without_tags(self, collector, scenario):
        """Test recording metric without tags."""
        collector.record_metric(
            scenario_id=scenario.id,
            metric_name="throughput",
            value=500.0
        )

        metrics = collector.get_metrics(
            scenario_id=scenario.id,
            metric_name="throughput"
        )

        assert len(metrics) == 1
        assert metrics[0].tags == {}

    def test_record_metric_with_custom_timestamp(self, collector, scenario):
        """Test recording metric with custom timestamp."""
        custom_time = datetime.utcnow() - timedelta(hours=1)
        collector.record_metric(
            scenario_id=scenario.id,
            metric_name="power",
            value=1000.0,
            timestamp=custom_time
        )

        metrics = collector.get_metrics(
            scenario_id=scenario.id,
            metric_name="power"
        )

        assert len(metrics) == 1
        assert metrics[0].timestamp == custom_time

    def test_record_metric_empty_scenario_id_raises_error(self, collector):
        """Test recording metric with empty scenario_id raises error."""
        with pytest.raises(ValueError):
            collector.record_metric(
                scenario_id="",
                metric_name="latency",
                value=100.0
            )

    def test_record_metric_empty_metric_name_raises_error(self, collector, scenario):
        """Test recording metric with empty metric_name raises error."""
        with pytest.raises(ValueError):
            collector.record_metric(
                scenario_id=scenario.id,
                metric_name="",
                value=100.0
            )

    def test_record_metric_none_value_raises_error(self, collector, scenario):
        """Test recording metric with None value raises error."""
        with pytest.raises(ValueError):
            collector.record_metric(
                scenario_id=scenario.id,
                metric_name="latency",
                value=None
            )


class TestMetricsCollectorBatch:
    """Test batch metrics recording."""

    def test_record_metrics_batch(self, collector, scenario):
        """Test recording multiple metrics in batch."""
        metrics = [
            ("latency", 100.0, {"device": "solar-1"}),
            ("throughput", 500.0, {"device": "solar-1"}),
            ("error_rate", 0.01, {"device": "solar-1"})
        ]

        collector.record_metrics_batch(
            scenario_id=scenario.id,
            metrics=metrics
        )

        all_metrics = collector.get_metrics(scenario_id=scenario.id)
        assert len(all_metrics) == 3

    def test_record_metrics_batch_empty_list_raises_error(self, collector, scenario):
        """Test recording empty metrics batch raises error."""
        with pytest.raises(ValueError):
            collector.record_metrics_batch(
                scenario_id=scenario.id,
                metrics=[]
            )

    def test_record_metrics_batch_empty_scenario_id_raises_error(self, collector):
        """Test recording batch with empty scenario_id raises error."""
        with pytest.raises(ValueError):
            collector.record_metrics_batch(
                scenario_id="",
                metrics=[("latency", 100.0, {})]
            )

    def test_record_metrics_batch_with_invalid_entries(self, collector, scenario):
        """Test batch recording skips invalid entries."""
        metrics = [
            ("latency", 100.0, {}),
            ("", 200.0, {}),  # Invalid: empty metric name
            ("throughput", None, {}),  # Invalid: None value
            ("power", 1000.0, {})
        ]

        # Should not raise error, just skip invalid entries
        collector.record_metrics_batch(
            scenario_id=scenario.id,
            metrics=metrics
        )

        all_metrics = collector.get_metrics(scenario_id=scenario.id)
        # Should have 2 valid metrics
        assert len(all_metrics) == 2


class TestMetricsCollectorQuerying:
    """Test metrics querying functionality."""

    def test_get_metrics_by_scenario(self, collector, scenario):
        """Test getting metrics by scenario."""
        collector.record_metric(scenario.id, "latency", 100.0)
        collector.record_metric(scenario.id, "throughput", 500.0)

        metrics = collector.get_metrics(scenario_id=scenario.id)
        assert len(metrics) == 2

    def test_get_metrics_by_metric_name(self, collector, scenario):
        """Test getting metrics filtered by name."""
        collector.record_metric(scenario.id, "latency", 100.0)
        collector.record_metric(scenario.id, "latency", 110.0)
        collector.record_metric(scenario.id, "throughput", 500.0)

        metrics = collector.get_metrics(
            scenario_id=scenario.id,
            metric_name="latency"
        )
        assert len(metrics) == 2
        assert all(m.metric_name == "latency" for m in metrics)

    def test_get_metrics_by_time_range(self, collector, scenario):
        """Test getting metrics filtered by time range."""
        now = datetime.utcnow()
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        collector.record_metric(scenario.id, "latency", 100.0, timestamp=past)
        collector.record_metric(scenario.id, "latency", 110.0, timestamp=now)
        collector.record_metric(scenario.id, "latency", 120.0, timestamp=future)

        # Get metrics in middle hour
        metrics = collector.get_metrics(
            scenario_id=scenario.id,
            start_time=now - timedelta(minutes=30),
            end_time=now + timedelta(minutes=30)
        )
        assert len(metrics) == 1
        assert metrics[0].value == 110.0

    def test_get_metrics_empty_scenario_id_raises_error(self, collector):
        """Test getting metrics with empty scenario_id raises error."""
        with pytest.raises(ValueError):
            collector.get_metrics(scenario_id="")

    def test_get_metrics_nonexistent_scenario(self, collector):
        """Test getting metrics for nonexistent scenario returns empty."""
        metrics = collector.get_metrics(scenario_id="nonexistent")
        assert len(metrics) == 0


class TestMetricsCollectorAggregation:
    """Test metrics aggregation functionality."""

    def test_aggregate_metrics_one_minute(self, collector, scenario):
        """Test aggregating metrics by 1-minute period."""
        # Use a fixed time at the start of a minute to avoid boundary issues
        now = datetime.utcnow().replace(second=0, microsecond=0)
        
        # Record metrics in same minute (within 60 seconds)
        for i in range(5):
            collector.record_metric(
                scenario.id,
                "latency",
                100.0 + i * 10,
                timestamp=now + timedelta(seconds=i*5)  # 5-second intervals
            )

        aggregated = collector.aggregate_metrics(
            scenario_id=scenario.id,
            metric_name="latency",
            period=AggregationPeriod.ONE_MINUTE,
            start_time=now,
            end_time=now + timedelta(minutes=1)
        )

        assert len(aggregated) >= 1
        agg = aggregated[0]
        assert agg.metric_name == "latency"
        assert agg.count == 5
        assert agg.min_value == 100.0
        assert agg.max_value == 140.0
        assert agg.avg_value == 120.0

    def test_aggregate_metrics_multiple_periods(self, collector, scenario):
        """Test aggregating metrics across multiple periods."""
        # Use a fixed time at the start of a minute to avoid boundary issues
        now = datetime.utcnow().replace(second=0, microsecond=0)
        
        # Record metrics in different minutes
        for minute in range(3):
            for i in range(3):
                collector.record_metric(
                    scenario.id,
                    "latency",
                    100.0 + i * 10,
                    timestamp=now + timedelta(minutes=minute, seconds=i*10)
                )

        aggregated = collector.aggregate_metrics(
            scenario_id=scenario.id,
            metric_name="latency",
            period=AggregationPeriod.ONE_MINUTE,
            start_time=now,
            end_time=now + timedelta(minutes=3)
        )

        assert len(aggregated) >= 3

    def test_aggregate_metrics_empty_scenario_id_raises_error(self, collector):
        """Test aggregating metrics with empty scenario_id raises error."""
        with pytest.raises(ValueError):
            collector.aggregate_metrics(
                scenario_id="",
                period=AggregationPeriod.ONE_MINUTE
            )

    def test_aggregate_metrics_nonexistent_scenario(self, collector):
        """Test aggregating metrics for nonexistent scenario returns empty."""
        aggregated = collector.aggregate_metrics(
            scenario_id="nonexistent",
            period=AggregationPeriod.ONE_MINUTE
        )
        assert len(aggregated) == 0


class TestMetricsCollectorStatistics:
    """Test metrics statistics functionality."""

    def test_get_metrics_statistics(self, collector, scenario):
        """Test getting statistics for a metric."""
        values = [100.0, 110.0, 120.0, 130.0, 140.0]
        for value in values:
            collector.record_metric(scenario.id, "latency", value)

        stats = collector.get_metrics_statistics(
            scenario_id=scenario.id,
            metric_name="latency"
        )

        assert stats["count"] == 5
        assert stats["min"] == 100.0
        assert stats["max"] == 140.0
        assert stats["avg"] == 120.0
        assert stats["sum"] == 600.0

    def test_get_metrics_statistics_empty_scenario_id_raises_error(self, collector):
        """Test getting statistics with empty scenario_id raises error."""
        with pytest.raises(ValueError):
            collector.get_metrics_statistics(
                scenario_id="",
                metric_name="latency"
            )

    def test_get_metrics_statistics_empty_metric_name_raises_error(self, collector, scenario):
        """Test getting statistics with empty metric_name raises error."""
        with pytest.raises(ValueError):
            collector.get_metrics_statistics(
                scenario_id=scenario.id,
                metric_name=""
            )

    def test_get_metrics_statistics_nonexistent_metric(self, collector, scenario):
        """Test getting statistics for nonexistent metric returns zeros."""
        stats = collector.get_metrics_statistics(
            scenario_id=scenario.id,
            metric_name="nonexistent"
        )

        assert stats["count"] == 0
        assert stats["min"] is None
        assert stats["max"] is None
        assert stats["avg"] is None
        assert stats["sum"] is None


class TestMetricsCollectorReporting:
    """Test performance report generation."""

    def test_generate_report(self, collector, scenario):
        """Test generating performance report."""
        # Record some metrics
        for i in range(10):
            collector.record_metric(scenario.id, "latency", 100.0 + i * 5)
            collector.record_metric(scenario.id, "throughput", 500.0 + i * 10)

        # Update scenario end time
        session = get_session()
        try:
            # Refresh the scenario from the database
            updated_scenario = session.query(Scenario).filter(
                Scenario.id == scenario.id
            ).first()
            if updated_scenario:
                updated_scenario.end_time = datetime.utcnow()
                session.commit()
        finally:
            close_session(session)

        report = collector.generate_report(scenario.id)

        assert report.scenario_id == scenario.id
        assert report.scenario_name == scenario.name
        assert report.duration_seconds >= 0
        assert "latency" in report.metrics_summary
        assert "throughput" in report.metrics_summary
        assert report.metrics_summary["latency"]["count"] == 10
        assert report.metrics_summary["throughput"]["count"] == 10

    def test_generate_report_nonexistent_scenario_raises_error(self, collector):
        """Test generating report for nonexistent scenario raises error."""
        with pytest.raises(ValueError):
            collector.generate_report("nonexistent")

    def test_generate_report_with_errors(self, collector, scenario):
        """Test generating report with error metrics."""
        collector.record_metric(scenario.id, "latency", 100.0)
        collector.record_metric(scenario.id, "error", 1.0)
        collector.record_metric(scenario.id, "error", 1.0)

        session = get_session()
        try:
            # Refresh the scenario from the database
            updated_scenario = session.query(Scenario).filter(
                Scenario.id == scenario.id
            ).first()
            if updated_scenario:
                updated_scenario.end_time = datetime.utcnow()
                session.commit()
        finally:
            close_session(session)

        report = collector.generate_report(scenario.id)

        assert report.error_count == 2


class TestMetricsCollectorCleanup:
    """Test metrics cleanup functionality."""

    def test_cleanup_old_metrics(self, collector, scenario):
        """Test cleaning up old metrics."""
        now = datetime.utcnow()
        old_time = now - timedelta(days=35)

        # Record old metric
        collector.record_metric(
            scenario.id,
            "latency",
            100.0,
            timestamp=old_time
        )

        # Record recent metric
        collector.record_metric(
            scenario.id,
            "latency",
            110.0,
            timestamp=now
        )

        # Cleanup metrics older than 30 days
        deleted_count = collector.cleanup_old_metrics(retention_days=30)

        assert deleted_count == 1

        # Verify recent metric still exists
        metrics = collector.get_metrics(scenario_id=scenario.id)
        assert len(metrics) == 1
        assert metrics[0].value == 110.0

    def test_cleanup_negative_retention_days_raises_error(self, collector):
        """Test cleanup with negative retention_days raises error."""
        with pytest.raises(ValueError):
            collector.cleanup_old_metrics(retention_days=-1)


class TestMetricsCollectorIntegration:
    """Integration tests for metrics collector."""

    def test_complete_metrics_workflow(self, collector, scenario):
        """Test complete metrics workflow."""
        # Record metrics
        metrics_data = [
            ("latency", 100.0, {"device": "solar-1"}),
            ("latency", 110.0, {"device": "solar-1"}),
            ("latency", 120.0, {"device": "solar-1"}),
            ("throughput", 500.0, {"device": "solar-1"}),
            ("throughput", 510.0, {"device": "solar-1"}),
        ]

        collector.record_metrics_batch(scenario.id, metrics_data)

        # Query metrics
        latency_metrics = collector.get_metrics(
            scenario_id=scenario.id,
            metric_name="latency"
        )
        assert len(latency_metrics) == 3

        # Get statistics
        stats = collector.get_metrics_statistics(
            scenario_id=scenario.id,
            metric_name="latency"
        )
        assert stats["count"] == 3
        assert stats["avg"] == 110.0

        # Aggregate metrics
        aggregated = collector.aggregate_metrics(
            scenario_id=scenario.id,
            period=AggregationPeriod.ONE_MINUTE
        )
        assert len(aggregated) > 0

        # Generate report
        session = get_session()
        try:
            scenario.end_time = datetime.utcnow()
            session.commit()
        finally:
            close_session(session)

        report = collector.generate_report(scenario.id)
        assert report.scenario_id == scenario.id
        assert len(report.metrics_summary) == 2

    def test_multiple_scenarios_metrics_isolation(self, collector):
        """Test metrics isolation between scenarios."""
        session = get_session()
        try:
            # Create two scenarios
            scenario1 = Scenario(
                id="scenario-1",
                name="Scenario 1",
                definition={},
                status=ScenarioStatus.RUNNING.value,
                start_time=datetime.utcnow()
            )
            scenario2 = Scenario(
                id="scenario-2",
                name="Scenario 2",
                definition={},
                status=ScenarioStatus.RUNNING.value,
                start_time=datetime.utcnow()
            )
            session.add_all([scenario1, scenario2])
            session.commit()

            # Record metrics for each scenario
            collector.record_metric(scenario1.id, "latency", 100.0)
            collector.record_metric(scenario2.id, "latency", 200.0)

            # Verify isolation
            metrics1 = collector.get_metrics(scenario_id=scenario1.id)
            metrics2 = collector.get_metrics(scenario_id=scenario2.id)

            assert len(metrics1) == 1
            assert len(metrics2) == 1
            assert metrics1[0].value == 100.0
            assert metrics2[0].value == 200.0
        finally:
            close_session(session)
