"""
Power Generation Module Service

Handles data collection and reporting for power generation side module.
Collects power generation data and reports it to VCC Master every 5 seconds.

Features:
- Periodic data collection (simulated sensor data)
- Data reporting to VCC Master API
- Retry mechanism (up to 3 attempts)
- Error handling and logging
"""

import logging
import random
import threading
import time
from datetime import datetime
from typing import Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from models.realtime_data_models import PowerGenerationData

logger = logging.getLogger(__name__)


class DataCollectionService:
    """Service for collecting power generation data from sensors."""

    def __init__(self, device_id: str = "vpp-power-generation"):
        """
        Initialize data collection service.
        
        Args:
            device_id: Identifier for this power generation device
        """
        self.device_id = device_id
        self.current_power = 100.0  # kW
        self.solar_power = 50.0     # kW
        self.wind_power = 50.0      # kW
        self.efficiency = 95.0      # %
        self.device_status = "running"
        
        logger.info(f"Data Collection Service initialized for {device_id}")

    def collect_data(self) -> PowerGenerationData:
        """
        Collect power generation data from sensors.
        
        Simulates sensor readings with small random variations.
        
        Returns:
            PowerGenerationData object with current sensor readings
        """
        # Simulate sensor data with small variations
        self.current_power = max(0, self.current_power + random.uniform(-5, 5))
        self.solar_power = max(0, self.solar_power + random.uniform(-3, 3))
        self.wind_power = max(0, self.wind_power + random.uniform(-3, 3))
        self.efficiency = max(0, min(100, self.efficiency + random.uniform(-1, 1)))
        
        # Randomly change device status occasionally
        if random.random() < 0.05:  # 5% chance
            self.device_status = random.choice(["running", "idle", "error"])
        
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=round(self.current_power, 2),
            solar_power=round(self.solar_power, 2),
            wind_power=round(self.wind_power, 2),
            efficiency=round(self.efficiency, 2),
            device_status=self.device_status
        )
        
        logger.debug(f"Data collected: power={data.current_power}kW, "
                    f"solar={data.solar_power}kW, wind={data.wind_power}kW")
        
        return data

    def set_power_level(self, current_power: float, solar_power: float, 
                       wind_power: float, efficiency: float):
        """
        Set power generation levels (for testing).
        
        Args:
            current_power: Current power generation (kW)
            solar_power: Solar power (kW)
            wind_power: Wind power (kW)
            efficiency: Generation efficiency (%)
        """
        self.current_power = current_power
        self.solar_power = solar_power
        self.wind_power = wind_power
        self.efficiency = efficiency
        logger.info(f"Power levels set: {current_power}kW, "
                   f"solar={solar_power}kW, wind={wind_power}kW")


