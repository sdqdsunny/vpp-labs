"""
Device Manager Service

Handles device registration, discovery, status monitoring, and configuration management.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError
from utils.database import SessionLocal
from utils.logger import setup_logger
from utils.errors import (
    ValidationError, DeviceNotFoundError, DuplicateDeviceError,
    DatabaseError
)
from utils.metrics import (
    device_count, device_online_count, device_registration_total,
    record_device_registration, time_database_query
)
from models.device import Device
from utils.validators import DeviceRegistration, DeviceConfig

logger = setup_logger(__name__)


class DeviceManager:
    """Manages device registration, discovery, and status monitoring"""
    
    # Default heartbeat timeout in seconds
    HEARTBEAT_TIMEOUT = 30
    
    def __init__(self):
        """Initialize device manager"""
        self.session = SessionLocal()
    
    def __del__(self):
        """Cleanup session"""
        if self.session:
            self.session.close()
    
    @time_database_query("device_registration")
    def register_device(self, device_data: DeviceRegistration) -> Device:
        """
        Register a new device
        
        Args:
            device_data: Device registration data
        
        Returns:
            Created Device instance
        
        Raises:
            ValidationError: If device data is invalid
            DuplicateDeviceError: If device ID already exists
            DatabaseError: If database operation fails
        """
        try:
            # Check if device already exists
            existing = self.session.query(Device).filter_by(
                id=device_data.device_id
            ).first()
            
            if existing:
                logger.warning(
                    f"Duplicate device registration attempt: {device_data.device_id}"
                )
                raise DuplicateDeviceError(
                    f"Device with ID '{device_data.device_id}' already exists",
                    details={"device_id": device_data.device_id}
                )
            
            # Create new device
            device = Device(
                id=device_data.device_id,
                device_type=device_data.device_type,
                location=device_data.location,
                capabilities=device_data.capabilities,
                configuration={},
                status="offline"
            )
            
            self.session.add(device)
            self.session.commit()
            
            logger.info(
                f"Device registered: {device_data.device_id}",
                extra={
                    "device_id": device_data.device_id,
                    "device_type": device_data.device_type,
                    "location": device_data.location
                }
            )
            
            # Record metrics
            record_device_registration(device_data.device_type)
            self._update_device_metrics()
            
            return device
        
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Database integrity error: {str(e)}")
            raise DatabaseError("Failed to register device")
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to register device: {str(e)}")
            raise
    
    @time_database_query("device_discovery")
    def discover_devices(
        self,
        page: int = 1,
        page_size: int = 50,
        status_filter: Optional[str] = None
    ) -> tuple:
        """
        Discover and list all devices with pagination
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            status_filter: Filter by status (online, offline, error)
        
        Returns:
            Tuple of (devices list, total count)
        
        Raises:
            ValidationError: If pagination parameters are invalid
            DatabaseError: If database operation fails
        """
        try:
            # Validate pagination parameters
            if page < 1:
                raise ValidationError("Page must be >= 1")
            if page_size < 1 or page_size > 100:
                raise ValidationError("Page size must be between 1 and 100")
            
            # Build query
            query = self.session.query(Device)
            
            # Apply status filter if provided
            if status_filter:
                if status_filter not in ["online", "offline", "error"]:
                    raise ValidationError(f"Invalid status: {status_filter}")
                query = query.filter_by(status=status_filter)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            devices = query.offset(offset).limit(page_size).all()
            
            logger.debug(
                f"Discovered {len(devices)} devices",
                extra={
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count
                }
            )
            
            return devices, total_count
        
        except Exception as e:
            logger.error(f"Failed to discover devices: {str(e)}")
            raise
    
    @time_database_query("device_get")
    def get_device(self, device_id: str) -> Device:
        """
        Get device by ID
        
        Args:
            device_id: Device ID
        
        Returns:
            Device instance
        
        Raises:
            DeviceNotFoundError: If device not found
            DatabaseError: If database operation fails
        """
        try:
            device = self.session.query(Device).filter_by(id=device_id).first()
            
            if not device:
                logger.warning(f"Device not found: {device_id}")
                raise DeviceNotFoundError(
                    f"Device with ID '{device_id}' not found",
                    details={"device_id": device_id}
                )
            
            return device
        
        except Exception as e:
            logger.error(f"Failed to get device: {str(e)}")
            raise
    
    @time_database_query("device_status_get")
    def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """
        Get device status
        
        Args:
            device_id: Device ID
        
        Returns:
            Dictionary with status information
        
        Raises:
            DeviceNotFoundError: If device not found
        """
        device = self.get_device(device_id)
        
        return {
            "device_id": device.id,
            "status": device.status,
            "last_heartbeat": device.last_heartbeat.isoformat() if device.last_heartbeat else None,
            "is_online": device.is_online(),
            "is_offline": device.is_offline(),
            "is_error": device.is_error()
        }
    
    @time_database_query("device_config_update")
    def update_device_config(
        self,
        device_id: str,
        config: DeviceConfig
    ) -> Device:
        """
        Update device configuration
        
        Args:
            device_id: Device ID
            config: Device configuration
        
        Returns:
            Updated Device instance
        
        Raises:
            DeviceNotFoundError: If device not found
            ValidationError: If configuration is invalid
            DatabaseError: If database operation fails
        """
        try:
            device = self.get_device(device_id)
            
            # Update configuration
            config_dict = config.dict(exclude_none=True)
            device.update_configuration(config_dict)
            
            self.session.commit()
            
            logger.info(
                f"Device configuration updated: {device_id}",
                extra={
                    "device_id": device_id,
                    "config": config_dict
                }
            )
            
            return device
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update device config: {str(e)}")
            raise
    
    @time_database_query("device_status_update")
    def update_device_status(self, device_id: str, status: str) -> Device:
        """
        Update device status
        
        Args:
            device_id: Device ID
            status: New status (online, offline, error)
        
        Returns:
            Updated Device instance
        
        Raises:
            DeviceNotFoundError: If device not found
            ValidationError: If status is invalid
            DatabaseError: If database operation fails
        """
        try:
            if status not in ["online", "offline", "error"]:
                raise ValidationError(f"Invalid status: {status}")
            
            device = self.get_device(device_id)
            device.update_status(status)
            
            self.session.commit()
            
            logger.info(
                f"Device status updated: {device_id} -> {status}",
                extra={
                    "device_id": device_id,
                    "status": status
                }
            )
            
            self._update_device_metrics()
            
            return device
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update device status: {str(e)}")
            raise
    
    @time_database_query("device_heartbeat_update")
    def update_device_heartbeat(self, device_id: str) -> Device:
        """
        Update device heartbeat (mark as online)
        
        Args:
            device_id: Device ID
        
        Returns:
            Updated Device instance
        
        Raises:
            DeviceNotFoundError: If device not found
            DatabaseError: If database operation fails
        """
        try:
            device = self.get_device(device_id)
            device.update_heartbeat()
            
            self.session.commit()
            
            logger.debug(
                f"Device heartbeat updated: {device_id}",
                extra={"device_id": device_id}
            )
            
            self._update_device_metrics()
            
            return device
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update device heartbeat: {str(e)}")
            raise
    
    @time_database_query("device_offline_check")
    def check_offline_devices(self) -> List[Device]:
        """
        Check for devices that should be marked offline based on heartbeat timeout
        
        Returns:
            List of devices marked as offline
        """
        try:
            timeout_threshold = datetime.utcnow() - timedelta(
                seconds=self.HEARTBEAT_TIMEOUT
            )
            
            # Find online devices with no recent heartbeat
            offline_devices = self.session.query(Device).filter(
                Device.status == "online",
                (Device.last_heartbeat < timeout_threshold) | (Device.last_heartbeat == None)
            ).all()
            
            # Mark them as offline
            for device in offline_devices:
                device.update_status("offline")
                logger.warning(
                    f"Device marked offline due to heartbeat timeout: {device.id}",
                    extra={"device_id": device.id}
                )
            
            if offline_devices:
                self.session.commit()
                self._update_device_metrics()
            
            return offline_devices
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to check offline devices: {str(e)}")
            raise
    
    @time_database_query("device_delete")
    def delete_device(self, device_id: str) -> bool:
        """
        Delete a device
        
        Args:
            device_id: Device ID
        
        Returns:
            True if device was deleted
        
        Raises:
            DeviceNotFoundError: If device not found
            DatabaseError: If database operation fails
        """
        try:
            device = self.get_device(device_id)
            
            self.session.delete(device)
            self.session.commit()
            
            logger.info(
                f"Device deleted: {device_id}",
                extra={"device_id": device_id}
            )
            
            self._update_device_metrics()
            
            return True
        
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete device: {str(e)}")
            raise
    
    def _update_device_metrics(self):
        """Update device metrics"""
        try:
            total_devices = self.session.query(Device).count()
            online_devices = self.session.query(Device).filter_by(
                status="online"
            ).count()
            
            device_count.set(total_devices)
            device_online_count.set(online_devices)
            
            logger.debug(
                f"Device metrics updated: total={total_devices}, online={online_devices}"
            )
        
        except Exception as e:
            logger.error(f"Failed to update device metrics: {str(e)}")
