"""
Storage Module Service

Handles data collection and reporting for storage/battery side module.
Collects storage data and reports it to VCC Master every 5 seconds.

Features:
- Periodic data collection (simulated battery sensor data)
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

from models.realtime_data_models import StorageData

logger = logging.getLogger(__name__)


class DataCollectionService:
    """Service for collecting storage/battery data from sensors."""

    def __init__(self, device_id: str = "vpp-storage"):
        """
        Initialize data collection service.
        
        Args:
            device_id: Identifier for this storage device
        """
        self.device_id = device_id
        self.soc = 75.0              # State of Charge (%)
        self.soh = 98.0              # State of Health (%)
        self.current_power = 50.0    # kW
        self.charge_status = "idle"  # charging/discharging/idle
        self.temperature = 25.0      # °C
        
        logger.info(f"Data Collection Service initialized for {device_id}")

    def collect_data(self) -> StorageData:
        """
        Collect storage data from sensors.
        
        Simulates sensor readings with small random variations.
        
        Returns:
            StorageData object with current sensor readings
        """
        # Simulate sensor data with small variations
        self.soc = max(0, min(100, self.soc + random.uniform(-2, 2)))
        self.soh = max(0, min(100, self.soh + random.uniform(-0.5, 0.5)))
        self.current_power = max(0, self.current_power + random.uniform(-5, 5))
        self.temperature = max(-50, min(80, self.temperature + random.uniform(-1, 1)))
        
        # Randomly change charge status occasionally
        if random.random() < 0.1:  # 10% chance
            self.charge_status = random.choice(["charging", "discharging", "idle"])
        
        data = StorageData(
            timestamp=datetime.now(),
            soc=round(self.soc, 2),
            soh=round(self.soh, 2),
            current_power=round(self.current_power, 2),
            charge_status=self.charge_status,
            temperature=round(self.temperature, 2)
        )
        
        logger.debug(f"Data collected: SOC={data.soc}%, SOH={data.soh}%, "
                    f"power={data.current_power}kW, temp={data.temperature}°C")
        
        return data

    def set_storage_level(self, soc: float, soh: float, current_power: float,
                         charge_status: str, temperature: float):
        """
        Set storage levels (for testing).
        
        Args:
            soc: State of Charge (%)
            soh: State of Health (%)
            current_power: Current power (kW)
            charge_status: Charge status (charging/discharging/idle)
            temperature: Temperature (°C)
        """
        self.soc = soc
        self.soh = soh
        self.current_power = current_power
        self.charge_status = charge_status
        self.temperature = temperature
        logger.info(f"Storage levels set: SOC={soc}%, SOH={soh}%, "
                   f"power={current_power}kW, temp={temperature}°C")


class DataReportingService:
    """Service for reporting storage data to VCC Master."""

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
    def _send_report(self, data: StorageData) -> bool:
        """
        Send storage data to VCC Master with retry logic.
        
        Args:
            data: Storage data to report
            
        Returns:
            True if report was successful, False otherwise
            
        Raises:
            requests.RequestException: If request fails after retries
        """
        try:
            url = f"{self.vcc_url}/api/vcc/report/storage"
            payload = {
                "timestamp": data.timestamp.isoformat(),
                "soc": data.soc,
                "soh": data.soh,
                "current_power": data.current_power,
                "charge_status": data.charge_status,
                "temperature": data.temperature
            }
            
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
            
            logger.info(f"Storage data reported successfully: "
                       f"SOC={data.soc}%, status={response.status_code}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to report storage data: {str(e)}")
            raise

    def report_data(self) -> bool:
        """
        Collect and report storage data.
        
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
        logger.info("Storage data reporting service started")

    def stop(self):
        """Stop the periodic reporting service."""
        self.is_running = False
        if self.report_thread:
            self.report_thread.join(timeout=5)
        logger.info("Storage data reporting service stopped")

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


class StorageModule:
    """Main storage module that coordinates data collection and reporting."""

    def __init__(self, vcc_url: str = "http://localhost:8080", 
                 report_interval: int = 5):
        """
        Initialize storage module.
        
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
        
        logger.info(f"Storage Module initialized: "
                   f"vcc_url={vcc_url}, report_interval={report_interval}s")

    def start(self):
        """Start the storage module."""
        self.reporting_service.start()
        logger.info("Storage Module started")

    def stop(self):
        """Stop the storage module."""
        self.reporting_service.stop()
        logger.info("Storage Module stopped")

    def collect_data(self) -> StorageData:
        """
        Collect storage data.
        
        Returns:
            StorageData object
        """
        return self.collection_service.collect_data()

    def report_data(self) -> bool:
        """
        Report storage data to VCC Master.
        
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
            "module": "storage",
            "vcc_url": self.vcc_url,
            "report_interval": self.report_interval,
            "reporting_stats": self.reporting_service.get_stats()
        }

    def set_storage_level(self, soc: float, soh: float, current_power: float,
                         charge_status: str, temperature: float):
        """
        Set storage levels (for testing).
        
        Args:
            soc: State of Charge (%)
            soh: State of Health (%)
            current_power: Current power (kW)
            charge_status: Charge status (charging/discharging/idle)
            temperature: Temperature (°C)
        """
        self.collection_service.set_storage_level(
            soc, soh, current_power, charge_status, temperature
        )
