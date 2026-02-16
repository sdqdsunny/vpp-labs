"""
5G Network Simulator

Simulates 5G network characteristics including latency, bandwidth, congestion,
and handover interruptions.
"""

import logging
import random
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from utils.errors import ValidationError
from utils.logger import get_logger

logger = get_logger(__name__)


class NetworkCondition(Enum):
    """Network condition states."""
    NORMAL = "normal"
    CONGESTED = "congested"
    HANDOVER = "handover"
    DEGRADED = "degraded"


@dataclass
class NetworkMetrics:
    """Network performance metrics."""
    latency_ms: float
    bandwidth_mbps: float
    packet_loss_rate: float
    jitter_ms: float
    condition: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "latency_ms": self.latency_ms,
            "bandwidth_mbps": self.bandwidth_mbps,
            "packet_loss_rate": self.packet_loss_rate,
            "jitter_ms": self.jitter_ms,
            "condition": self.condition,
            "timestamp": self.timestamp.isoformat(),
        }


class NetworkSimulator:
    """
    5G Network Simulator
    
    Simulates 5G network characteristics for VPP operations.
    Models latency, bandwidth, congestion, and handover effects.
    
    Requirements:
    - 6.1: Model latency (10-50ms typical, up to 100ms under load)
    - 6.2: Model bandwidth (100Mbps to 1Gbps)
    - 6.3: Simulate network congestion
    - 6.4: Simulate handover interruptions (100-500ms)
    - 6.5: Maintain realistic network behavior
    """
    
    # Latency ranges (milliseconds)
    LATENCY_NORMAL_MIN = 10
    LATENCY_NORMAL_MAX = 50
    LATENCY_CONGESTED_MIN = 50
    LATENCY_CONGESTED_MAX = 100
    LATENCY_HANDOVER_MIN = 100
    LATENCY_HANDOVER_MAX = 500
    
    # Bandwidth ranges (Mbps)
    BANDWIDTH_MIN = 100
    BANDWIDTH_MAX = 1000
    BANDWIDTH_CONGESTED_FACTOR = 0.5  # 50% reduction during congestion
    
    # Packet loss rates
    PACKET_LOSS_NORMAL = 0.0
    PACKET_LOSS_CONGESTED = 0.02  # 2%
    PACKET_LOSS_HANDOVER = 0.05   # 5%
    
    # Jitter (milliseconds)
    JITTER_NORMAL = 1.0
    JITTER_CONGESTED = 5.0
    JITTER_HANDOVER = 20.0
    
    def __init__(self, network_id: Optional[str] = None):
        """
        Initialize 5G Network Simulator.
        
        Args:
            network_id: Unique network identifier
        """
        self.network_id = network_id or f"net-{random.randint(1000, 9999)}"
        self.condition = NetworkCondition.NORMAL
        self.load_factor = 0.0  # 0.0 to 1.0
        self.congestion_probability = 0.1
        self.handover_probability = 0.05
        self.messages_processed = 0
        self.messages_dropped = 0
        self.total_latency_ms = 0.0
        self.last_handover_time = 0.0
        self.handover_cooldown = 5.0  # seconds
        
        logger.info(f"5G Network Simulator initialized: {self.network_id}")
    
    def simulate_latency(self) -> float:
        """
        Simulate network latency based on current condition.
        
        Returns:
            Latency in milliseconds
        """
        if self.condition == NetworkCondition.NORMAL:
            base_latency = random.uniform(
                self.LATENCY_NORMAL_MIN,
                self.LATENCY_NORMAL_MAX
            )
            jitter = random.gauss(0, self.JITTER_NORMAL)
        elif self.condition == NetworkCondition.CONGESTED:
            base_latency = random.uniform(
                self.LATENCY_CONGESTED_MIN,
                self.LATENCY_CONGESTED_MAX
            )
            jitter = random.gauss(0, self.JITTER_CONGESTED)
        elif self.condition == NetworkCondition.HANDOVER:
            base_latency = random.uniform(
                self.LATENCY_HANDOVER_MIN,
                self.LATENCY_HANDOVER_MAX
            )
            jitter = random.gauss(0, self.JITTER_HANDOVER)
        else:  # DEGRADED
            base_latency = random.uniform(
                self.LATENCY_CONGESTED_MIN,
                self.LATENCY_HANDOVER_MAX
            )
            jitter = random.gauss(0, self.JITTER_CONGESTED)
        
        latency = max(0, base_latency + jitter)
        self.total_latency_ms += latency
        
        return latency
    
    def simulate_bandwidth(self) -> float:
        """
        Simulate available bandwidth based on current condition.
        
        Returns:
            Bandwidth in Mbps
        """
        base_bandwidth = random.uniform(self.BANDWIDTH_MIN, self.BANDWIDTH_MAX)
        
        if self.condition == NetworkCondition.CONGESTED:
            bandwidth = base_bandwidth * self.BANDWIDTH_CONGESTED_FACTOR
        elif self.condition == NetworkCondition.HANDOVER:
            bandwidth = base_bandwidth * 0.1  # 10% during handover
        else:
            bandwidth = base_bandwidth
        
        return max(self.BANDWIDTH_MIN, bandwidth)
    
    def simulate_packet_loss(self) -> bool:
        """
        Simulate packet loss based on current condition.
        
        Returns:
            True if packet is lost, False otherwise
        """
        if self.condition == NetworkCondition.NORMAL:
            loss_rate = self.PACKET_LOSS_NORMAL
        elif self.condition == NetworkCondition.CONGESTED:
            loss_rate = self.PACKET_LOSS_CONGESTED
        elif self.condition == NetworkCondition.HANDOVER:
            loss_rate = self.PACKET_LOSS_HANDOVER
        else:  # DEGRADED
            loss_rate = self.PACKET_LOSS_CONGESTED
        
        if random.random() < loss_rate:
            self.messages_dropped += 1
            return True
        
        return False
    
    def simulate_congestion(self, load_factor: float) -> NetworkMetrics:
        """
        Simulate network congestion based on load factor.
        
        Args:
            load_factor: Load factor (0.0 to 1.0)
            
        Returns:
            Network metrics
            
        Raises:
            ValidationError: If load_factor is invalid
        """
        if not 0.0 <= load_factor <= 1.0:
            raise ValidationError("Load factor must be 0.0-1.0")
        
        self.load_factor = load_factor
        
        # Determine condition based on load
        if load_factor > 0.8:
            self.condition = NetworkCondition.CONGESTED
        elif load_factor > 0.5:
            self.condition = NetworkCondition.DEGRADED
        else:
            self.condition = NetworkCondition.NORMAL
        
        # Simulate metrics
        latency = self.simulate_latency()
        bandwidth = self.simulate_bandwidth()
        packet_loss = self.simulate_packet_loss()
        
        metrics = NetworkMetrics(
            latency_ms=latency,
            bandwidth_mbps=bandwidth,
            packet_loss_rate=self.PACKET_LOSS_CONGESTED if packet_loss else 0.0,
            jitter_ms=self._get_jitter(),
            condition=self.condition.value,
            timestamp=datetime.utcnow(),
        )
        
        logger.info(
            f"Network congestion simulated: "
            f"load={load_factor:.2f}, condition={self.condition.value}, "
            f"latency={latency:.1f}ms, bandwidth={bandwidth:.1f}Mbps"
        )
        
        return metrics
    
    def simulate_handover(self) -> Tuple[float, bool]:
        """
        Simulate 5G handover event.
        
        Returns:
            Tuple of (interruption_duration_ms, handover_occurred)
        """
        current_time = time.time()
        time_since_last_handover = current_time - self.last_handover_time
        
        # Check cooldown period
        if time_since_last_handover < self.handover_cooldown:
            return 0.0, False
        
        # Simulate handover probability
        if random.random() > self.handover_probability:
            return 0.0, False
        
        # Handover occurred
        self.condition = NetworkCondition.HANDOVER
        self.last_handover_time = current_time
        
        # Generate interruption duration
        interruption_ms = random.uniform(
            self.LATENCY_HANDOVER_MIN,
            self.LATENCY_HANDOVER_MAX
        )
        
        logger.warning(
            f"5G handover simulated: "
            f"interruption={interruption_ms:.1f}ms"
        )
        
        return interruption_ms, True
    
    def apply_network_conditions(
        self,
        message: bytes,
        load_factor: float = 0.0
    ) -> Tuple[Optional[bytes], Dict[str, Any]]:
        """
        Apply network conditions to message.
        
        Args:
            message: Message bytes
            load_factor: Network load factor (0.0-1.0)
            
        Returns:
            Tuple of (message or None if dropped, network_metrics)
            
        Raises:
            ValidationError: If parameters are invalid
        """
        if not message:
            raise ValidationError("Message cannot be None")
        
        if not 0.0 <= load_factor <= 1.0:
            raise ValidationError("Load factor must be 0.0-1.0")
        
        self.messages_processed += 1
        
        # Simulate congestion
        metrics = self.simulate_congestion(load_factor)
        
        # Simulate packet loss
        if self.simulate_packet_loss():
            logger.warning(f"Message dropped due to packet loss")
            return None, metrics.to_dict()
        
        # Simulate handover
        interruption_ms, handover_occurred = self.simulate_handover()
        if handover_occurred:
            metrics.latency_ms += interruption_ms
        
        return message, metrics.to_dict()
    
    def get_network_status(self) -> Dict[str, Any]:
        """
        Get current network status.
        
        Returns:
            Network status information
        """
        avg_latency = (
            self.total_latency_ms / self.messages_processed
            if self.messages_processed > 0
            else 0.0
        )
        
        return {
            "network_id": self.network_id,
            "condition": self.condition.value,
            "load_factor": self.load_factor,
            "messages_processed": self.messages_processed,
            "messages_dropped": self.messages_dropped,
            "average_latency_ms": avg_latency,
            "total_latency_ms": self.total_latency_ms,
            "packet_loss_rate": (
                self.messages_dropped / self.messages_processed
                if self.messages_processed > 0
                else 0.0
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def reset(self) -> None:
        """Reset network simulator state."""
        self.condition = NetworkCondition.NORMAL
        self.load_factor = 0.0
        self.messages_processed = 0
        self.messages_dropped = 0
        self.total_latency_ms = 0.0
        self.last_handover_time = 0.0
        logger.info(f"Network Simulator reset: {self.network_id}")
    
    def _get_jitter(self) -> float:
        """Get current jitter based on condition."""
        if self.condition == NetworkCondition.NORMAL:
            return self.JITTER_NORMAL
        elif self.condition == NetworkCondition.CONGESTED:
            return self.JITTER_CONGESTED
        elif self.condition == NetworkCondition.HANDOVER:
            return self.JITTER_HANDOVER
        else:
            return self.JITTER_CONGESTED
