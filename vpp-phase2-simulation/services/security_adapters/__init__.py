"""
Security Testing Tool Adapters

This module provides adapters for various security testing tools including:
- OpenDNP3 (DNP3 protocol testing)
- python-opcua (OPC UA protocol testing)
- Boofuzz (Protocol fuzzing)
- PyModbus (Modbus protocol testing)
- SocketCAN (CAN protocol testing)
"""

from .base_adapter import TestAdapter, TestRequest, TestResult
from .dnp3_adapter import DNP3Adapter
from .opcua_adapter import OPCUAAdapter
from .boofuzz_adapter import BoofuzzAdapter
from .modbus_adapter import ModbusAdapter
from .can_adapter import CANAdapter

__all__ = [
    'TestAdapter',
    'TestRequest',
    'TestResult',
    'DNP3Adapter',
    'OPCUAAdapter',
    'BoofuzzAdapter',
    'ModbusAdapter',
    'CANAdapter',
]
