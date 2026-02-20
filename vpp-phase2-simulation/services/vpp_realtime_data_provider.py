"""
VPP Real-time Data Provider Service

Provides real-time data from VPP microservices for visualization and monitoring.
Fetches data from Power Generation, Storage, Demand, and Coordinator services.
"""

import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from threading import Lock

from services.vpp_data_store import get_vpp_data_store

logger = logging.getLogger(__name__)


class VPPRealtimeDataProvider:
    """Provides real-time data from VPP microservices."""

    def __init__(self, 
                 power_url: str = "http://localhost:5001",
                 storage_url: str = "http://localhost:5002",
                 demand_url: str = "http://localhost:5003",
                 coordinator_url: str = "http://localhost:8000"):
        """Initialize VPP data provider.
        
        Args:
            power_url: Power generation service URL
            storage_url: Storage service URL
            demand_url: Demand service URL
            coordinator_url: Coordinator service URL
        """
        self.power_url = power_url
        self.storage_url = storage_url
        self.demand_url = demand_url
        self.coordinator_url = coordinator_url
        
        self.last_power_data: Optional[Dict[str, Any]] = None
        self.last_storage_data: Optional[Dict[str, Any]] = None
        self.last_demand_data: Optional[Dict[str, Any]] = None
        self.last_coordination_data: Optional[Dict[str, Any]] = None
        
        self.data_lock = Lock()
        self.fetch_errors = {
            'power': 0,
            'storage': 0,
            'demand': 0,
            'coordinator': 0
        }

    def fetch_all_data(self) -> Dict[str, Any]:
        """Fetch all real-time data from VPP services.
        
        Returns:
            Dictionary containing all VPP data
        """
        with self.data_lock:
            timestamp = datetime.now().isoformat()
            
            # Fetch data from each service
            power_data = self._fetch_power_data()
            storage_data = self._fetch_storage_data()
            demand_data = self._fetch_demand_data()
            coordinator_data = self._fetch_coordinator_data()
            
            # Calculate energy balance
            energy_balance = self._calculate_energy_balance(
                power_data, storage_data, demand_data
            )
            
            return {
                'timestamp': timestamp,
                'power_generation': power_data,
                'storage': storage_data,
                'demand': demand_data,
                'coordinator': coordinator_data,
                'energy_balance': energy_balance,
                'system_status': self._get_system_status(
                    power_data, storage_data, demand_data
                ),
                'fetch_errors': self.fetch_errors
            }

    def _fetch_power_data(self) -> Dict[str, Any]:
        """Fetch power generation data."""
        try:
            # 首先尝试从数据存储获取
            store = get_vpp_data_store()
            data = store.get_power_data()
            
            # 如果数据不是默认值，返回存储的数据
            if data.get('current_power', 0) != 0 or data.get('solar_power', 0) != 0:
                self.fetch_errors['power'] = 0
                return data
            
            # 否则尝试从微服务获取
            response = requests.get(
                f"{self.power_url}/api/power/status",
                timeout=2
            )
            if response.status_code == 200:
                self.fetch_errors['power'] = 0
                return response.json()
            else:
                self.fetch_errors['power'] += 1
                return data
        except Exception as e:
            logger.warning(f"Error fetching power data: {e}")
            self.fetch_errors['power'] += 1
            store = get_vpp_data_store()
            return store.get_power_data()

    def _fetch_storage_data(self) -> Dict[str, Any]:
        """Fetch storage data."""
        try:
            # 首先尝试从数据存储获取
            store = get_vpp_data_store()
            data = store.get_storage_data()
            
            # 如果数据不是默认值，返回存储的数据
            if data.get('soc', 50) != 50 or data.get('current_power', 0) != 0:
                self.fetch_errors['storage'] = 0
                return data
            
            # 否则尝试从微服务获取
            response = requests.get(
                f"{self.storage_url}/api/storage/status",
                timeout=2
            )
            if response.status_code == 200:
                self.fetch_errors['storage'] = 0
                return response.json()
            else:
                self.fetch_errors['storage'] += 1
                return data
        except Exception as e:
            logger.warning(f"Error fetching storage data: {e}")
            self.fetch_errors['storage'] += 1
            store = get_vpp_data_store()
            return store.get_storage_data()

    def _fetch_demand_data(self) -> Dict[str, Any]:
        """Fetch demand data."""
        try:
            # 首先尝试从数据存储获取
            store = get_vpp_data_store()
            data = store.get_demand_data()
            
            # 如果数据不是默认值，返回存储的数据
            if data.get('current_demand', 0) != 0 or data.get('flexible_demand', 0) != 0:
                self.fetch_errors['demand'] = 0
                return data
            
            # 否则尝试从微服务获取
            response = requests.get(
                f"{self.demand_url}/api/demand/status",
                timeout=2
            )
            if response.status_code == 200:
                self.fetch_errors['demand'] = 0
                return response.json()
            else:
                self.fetch_errors['demand'] += 1
                return data
        except Exception as e:
            logger.warning(f"Error fetching demand data: {e}")
            self.fetch_errors['demand'] += 1
            store = get_vpp_data_store()
            return store.get_demand_data()

    def _fetch_coordinator_data(self) -> Dict[str, Any]:
        """Fetch coordinator data."""
        try:
            # 首先尝试从数据存储获取
            store = get_vpp_data_store()
            data = store.get_coordinator_data()
            
            # 尝试从微服务获取
            response = requests.get(
                f"{self.coordinator_url}/api/coordinator/status",
                timeout=2
            )
            if response.status_code == 200:
                self.fetch_errors['coordinator'] = 0
                return response.json()
            else:
                self.fetch_errors['coordinator'] += 1
                return data
        except Exception as e:
            logger.warning(f"Error fetching coordinator data: {e}")
            self.fetch_errors['coordinator'] += 1
            store = get_vpp_data_store()
            return store.get_coordinator_data()

    def _calculate_energy_balance(self, power_data: Dict, storage_data: Dict, 
                                  demand_data: Dict) -> Dict[str, Any]:
        """Calculate energy balance across the system.
        
        Returns:
            Energy balance information
        """
        try:
            power_output = power_data.get('current_power', 0)
            storage_power = storage_data.get('current_power', 0)
            demand_power = demand_data.get('current_demand', 0)
            
            # Calculate balance
            total_supply = power_output + storage_power
            balance = total_supply - demand_power
            
            return {
                'power_generation': power_output,
                'storage_discharge': max(0, storage_power),
                'storage_charge': max(0, -storage_power),
                'demand': demand_power,
                'total_supply': total_supply,
                'balance': balance,
                'status': 'balanced' if abs(balance) < 1 else ('surplus' if balance > 0 else 'deficit')
            }
        except Exception as e:
            logger.warning(f"Error calculating energy balance: {e}")
            return self._get_default_energy_balance()

    def _get_system_status(self, power_data: Dict, storage_data: Dict, 
                          demand_data: Dict) -> Dict[str, Any]:
        """Get overall system status.
        
        Returns:
            System status information
        """
        try:
            power_status = power_data.get('device_status', 'unknown')
            storage_status = storage_data.get('charge_status', 'unknown')
            demand_status = demand_data.get('dr_status', 'unknown')
            
            # Determine overall status
            if power_status == 'error' or storage_status == 'error' or demand_status == 'error':
                overall_status = 'error'
            elif power_status == 'running' and storage_status != 'error' and demand_status != 'error':
                overall_status = 'running'
            else:
                overall_status = 'idle'
            
            return {
                'power_status': power_status,
                'storage_status': storage_status,
                'demand_status': demand_status,
                'overall_status': overall_status,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Error getting system status: {e}")
            return self._get_default_system_status()

    @staticmethod
    def _get_default_power_data() -> Dict[str, Any]:
        """Get default power data."""
        return {
            'current_power': 0,
            'solar_power': 0,
            'wind_power': 0,
            'efficiency': 0,
            'device_status': 'idle',
            'module_id': 'vpp-power-generation'
        }

    @staticmethod
    def _get_default_storage_data() -> Dict[str, Any]:
        """Get default storage data."""
        return {
            'soc': 50,
            'soh': 100,
            'current_power': 0,
            'charge_status': 'idle',
            'temperature': 25,
            'module_id': 'vpp-storage'
        }

    @staticmethod
    def _get_default_demand_data() -> Dict[str, Any]:
        """Get default demand data."""
        return {
            'current_demand': 0,
            'flexible_demand': 0,
            'dr_status': 'inactive',
            'module_id': 'vpp-demand'
        }

    @staticmethod
    def _get_default_coordinator_data() -> Dict[str, Any]:
        """Get default coordinator data."""
        return {
            'coordination_count': 0,
            'last_coordination_time': None,
            'optimization_score': 0,
            'status': 'idle'
        }

    @staticmethod
    def _get_default_energy_balance() -> Dict[str, Any]:
        """Get default energy balance."""
        return {
            'power_generation': 0,
            'storage_discharge': 0,
            'storage_charge': 0,
            'demand': 0,
            'total_supply': 0,
            'balance': 0,
            'status': 'unknown'
        }

    @staticmethod
    def _get_default_system_status() -> Dict[str, Any]:
        """Get default system status."""
        return {
            'power_status': 'unknown',
            'storage_status': 'unknown',
            'demand_status': 'unknown',
            'overall_status': 'unknown',
            'timestamp': datetime.now().isoformat()
        }


# Global instance
_provider_instance: Optional[VPPRealtimeDataProvider] = None


def get_vpp_data_provider() -> VPPRealtimeDataProvider:
    """Get or create VPP data provider instance."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = VPPRealtimeDataProvider()
    return _provider_instance