class DataReportingService:
    """Service for reporting power generation data to VCC Master."""

    def __init__(self, vcc_url: str = "http://localhost:8080", 
                 report_interval: int = 5, max_retries: int = 3):
        """
        Initialize data reporting service.
        
        Args:
            vcc_url: Base URL of VCC Master API
            report_interval: Interval between reports in seconds (default: 5)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.vcc_url = vcc_url
        self.report_interval = report_interval
        self.max_retries = max_retries
        self.is_running = False
        self.report_thread = None
        self.collection_service = DataCollectionService()
        self.last_report_time = None
        self.report_count = 0
        self.failed_report_count = 0
        
        logger.info(f"Data Reporting Service initialized: "
                   f"vcc_url={vcc_url}, interval={report_interval}s, "
                   f"max_retries={max_retries}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _send_report(self, data: PowerGenerationData) -> bool:
        """
        Send power generation data to VCC Master with retry logic.
        
        Args:
            data: Power generation data to report
            
        Returns:
            True if report was successful, False otherwise
            
        Raises:
            requests.RequestException: If request fails after retries
        """
        try:
            url = f"{self.vcc_url}/api/vcc/report/power"
            payload = {
                "timestamp": data.timestamp.isoformat(),
                "current_power": data.current_power,
                "solar_power": data.solar_power,
                "wind_power": data.wind_power,
                "efficiency": data.efficiency,
                "device_status": data.device_status
            }
            
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
            
            logger.info(f"Power data reported successfully: "
                       f"power={data.current_power}kW, status={response.status_code}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to report power data: {str(e)}")
            raise

    def report_data(self) -> bool:
        """
        Collect and report power generation data.
        
        Returns:
            True if report was successful, False otherwise
        """
        try:
            # Collect data
            data = self.collection_service.collect_data()
            
            # Send report with retry
            self._send_report(data)
            
            self.report_count += 1
            self.last_report_time = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"Error reporting data: {str(e)}")
            self.failed_report_count += 1
            return False

    def start(self):
        """Start the periodic reporting service."""
        if self.is_running:
            logger.warning("Reporting service is already running")
            return
        
        self.is_running = True
        self.report_thread = threading.Thread(target=self._report_loop, daemon=True)
        self.report_thread.start()
        logger.info("Power generation data reporting service started")

    def stop(self):
        """Stop the periodic reporting service."""
        self.is_running = False
        if self.report_thread:
            self.report_thread.join(timeout=5)
        logger.info("Power generation data reporting service stopped")

    def _report_loop(self):
        """Main reporting loop that runs in a separate thread."""
        while self.is_running:
            try:
                self.report_data()
                time.sleep(self.report_interval)
            except Exception as e:
                logger.error(f"Error in reporting loop: {str(e)}")
                time.sleep(self.report_interval)

    def get_stats(self) -> dict:
        """
        Get reporting statistics.
        
        Returns:
            Dictionary with reporting stats
        """
        return {
            "is_running": self.is_running,
            "report_count": self.report_count,
            "failed_report_count": self.failed_report_count,
            "last_report_time": self.last_report_time.isoformat() if self.last_report_time else None,
            "report_interval": self.report_interval,
            "vcc_url": self.vcc_url
        }


class PowerGenerationModule:
    """Main power generation module that coordinates data collection and reporting."""

    def __init__(self, vcc_url: str = "http://localhost:8080", 
                 report_interval: int = 5):
        """
        Initialize power generation module.
        
        Args:
            vcc_url: Base URL of VCC Master API
            report_interval: Interval between reports in seconds
        """
        self.vcc_url = vcc_url
        self.report_interval = report_interval
        self.collection_service = DataCollectionService()
        self.reporting_service = DataReportingService(
            vcc_url=vcc_url,
            report_interval=report_interval
        )
        
        logger.info(f"Power Generation Module initialized: "
                   f"vcc_url={vcc_url}, report_interval={report_interval}s")

    def start(self):
        """Start the power generation module."""
        self.reporting_service.start()
        logger.info("Power Generation Module started")

    def stop(self):
        """Stop the power generation module."""
        self.reporting_service.stop()
        logger.info("Power Generation Module stopped")

    def collect_data(self) -> PowerGenerationData:
        """
        Collect power generation data.
        
        Returns:
            PowerGenerationData object
        """
        return self.collection_service.collect_data()

    def report_data(self) -> bool:
        """
        Report power generation data to VCC Master.
        
        Returns:
            True if successful, False otherwise
        """
        return self.reporting_service.report_data()

    def get_stats(self) -> dict:
        """
        Get module statistics.
        
        Returns:
            Dictionary with module stats
        """
        return {
            "module": "power_generation",
            "vcc_url": self.vcc_url,
            "report_interval": self.report_interval,
            "reporting_stats": self.reporting_service.get_stats()
        }

    def set_power_level(self, current_power: float, solar_power: float,
                       wind_power: float, efficiency: float):
        """
        Set power generation levels (for testing).
        
        Args:
            current_power: Current power generation (kW)
            solar_power: Solar power (kW)
            wind_power: Wind power (kW)
            efficiency: Generation efficiency (%)
        """
        self.collection_service.set_power_level(
            current_power, solar_power, wind_power, efficiency
        )
