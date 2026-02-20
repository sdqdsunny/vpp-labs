"""
DNP3 Attack Detection Module

This module provides anomaly detection for DNP3 protocol traffic by analyzing
packet parameters and identifying suspicious patterns.

Author: Kiro AI Assistant
Date: 2026-02-19
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """Severity levels for detected anomalies"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class DNP3AnomalyResult:
    """Result of DNP3 anomaly detection"""
    is_anomalous: bool
    anomalies: List[str] = field(default_factory=list)
    severity: SeverityLevel = SeverityLevel.LOW
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict = field(default_factory=dict)
    rule_violations: Dict = field(default_factory=dict)


class DNP3AttackDetector:
    """
    DNP3 Attack Detection Engine
    
    Detects anomalous DNP3 traffic by analyzing packet parameters:
    - Control field validation
    - Function code validation
    - Data length validation
    - Sequence number validation
    - Object type validation
    """
    
    # Valid DNP3 function codes
    VALID_FUNCTION_CODES = {
        0x00: "Confirm",
        0x01: "Read",
        0x02: "Write",
        0x03: "Select",
        0x04: "Operate",
        0x05: "Direct Operate",
        0x06: "Direct Operate No Ack",
        0x07: "Immediate Freeze",
        0x08: "Immediate Freeze No Ack",
        0x09: "Freeze and Clear",
        0x0A: "Freeze and Clear No Ack",
        0x0B: "Freeze With Time",
        0x0C: "Freeze With Time No Ack",
        0x0D: "Cold Restart",
        0x0E: "Warm Restart",
        0x0F: "Initialize Data",
        0x10: "Initialize Application",
        0x11: "Start Application",
        0x12: "Stop Application",
        0x13: "Save Configuration",
        0x14: "Enable Unsolicited",
        0x15: "Disable Unsolicited",
        0x16: "Assign Classes",
        0x17: "Delay Measurement",
        0x18: "Record Current Time",
        0x19: "Open File",
        0x1A: "Close File",
        0x1B: "Delete File",
        0x1C: "Get File Info",
        0x1D: "Authenticate File",
        0x1E: "Abort File",
        0x1F: "Activate Configuration",
        0x20: "Authentication Request",
        0x21: "Authentication Reply",
    }
    
    # Valid DNP3 object types
    VALID_OBJECT_TYPES = {
        1, 2, 3, 4,  # Binary Input
        10, 11, 12, 13,  # Binary Input Change
        20, 21, 22, 23,  # Binary Output
        30, 31, 32, 33,  # Binary Output Change
        40, 41, 42, 43,  # Counter
        50, 51, 52, 53,  # Counter Change
        60, 61, 62, 63,  # Analog Input
        70, 71, 72, 73,  # Analog Input Change
        80, 81, 82, 83,  # Analog Output
        90, 91, 92, 93,  # Analog Output Change
        100, 101, 102, 103,  # Time and Date
        110, 111, 112, 113,  # Class Data
        120, 121, 122, 123,  # File Control
    }
    
    def __init__(self):
        """Initialize the DNP3 Attack Detector"""
        self.logger = logging.getLogger(__name__)
        self.alarm_state = {
            'last_anomaly': None,
            'anomaly_count': 0,
            'is_alarmed': False,
        }
        self.packet_history = []
        self.max_history_size = 1000
        self.detection_rules = self._init_rules()
    
    def _init_rules(self) -> Dict:
        """Initialize detection rules"""
        return {
            'control_field': self._check_control_field,
            'function_code': self._check_function_code,
            'data_length': self._check_data_length,
            'sequence_number': self._check_sequence_number,
            'object_type': self._check_object_type,
        }
    
    def analyze_packet(self, packet_data: Dict) -> DNP3AnomalyResult:
        """
        Analyze a DNP3 packet for anomalies
        
        Args:
            packet_data: Dictionary containing DNP3 packet parameters
            
        Returns:
            DNP3AnomalyResult with detection results
        """
        anomalies = []
        severity = SeverityLevel.LOW
        rule_violations = {}
        
        # Apply all detection rules
        for rule_name, rule_func in self.detection_rules.items():
            try:
                result = rule_func(packet_data)
                rule_violations[rule_name] = result
                
                if not result['passed']:
                    anomalies.append(result['message'])
                    
                    # Update severity
                    rule_severity = SeverityLevel(result['severity'])
                    if rule_severity == SeverityLevel.HIGH:
                        severity = SeverityLevel.HIGH
                    elif rule_severity == SeverityLevel.MEDIUM and severity != SeverityLevel.HIGH:
                        severity = SeverityLevel.MEDIUM
                        
            except Exception as e:
                self.logger.error(f"Error in rule {rule_name}: {e}")
                rule_violations[rule_name] = {
                    'passed': False,
                    'message': f"Error executing rule: {str(e)}",
                    'severity': 'high'
                }
        
        is_anomalous = len(anomalies) > 0
        
        # Update alarm state
        if is_anomalous:
            self.alarm_state['last_anomaly'] = datetime.now()
            self.alarm_state['anomaly_count'] += 1
            self.alarm_state['is_alarmed'] = True
        
        # Add to history
        self._add_to_history(packet_data, is_anomalous)
        
        return DNP3AnomalyResult(
            is_anomalous=is_anomalous,
            anomalies=anomalies,
            severity=severity,
            timestamp=datetime.now(),
            details=packet_data,
            rule_violations=rule_violations
        )
    
    def _check_control_field(self, packet: Dict) -> Dict:
        """
        Check DNP3 control field validity
        
        Control field bits:
        - DIR (Direction): 0 or 1
        - PRM (Primary): 0 or 1
        - FCB (Frame Count Bit): 0 or 1
        - FCV (Frame Count Valid): 0 or 1
        """
        control_field = packet.get('control_field')
        
        if control_field is None:
            return {
                'passed': False,
                'message': 'Missing control field',
                'severity': 'high'
            }
        
        if not isinstance(control_field, int):
            return {
                'passed': False,
                'message': f'Invalid control field type: {type(control_field)}',
                'severity': 'high'
            }
        
        if not (0 <= control_field <= 255):
            return {
                'passed': False,
                'message': f'Control field out of range: {control_field}',
                'severity': 'high'
            }
        
        return {
            'passed': True,
            'message': 'Control field valid',
            'severity': 'low'
        }
    
    def _check_function_code(self, packet: Dict) -> Dict:
        """
        Check DNP3 function code validity
        
        Function code must be one of the valid DNP3 function codes
        """
        function_code = packet.get('function_code')
        
        if function_code is None:
            return {
                'passed': False,
                'message': 'Missing function code',
                'severity': 'high'
            }
        
        if not isinstance(function_code, int):
            return {
                'passed': False,
                'message': f'Invalid function code type: {type(function_code)}',
                'severity': 'high'
            }
        
        if function_code not in self.VALID_FUNCTION_CODES:
            return {
                'passed': False,
                'message': f'Invalid function code: 0x{function_code:02X}',
                'severity': 'high'
            }
        
        return {
            'passed': True,
            'message': f'Function code valid: {self.VALID_FUNCTION_CODES[function_code]}',
            'severity': 'low'
        }
    
    def _check_data_length(self, packet: Dict) -> Dict:
        """
        Check DNP3 data length validity
        
        Valid range: 0-65535 bytes
        """
        data_length = packet.get('data_length', 0)
        
        if not isinstance(data_length, int):
            return {
                'passed': False,
                'message': f'Invalid data length type: {type(data_length)}',
                'severity': 'medium'
            }
        
        if not (0 <= data_length <= 65535):
            return {
                'passed': False,
                'message': f'Data length out of range: {data_length}',
                'severity': 'medium'
            }
        
        return {
            'passed': True,
            'message': f'Data length valid: {data_length} bytes',
            'severity': 'low'
        }
    
    def _check_sequence_number(self, packet: Dict) -> Dict:
        """
        Check DNP3 sequence number validity
        
        Sequence number should be in valid range and follow expected pattern
        """
        sequence_number = packet.get('sequence_number')
        
        if sequence_number is None:
            return {
                'passed': False,
                'message': 'Missing sequence number',
                'severity': 'medium'
            }
        
        if not isinstance(sequence_number, int):
            return {
                'passed': False,
                'message': f'Invalid sequence number type: {type(sequence_number)}',
                'severity': 'medium'
            }
        
        if not (0 <= sequence_number <= 65535):
            return {
                'passed': False,
                'message': f'Sequence number out of range: {sequence_number}',
                'severity': 'medium'
            }
        
        # Check sequence number continuity if we have history
        if self.packet_history:
            last_packet = self.packet_history[-1]
            last_seq = last_packet.get('sequence_number', 0)
            
            # Allow reasonable gaps (0-10)
            diff = (sequence_number - last_seq) % 65536
            if diff > 10 and diff < 65526:  # Not a reasonable gap
                return {
                    'passed': False,
                    'message': f'Suspicious sequence number jump: {last_seq} -> {sequence_number}',
                    'severity': 'medium'
                }
        
        return {
            'passed': True,
            'message': f'Sequence number valid: {sequence_number}',
            'severity': 'low'
        }
    
    def _check_object_type(self, packet: Dict) -> Dict:
        """
        Check DNP3 object type validity
        
        Object type must be one of the valid DNP3 object types
        """
        object_type = packet.get('object_type')
        
        if object_type is None:
            return {
                'passed': False,
                'message': 'Missing object type',
                'severity': 'high'
            }
        
        if not isinstance(object_type, int):
            return {
                'passed': False,
                'message': f'Invalid object type type: {type(object_type)}',
                'severity': 'high'
            }
        
        if object_type not in self.VALID_OBJECT_TYPES:
            return {
                'passed': False,
                'message': f'Invalid object type: {object_type}',
                'severity': 'high'
            }
        
        return {
            'passed': True,
            'message': f'Object type valid: {object_type}',
            'severity': 'low'
        }
    
    def _add_to_history(self, packet_data: Dict, is_anomalous: bool) -> None:
        """Add packet to history for sequence analysis"""
        self.packet_history.append({
            'timestamp': datetime.now(),
            'is_anomalous': is_anomalous,
            **packet_data
        })
        
        # Maintain history size limit
        if len(self.packet_history) > self.max_history_size:
            self.packet_history.pop(0)
    
    def get_alarm_state(self) -> Dict:
        """Get current alarm state"""
        return {
            'last_anomaly': self.alarm_state['last_anomaly'],
            'anomaly_count': self.alarm_state['anomaly_count'],
            'is_alarmed': self.alarm_state['is_alarmed'],
            'history_size': len(self.packet_history),
        }
    
    def reset_alarm(self) -> None:
        """Reset alarm state"""
        self.alarm_state['is_alarmed'] = False
        self.logger.info("Alarm state reset")
    
    def get_statistics(self) -> Dict:
        """Get detection statistics"""
        if not self.packet_history:
            return {
                'total_packets': 0,
                'anomalous_packets': 0,
                'anomaly_rate': 0.0,
            }
        
        total = len(self.packet_history)
        anomalous = sum(1 for p in self.packet_history if p.get('is_anomalous', False))
        
        return {
            'total_packets': total,
            'anomalous_packets': anomalous,
            'anomaly_rate': (anomalous / total * 100) if total > 0 else 0.0,
        }
