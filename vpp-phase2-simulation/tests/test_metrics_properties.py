"""
Property-based tests for Metrics Collector.

Tests correctness properties using Hypothesis framework.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
from typing import List, Dict
import uuid

from services.metrics_collector import (
    MetricsCollector,
    AggregationPeriod
)
from models.scenario import Scenario, ScenarioStatus
from models.metrics import Metric
from utils.database import get_session, close_session, init_db, drop_db


@pytest.fixture(scope="function")
def setup_db():
    """Set up test database."""
    init_db()
    yield
    drop_db()


@pytest.fixture
def collector(setup_db):
    """Create metrics collector instance."""
    return MetricsCollector()


@pytest.fixture
def scenario(setup_db):
    """Create test scenario with unique ID."""
    session = get_session()
    try:
        # Use unique ID to avoid conflicts between Hypothesis examples
        scenario_id = f"test-scenario-{uuid.uuid4().hex[:8]}"
        scenario = Scenario(
            id=scenario_id,
            name="Test Scenario",
            definition={},
            status=ScenarioStatus.RUNNING.value,
            start_time=datetime.utcnow()
        )
        session.add(scenario)
        session.commit()
        return scenario
    finally:
        close_session(session)


class TestMetricsCollectionProperties:
    """Property-based tests for metrics collection."""

    @given(
        metric_name=st.text(min_size=1, max_size=100),
        value=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
        tags=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.text(max_size=100),
            max_size=5
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    def test_property_51_metrics_collection_during_simulation(
        self,
        collector,
        scenario,
        metric_name,
        value,
        tags
    ):
        """
        **Property 51: Metrics Collection During Simulation**

        *For any* running simulation, the system should collect metrics
        (latency, throughput, error rate) continuously.

        **Validates: Requirements 11.1**
        """
        # Clear any existing metrics for this scenario to ensure isolation
        session = get_session()
        try:
            session.query(Metric).filter(Metric.scenario_id == scenario.id).delete()
            session.commit()
        finally:
            close_session(session)
        
        # Record metric
        collector.record_metric(
            scenario_id=scenario.id,
            metric_name=metric_name,
            value=value,
            tags=tags
        )

        # Verify metric was recorded
        metrics = collector.get_metrics(
            scenario_id=scenario.id,
            metric_name=metric_name
        )

        assert len(metrics) == 1
        assert metrics[0].metric_name == metric_name
        assert metrics[0].value == value
        assert metrics[0].scenario_id == scenario.id
        assert metrics[0].timestamp is not None

    @given(
        num_metrics=st.integers(min_value=1, max_value=100),
        metric_name=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    def test_property_52_metrics_aggregation(
        self,
        collector,
        scenario,
        num_metrics,
        metric_name
    ):
        """
        **Property 52: Metrics Aggregation**

        *For any* set of collected metrics, the system should aggregate
        data by time period (1s, 1m, 1h) correctly.

        **Validates: Requirements 11.2**
        """
        # Clear any existing metrics for this scenario to ensure isolation
        session = get_session()
        try:
            session.query(Metric).filter(Metric.scenario_id == scenario.id).delete()
            session.commit()
        finally:
            close_session(session)
        
        # Record multiple metrics
        values = []
        now = datetime.utcnow()
        for i in range(num_metrics):
            value = float(i * 10)
            values.append(value)
            collector.record_metric(
                scenario_id=scenario.id,
                metric_name=metric_name,
                value=value,
                timestamp=now + timedelta(seconds=i)
            )

        # Aggregate by 1-minute period
        aggregated = collector.aggregate_metrics(
            scenario_id=scenario.id,
            metric_name=metric_name,
            period=AggregationPeriod.ONE_MINUTE
        )

        # Verify aggregation
        assert len(aggregated) > 0
        
        # Verify aggregated metrics are correct
        total_sum = 0
        total_count = 0
        for agg in aggregated:
            assert agg.metric_name == metric_name
            assert agg.count > 0
            assert agg.min_value <= agg.avg_value <= agg.max_value
            total_sum += agg.sum_value
            total_count += agg.count
        
        # Verify total sum and count match
        assert total_sum == sum(values)
        assert total_count == num_metrics

    @given(
        num_metrics=st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    def test_property_53_metrics_query_performance(
        self,
        collector,
        scenario,
        num_metrics
    ):
        """
        **Property 53: Metrics Query Performance**

        *For any* metrics query, the system should return aggregated data
        with statistics within 1 second.

        **Validates: Requirements 11.3**
        """
        # Record metrics
        for i in range(num_metrics):
            collector.record_metric(
                scenario_id=scenario.id,
                metric_name="latency",
                value=float(100 + i)
            )

        # Query metrics and measure time
        import time
        start_time = time.time()
        
        aggregated = collector.aggregate_metrics(
            scenario_id=scenario.id,
            metric_name="latency",
            period=AggregationPeriod.ONE_MINUTE
        )
        
        elapsed_time = time.time() - start_time

        # Verify query completed within 1 second
        assert elapsed_time < 1.0
        assert len(aggregated) > 0

    def test_property_54_performance_report_generation(
        self,
        collector,
        scenario
    ):
        """
        **Property 54: Performance Report Generation**

        *For any* completed simulation, the system should generate a
        performance report with all metrics and analysis.

        **Validates: Requirements 11.4**
        """
        # Record metrics
        for i in range(10):
            collector.record_metric(
                scenario_id=scenario.id,
                metric_name="latency",
                value=100.0 + i * 5
            )
            collector.record_metric(
                scenario_id=scenario.id,
                metric_name="throughput",
                value=500.0 + i * 10
            )

        # Update scenario end time
        session = get_session()
        try:
            scenario.end_time = datetime.utcnow()
            session.commit()
        finally:
            close_session(session)

        # Generate report
        report = collector.generate_report(scenario.id)

        # Verify report contains all required information
        assert report.scenario_id == scenario.id
        assert report.scenario_name is not None
        assert report.start_time is not None
        assert report.end_time is not None
        assert report.duration_seconds >= 0
        assert report.metrics_summary is not None
        assert len(report.metrics_summary) > 0
        assert report.aggregated_metrics is not None

    @given(
        num_metrics=st.integers(min_value=4, max_value=100),
        retention_days=st.integers(min_value=30, max_value=60)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    def test_property_55_historical_metrics_retention(
        self,
        collector,
        scenario,
        num_metrics,
        retention_days
    ):
        """
        **Property 55: Historical Metrics Retention**

        *For any* metrics collected, the system should maintain at least
        30 days of historical data without data loss.

        **Validates: Requirements 11.5**
        """
        # Clear any existing metrics for this scenario to ensure isolation
        session = get_session()
        try:
            session.query(Metric).filter(Metric.scenario_id == scenario.id).delete()
            session.commit()
        finally:
            close_session(session)
        
        # Record metrics at various times
        now = datetime.utcnow()
        
        # Split metrics evenly between recent and old
        recent_count = num_metrics // 2
        old_count = num_metrics - recent_count
        
        # Record recent metrics (within retention period)
        for i in range(recent_count):
            collector.record_metric(
                scenario_id=scenario.id,
                metric_name="latency",
                value=100.0 + i,
                timestamp=now - timedelta(days=5)
            )

        # Record old metrics (outside retention period)
        for i in range(old_count):
            collector.record_metric(
                scenario_id=scenario.id,
                metric_name="latency",
                value=200.0 + i,
                timestamp=now - timedelta(days=retention_days + 10)
            )

        # Get all metrics before cleanup
        all_metrics_before = collector.get_metrics(scenario_id=scenario.id)
        assert len(all_metrics_before) == num_metrics

        # Cleanup old metrics
        deleted_count = collector.cleanup_old_metrics(retention_days=retention_days)

        # Verify old metrics were deleted
        assert deleted_count == old_count

        # Verify recent metrics still exist
        all_metrics_after = collector.get_metrics(scenario_id=scenario.id)
        assert len(all_metrics_after) == recent_count

        # Verify all remaining metrics are recent
        for metric in all_metrics_after:
            assert metric.value >= 100.0  # Recent metrics


class TestMetricsAggregationProperties:
    """Property-based tests for metrics aggregation."""

    @given(
        values=st.lists(
            st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=100
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    def test_aggregation_statistics_correctness(
        self,
        collector,
        scenario,
        values
    ):
        """Test that aggregation statistics are mathematically correct."""
        # Clear any existing metrics for this scenario to ensure isolation
        session = get_session()
        try:
            session.query(Metric).filter(Metric.scenario_id == scenario.id).delete()
            session.commit()
        finally:
            close_session(session)
        
        # Record metrics
        now = datetime.utcnow()
        for i, value in enumerate(values):
            collector.record_metric(
                scenario_id=scenario.id,
                metric_name="test_metric",
                value=value,
                timestamp=now + timedelta(seconds=i)
            )

        # Get statistics
        stats = collector.get_metrics_statistics(
            scenario_id=scenario.id,
            metric_name="test_metric"
        )

        # Verify statistics are correct
        assert stats["count"] == len(values)
        assert stats["min"] == min(values)
        assert stats["max"] == max(values)
        assert abs(stats["avg"] - (sum(values) / len(values))) < 0.0001
        assert stats["sum"] == sum(values)

    @given(
        num_metrics=st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    def test_aggregation_preserves_data_integrity(
        self,
        collector,
        scenario,
        num_metrics
    ):
        """Test that aggregation preserves data integrity."""
        # Clear any existing metrics for this scenario to ensure isolation
        session = get_session()
        try:
            session.query(Metric).filter(Metric.scenario_id == scenario.id).delete()
            session.commit()
        finally:
            close_session(session)
        
        # Record metrics
        values = []
        now = datetime.utcnow()
        for i in range(num_metrics):
            value = float(100 + i * 10)
            values.append(value)
            collector.record_metric(
                scenario_id=scenario.id,
                metric_name="latency",
                value=value,
                timestamp=now + timedelta(seconds=i)
            )

        # Get raw metrics
        raw_metrics = collector.get_metrics(
            scenario_id=scenario.id,
            metric_name="latency"
        )

        # Verify all metrics are present
        assert len(raw_metrics) == num_metrics
        
        # Verify values match
        raw_values = sorted([m.value for m in raw_metrics])
        assert raw_values == sorted(values)


class TestMetricsIsolationProperties:
    """Property-based tests for metrics isolation."""

    @given(
        num_scenarios=st.integers(min_value=2, max_value=5),
        metrics_per_scenario=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    def test_metrics_isolation_between_scenarios(
        self,
        collector,
        num_scenarios,
        metrics_per_scenario
    ):
        """Test that metrics are properly isolated between scenarios."""
        session = get_session()
        try:
            # Clear all metrics first to ensure isolation
            session.query(Metric).delete()
            session.commit()
            
            # Create multiple scenarios with unique IDs
            scenarios = []
            for i in range(num_scenarios):
                scenario = Scenario(
                    id=f"scenario-{uuid.uuid4().hex[:8]}-{i}",
                    name=f"Scenario {i}",
                    definition={},
                    status=ScenarioStatus.RUNNING.value,
                    start_time=datetime.utcnow()
                )
                session.add(scenario)
                scenarios.append(scenario)
            session.commit()

            # Record metrics for each scenario
            for scenario in scenarios:
                for j in range(metrics_per_scenario):
                    collector.record_metric(
                        scenario_id=scenario.id,
                        metric_name="latency",
                        value=float(100 + j)
                    )

            # Verify isolation
            for scenario in scenarios:
                metrics = collector.get_metrics(scenario_id=scenario.id)
                assert len(metrics) == metrics_per_scenario
                
                # Verify all metrics belong to this scenario
                for metric in metrics:
                    assert metric.scenario_id == scenario.id
        finally:
            close_session(session)
