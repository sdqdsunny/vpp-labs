"""
VPP 实时数据存储服务

提供基于文件的数据存储，用于存储和检索 VPP 实时数据。
"""

import threading
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class VPPDataStore:
    """VPP 实时数据存储"""
    
    _instance = None
    _lock = threading.Lock()
    
    # 数据文件路径
    DATA_DIR = "/app/data"
    POWER_FILE = os.path.join(DATA_DIR, "vpp_power_data.json")
    STORAGE_FILE = os.path.join(DATA_DIR, "vpp_storage_data.json")
    DEMAND_FILE = os.path.join(DATA_DIR, "vpp_demand_data.json")
    COORDINATOR_FILE = os.path.join(DATA_DIR, "vpp_coordinator_data.json")
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._data_lock = threading.Lock()
        
        # 确保数据目录存在
        os.makedirs(self.DATA_DIR, exist_ok=True)
        
        # 初始化默认数据
        self._init_default_data()
    
    def _init_default_data(self):
        """初始化默认数据文件"""
        default_power = {
            "current_power": 0.0,
            "solar_power": 0.0,
            "wind_power": 0.0,
            "efficiency": 0.0,
            "device_status": "idle",
            "timestamp": datetime.now().isoformat()
        }
        
        default_storage = {
            "soc": 50.0,
            "soh": 100.0,
            "current_power": 0.0,
            "charge_status": "idle",
            "temperature": 25.0,
            "timestamp": datetime.now().isoformat()
        }
        
        default_demand = {
            "current_demand": 0.0,
            "flexible_demand": 0.0,
            "dr_status": "inactive",
            "timestamp": datetime.now().isoformat()
        }
        
        default_coordinator = {
            "status": "operational",
            "active_connections": 0,
            "last_coordination": datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
        # 如果文件不存在，创建它们
        if not os.path.exists(self.POWER_FILE):
            self._write_file(self.POWER_FILE, default_power)
        if not os.path.exists(self.STORAGE_FILE):
            self._write_file(self.STORAGE_FILE, default_storage)
        if not os.path.exists(self.DEMAND_FILE):
            self._write_file(self.DEMAND_FILE, default_demand)
        if not os.path.exists(self.COORDINATOR_FILE):
            self._write_file(self.COORDINATOR_FILE, default_coordinator)
    
    def _write_file(self, filepath: str, data: Dict[str, Any]) -> None:
        """写入数据到文件"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error writing to {filepath}: {e}")
    
    def _read_file(self, filepath: str) -> Dict[str, Any]:
        """从文件读取数据"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error reading from {filepath}: {e}")
        return {}
    
    def update_power_data(self, data: Dict[str, Any]) -> None:
        """更新电源数据"""
        with self._data_lock:
            current = self._read_file(self.POWER_FILE)
            current.update(data)
            current["timestamp"] = datetime.now().isoformat()
            self._write_file(self.POWER_FILE, current)
    
    def update_storage_data(self, data: Dict[str, Any]) -> None:
        """更新储能数据"""
        with self._data_lock:
            current = self._read_file(self.STORAGE_FILE)
            current.update(data)
            current["timestamp"] = datetime.now().isoformat()
            self._write_file(self.STORAGE_FILE, current)
    
    def update_demand_data(self, data: Dict[str, Any]) -> None:
        """更新需求数据"""
        with self._data_lock:
            current = self._read_file(self.DEMAND_FILE)
            current.update(data)
            current["timestamp"] = datetime.now().isoformat()
            self._write_file(self.DEMAND_FILE, current)
    
    def update_coordinator_data(self, data: Dict[str, Any]) -> None:
        """更新协调器数据"""
        with self._data_lock:
            current = self._read_file(self.COORDINATOR_FILE)
            current.update(data)
            current["timestamp"] = datetime.now().isoformat()
            self._write_file(self.COORDINATOR_FILE, current)
    
    def get_power_data(self) -> Dict[str, Any]:
        """获取电源数据"""
        with self._data_lock:
            return self._read_file(self.POWER_FILE)
    
    def get_storage_data(self) -> Dict[str, Any]:
        """获取储能数据"""
        with self._data_lock:
            return self._read_file(self.STORAGE_FILE)
    
    def get_demand_data(self) -> Dict[str, Any]:
        """获取需求数据"""
        with self._data_lock:
            return self._read_file(self.DEMAND_FILE)
    
    def get_coordinator_data(self) -> Dict[str, Any]:
        """获取协调器数据"""
        with self._data_lock:
            return self._read_file(self.COORDINATOR_FILE)
    
    def get_all_data(self) -> Dict[str, Any]:
        """获取所有数据"""
        with self._data_lock:
            return {
                "power_generation": self._read_file(self.POWER_FILE),
                "storage": self._read_file(self.STORAGE_FILE),
                "demand": self._read_file(self.DEMAND_FILE),
                "coordinator": self._read_file(self.COORDINATOR_FILE),
                "timestamp": datetime.now().isoformat()
            }


def get_vpp_data_store() -> VPPDataStore:
    """获取 VPP 数据存储单例"""
    return VPPDataStore()
