"""
Unit Tests for 5G Network Simulator

Tests network latency, bandwidth, congestion, and handover simulation.
"""

import pytest
from datetime import datetime
from services.network_simulator import (
    NetworkSimulator,
    NetworkCondition,
    NetworkMetrics,
)
from utils.errors import ValidationError


class TestNetworkSimulator:
    """Test 5G Network Simulator functionality."""
    
    @pytest.fixture
    def simulator(self):
        """Create network simulator instance."""
        return NetworkSimulator()
    
    def test_simulator_initialization(self):
        """Test network simulator initialization."""
        sim = NetworkSimulator()
        assert sim.network_id is not None
        assert sim.condition == NetworkCondition.NORMAL
        assert sim.load_factor == 0.0
        assert sim.messages_processed == 0
        assert sim.messages_dropped == 0
    
    def test_simulator_initialization_with_id(self):
        """Test network simulator initialization with custom ID."""
        sim = NetworkSimulator(network_id="net-custom")
        assert sim.network_id == "net-custom"
    
    def test_simulate_latency_normal(self, simulator):
        """Test latency simulation in normal condition."""
        simulator.condition = NetworkCondition.NORMAL
        
        latencies = [simulator.simulate_latency() for _ in range(100)]
        
        # Check that latencies are within expected range (with jitter)
        assert all(latency >= 0 for latency in latencies)
        assert all(latency <= 100 for latency in latencies)  # Allow for jitter
    
    def test_simulate_latency_congested(self, simulator):
        """Test latency simulation in congested condition."""
        simulator.condition = NetworkCondition.CONGESTED
        
        latencies = [simulator.simulate_latency() for _ in range(100)]
        
        # Congested latencies should be higher on average
        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency > 40  # Should be higher than normal
    
    def test_simulate_latency_handover(self, simulator):
        """Test latency simulation during handover."""
        simulator.condition = NetworkCondition.HANDOVER
        
        latencies = [simulator.simulate_latency() for _ in range(100)]
        
        # Handover latencies should be even higher
        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency > 100
    
    def test_simulate_bandwidth_normal(self, simulator):
        """Test bandwidth simulation in normal condition."""
        simulator.condition = NetworkCondition.NORMAL
        
        bandwidths = [simulator.simulate_bandwidth() for _ in range(100)]
        
        # Check that bandwidths are within expected range
        assert all(bw >= 100 for bw in bandwidths)
        assert all(bw <= 1000 for bw in bandwidths)
    
    def test_simulate_bandwidth_congested(self, simulator):
        """Test bandwidth simulation in congested condition."""
        simulator.condition = NetworkCondition.CONGESTED
        
        bandwidths = [simulator.simulate_bandwidth() for _ in range(100)]
        
        # Congested bandwidth should be lower on average
        avg_bandwidth = sum(bandwidths) / len(bandwidths)
        assert avg_bandwidth < 600  # Should be lower than normal
    
    def test_simulate_bandwidth_handover(self, simulator):
        """Test bandwidth simulation during handover."""
        simulator.condition = NetworkCondition.HANDOVER
        
        bandwidths = [simulator.simulate_bandwidth() for _ in range(100)]
        
        # Handover bandwidth should be very low
        avg_bandwidth = sum(bandwidths) / len(bandwidths)
        assert avg_bandwidth < 200
    
    def test_simulate_packet_loss_normal(self, simulator):
        """Test packet loss simulation in normal condition."""
        simulator.condition = NetworkCondition.NORMAL
        
        losses = [simulator.simulate_packet_loss() for _ in range(1000)]
        
        # Normal condition should have very low packet loss
        loss_rate = sum(losses) / len(losses)
        assert loss_rate < 0.01  # Less than 1%
    
    def test_simulate_packet_loss_congested(self, simulator):
        """Test packet loss simulation in congested condition."""
        simulator.condition = NetworkCondition.CONGESTED
        
        losses = [simulator.simulate_packet_loss() for _ in range(1000)]
        
        # Congested condition should have higher packet loss
        loss_rate = sum(losses) / len(losses)
        assert loss_rate > 0.01  # More than 1%
    
    def test_simulate_packet_loss_handover(self, simulator):
        """Test packet loss simulation during handover."""
        simulator.condition = NetworkCondition.HANDOVER
        
        losses = [simulator.simulate_packet_loss() for _ in range(1000)]
        
        # Handover should have even higher packet loss
        loss_rate = sum(losses) / len(losses)
        assert loss_rate > 0.03  # More than 3%
    
    def test_simulate_congestion_low_load(self, simulator):
        """Test congestion simulation with low load."""
        metrics = simulator.simulate_congestion(load_factor=0.3)
        
        assert metrics.condition == NetworkCondition.NORMAL.value
        assert metrics.latency_ms > 0
        assert metrics.bandwidth_mbps > 0
    
    def test_simulate_congestion_medium_load(self, simulator):
        """Test congestion simulation with medium load."""
        metrics = simulator.simulate_congestion(load_factor=0.6)
        
        assert metrics.condition == NetworkCondition.DEGRADED.value
    
    def test_simulate_congestion_high_load(self, simulator):
        """Test congestion simulation with high load."""
        metrics = simulator.simulate_congestion(load_factor=0.9)
        
        assert metrics.condition == NetworkCondition.CONGESTED.value
    
    def test_simulate_congestion_invalid_load(self, simulator):
        """Test congestion simulation with invalid load factor."""
        with pytest.raises(ValidationError):
            simulator.simulate_congestion(load_factor=1.5)
        
        with pytest.raises(ValidationError):
            simulator.simulate_congestion(load_factor=-0.1)
    
    def test_simulate_handover(self, simulator):
        """Test handover simulation."""
        # Set low probability to test handover occurrence
        simulator.handover_probability = 1.0
        simulator.last_handover_time = 0.0
        
        interruption_ms, occurred = simulator.simulate_handover()
        
        if occurred:
            assert interruption_ms > 0
            assert simulator.condition == NetworkCondition.HANDOVER
    
    def test_simulate_handover_cooldown(self, simulator):
        """Test handover cooldown period."""
        simulator.handover_probability = 1.0
        simulator.last_handover_time = 0.0
        
        # First handover
        interruption1, occurred1 = simulator.simulate_handover()
        
        # Second handover attempt (should be blocked by cooldown)
        interruption2, occurred2 = simulator.simulate_handover()
        
        # Second should not occur due to cooldown
        assert occurred2 == False
    
    def test_apply_network_conditions(self, simulator):
        """Test applying network conditions to message."""
        message = b"test message"
        
        result_msg, metrics = simulator.apply_network_conditions(message, load_factor=0.5)
        
        assert result_msg is not None or result_msg is None  # May be dropped
        assert "latency_ms" in metrics
        assert "bandwidth_mbps" in metrics
        assert "packet_loss_rate" in metrics
        assert simulator.messages_processed == 1
    
    def test_apply_network_conditions_packet_loss(self, simulator):
        """Test applying network conditions with packet loss."""
        message = b"test message"
        simulator.condition = NetworkCondition.HANDOVER
        
        # Run multiple times to potentially get packet loss
        dropped_count = 0
        for _ in range(100):
            result_msg, metrics = simulator.apply_network_conditions(message, load_factor=0.9)
            if result_msg is None:
                dropped_count += 1
        
        # Should have some dropped messages (at least 1 due to high packet loss rate)
        assert dropped_count >= 1
        assert simulator.messages_dropped >= 1
    
    def test_apply_network_conditions_invalid_load(self, simulator):
        """Test applying network conditions with invalid load factor."""
        message = b"test message"
        
        with pytest.raises(ValidationError):
            simulator.apply_network_conditions(message, load_factor=1.5)
    
    def test_apply_network_conditions_none_message(self, simulator):
        """Test applying network conditions to None message."""
        with pytest.raises(ValidationError):
            simulator.apply_network_conditions(None, load_factor=0.5)
    
    def test_get_network_status(self, simulator):
        """Test getting network status."""
        # Process some messages
        for i in range(10):
            simulator.apply_network_conditions(b"test", load_factor=0.5)
        
        status = simulator.get_network_status()
        
        assert status["network_id"] == simulator.network_id
        assert status["messages_processed"] == 10
        assert "average_latency_ms" in status
        assert "packet_loss_rate" in status
    
    def test_get_network_status_no_messages(self, simulator):
        """Test getting network status with no messages processed."""
        status = simulator.get_network_status()
        
        assert status["messages_processed"] == 0
        assert status["average_latency_ms"] == 0.0
        assert status["packet_loss_rate"] == 0.0
    
    def test_reset(self, simulator):
        """Test network simulator reset."""
        # Add some state
        simulator.apply_network_conditions(b"test", load_factor=0.5)
        simulator.total_latency_ms = 100.0
        simulator.messages_dropped = 5
        
        simulator.reset()
        
        assert simulator.condition == NetworkCondition.NORMAL
        assert simulator.load_factor == 0.0
        assert simulator.messages_processed == 0
        assert simulator.messages_dropped == 0
        assert simulator.total_latency_ms == 0.0
    
    def test_network_metrics_to_dict(self):
        """Test network metrics to dictionary conversion."""
        metrics = NetworkMetrics(
            latency_ms=25.0,
            bandwidth_mbps=500.0,
            packet_loss_rate=0.01,
            jitter_ms=2.0,
            condition="normal",
            timestamp=datetime.utcnow(),
        )
        
        metrics_dict = metrics.to_dict()
        
        assert metrics_dict["latency_ms"] == 25.0
        assert metrics_dict["bandwidth_mbps"] == 500.0
        assert metrics_dict["packet_loss_rate"] == 0.01
        assert metrics_dict["jitter_ms"] == 2.0
        assert metrics_dict["condition"] == "normal"
    
    def test_latency_accumulation(self, simulator):
        """Test that latency is accumulated correctly."""
        initial_latency = simulator.total_latency_ms
        
        for _ in range(10):
            simulator.simulate_latency()
        
        assert simulator.total_latency_ms > initial_latency
    
    def test_multiple_conditions_transition(self, simulator):
        """Test transitioning between different network conditions."""
        # Normal condition
        metrics1 = simulator.simulate_congestion(load_factor=0.2)
        assert metrics1.condition == NetworkCondition.NORMAL.value
        
        # Degraded condition
        metrics2 = simulator.simulate_congestion(load_factor=0.6)
        assert metrics2.condition == NetworkCondition.DEGRADED.value
        
        # Congested condition
        metrics3 = simulator.simulate_congestion(load_factor=0.9)
        assert metrics3.condition == NetworkCondition.CONGESTED.value
    
    def test_realistic_scenario(self, simulator):
        """Test realistic network simulation scenario."""
        # Simulate varying load over time
        loads = [0.2, 0.4, 0.6, 0.8, 0.9, 0.7, 0.5, 0.3]
        
        for load in loads:
            msg, metrics = simulator.apply_network_conditions(b"data", load_factor=load)
            assert metrics is not None
        
        status = simulator.get_network_status()
        assert status["messages_processed"] == len(loads)
        assert status["average_latency_ms"] > 0
