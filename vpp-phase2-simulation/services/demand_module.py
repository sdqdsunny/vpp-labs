"""
Demand side module for VPP real-time data exchange.

Implements:
- DataCollectionService: Simulates demand data collection
- DataReportingService: Handles periodic data reporting to VCC
- DemandModule: Main module coordinating collection and reporting
"""

import random
import threading
import time
import requests
from datetime import datetime
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from models.realtime_data_models import DemandData


class DataCollectionService:
    """Simulates demand side data collection."""

    def __init__(self, device_id: str = "vpp-demand"):
        """Initialize data collection service.
        
        Args:
            device_id: Device identifier
        """
        self.device_id = device_id
        self.current_load = 100.0  # kW
        self.forecast_load = 110.0  # kW
        self.adjustable_range = (80.0, 120.0)  # (min, max) kW
        self.dr_status = "inactive"

    def collect_data(self) -> DemandData:
        """Collect demand side data.
        
        Returns:
            DemandData: Collected demand data with realistic variations
        """
        # Add small random variations to simulate real data
        current_load = self.current_load + random.uniform(-5, 5)
        forecast_load = self.forecast_load + random.uniform(-10, 10)
        
        # Ensure values stay within reasonable bounds
        current_load = max(0, min(current_load, 200))
        forecast_load = max(0, min(forecast_load, 200))
        
        return DemandData(
            timestamp=datetime.now(),
            current_load=current_load,
            forecast_load=forecast_load,
            adjustable_range=self.adjustable_range,
            dr_status=self.dr_status
        )

    def set_demand_level(self, current_load: float, forecast_load: float,
                        adjustable_min: float, adjustable_max: float,
                        dr_status: str):
        """Set demand levels for testing.
        
        Args:
            current_load: Current load (kW)
            forecast_load: Forecasted load (kW)
            adjustable_min: Minimum adjustable load (kW)
            adjustable_max: Maximum adjustable load (kW)
            dr_status: Demand response status (active/inactive)
        """
        self.current_load = current_load
        self.forecast_load = forecast_load
        self.adjustable_range = (adjustable_min, adjustable_max)
        self.dr_status = dr_status


class DataReportingService:
    """Handles periodic data reporting to VCC Master."""

    def __init__(self, vcc_url: str = "http://localhost:8080",
                 report_interval: int = 5, max_retries: int = 3):
        """Initialize data reporting service.
        
        Args:
            vcc_url: VCC Master URL
            report_interval: Reporting interval in seconds
            max_retries: Maximum retry attempts
        """
        self.vcc_url = vcc_url
        self.report_interval = report_interval
        self.max_retries = max_retries
        self.is_running = False
        self.report_thread: Optional[threading.Thread] = None
        self.report_count = 0
        self.failed_report_count = 0
        self.last_report_time: Optional[datetime] = None
        self.collection_service = DataCollectionService()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _send_report(self, data: DemandData) -> bool:
        """Send data report to VCC with retry logic.
        
        Args:
            data: Demand data to report
            
        Returns:
            bool: True if successful, raises RetryError if all retries fail
        """
        url = f"{self.vcc_url}/api/vcc/report/demand"
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=data.to_dict(), headers=headers, timeout=5)
        response.raise_for_status()
        
        return response.status_code == 200

    def report_data(self) -> bool:
        """Report demand data to VCC.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = self.collection_service.collect_data()
            self._send_report(data)
            self.report_count += 1
            self.last_report_time = datetime.now()
            return True
        except Exception:
            self.failed_report_count += 1
            return False

    def start(self):
        """Start periodic data reporting."""
        if self.is_running:
            return
        
        self.is_running = True
        self.report_thread = threading.Thread(target=self._report_loop, daemon=True)
        self.report_thread.start()

    def stop(self):
        """Stop periodic data reporting."""
        self.is_running = False
        if self.report_thread:
            self.report_thread.join(timeout=5)

    def _report_loop(self):
        """Background reporting loop."""
        while self.is_running:
            self.report_data()
            time.sleep(self.report_interval)

    def get_stats(self) -> dict:
        """Get reporting statistics.
        
        Returns:
            dict: Statistics including report count, failures, etc.
        """
        return {
            "is_running": self.is_running,
            "report_count": self.report_count,
            "failed_report_count": self.failed_report_count,
            "last_report_time": self.last_report_time.isoformat() if self.last_report_time else None,
            "report_interval": self.report_interval,
            "vcc_url": self.vcc_url,
        }


class DemandModule:
    """Main demand side module."""

    def __init__(self, vcc_url: str = "http://localhost:8080",
                 report_interval: int = 5):
        """Initialize demand module.
        
        Args:
            vcc_url: VCC Master URL
            report_interval: Reporting interval in seconds
        """
        self.vcc_url = vcc_url
        self.report_interval = report_interval
        self.collection_service = DataCollectionService()
        self.reporting_service = DataReportingService(
            vcc_url=vcc_url,
            report_interval=report_interval
        )

    def start(self):
        """Start the demand module."""
        self.reporting_service.start()

    def stop(self):
        """Stop the demand module."""
        self.reporting_service.stop()

    def collect_data(self) -> DemandData:
        """Collect demand data.
        
        Returns:
            DemandData: Collected demand data
        """
        return self.collection_service.collect_data()

    def report_data(self) -> bool:
        """Report demand data to VCC.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.reporting_service.report_data()

    def get_stats(self) -> dict:
        """Get module statistics.
        
        Returns:
            dict: Module statistics
        """
        return {
            "module": "demand",
            "vcc_url": self.vcc_url,
            "report_interval": self.report_interval,
            "reporting_stats": self.reporting_service.get_stats(),
        }

    def set_demand_level(self, current_load: float, forecast_load: float,
                        adjustable_min: float, adjustable_max: float,
                        dr_status: str):
        """Set demand levels for testing.
        
        Args:
            current_load: Current load (kW)
            forecast_load: Forecasted load (kW)
            adjustable_min: Minimum adjustable load (kW)
            adjustable_max: Maximum adjustable load (kW)
            dr_status: Demand response status (active/inactive)
        """
        self.collection_service.set_demand_level(
            current_load, forecast_load, adjustable_min, adjustable_max, dr_status
        )
