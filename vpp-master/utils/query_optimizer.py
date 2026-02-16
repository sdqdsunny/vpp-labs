"""
Query Optimization Utilities

Provides optimized query methods for common database operations
with built-in caching and performance monitoring.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from utils.logger import setup_logger
from utils.query_cache import cached_query, invalidate_cache_for
from utils.metrics import time_database_query
import time

logger = setup_logger(__name__)


class QueryOptimizer:
    """
    Provides optimized query methods with caching and performance monitoring.
    """
    
    @staticmethod
    @time_database_query('get_all_devices')
    @cached_query(ttl_seconds=300)
    def get_all_devices(session: Session) -> List[Any]:
        """
        Get all devices with caching.
        
        Args:
            session: Database session
            
        Returns:
            List of all devices
        """
        from models.device import Device
        return session.query(Device).all()
    
    @staticmethod
    @time_database_query('get_devices_by_type')
    @cached_query(ttl_seconds=300)
    def get_devices_by_type(session: Session, device_type: str) -> List[Any]:
        """
        Get devices filtered by type with caching.
        
        Args:
            session: Database session
            device_type: Type of device to filter by
            
        Returns:
            List of devices matching the type
        """
        from models.device import Device
        return session.query(Device).filter(Device.device_type == device_type).all()
    
    @staticmethod
    @time_database_query('get_devices_by_status')
    @cached_query(ttl_seconds=300)
    def get_devices_by_status(session: Session, status: str) -> List[Any]:
        """
        Get devices filtered by status with caching.
        
        Args:
            session: Database session
            status: Status to filter by (online, offline, error)
            
        Returns:
            List of devices with the specified status
        """
        from models.device import Device
        return session.query(Device).filter(Device.status == status).all()
    
    @staticmethod
    @time_database_query('get_devices_by_location')
    @cached_query(ttl_seconds=300)
    def get_devices_by_location(session: Session, location: str) -> List[Any]:
        """
        Get devices filtered by location with caching.
        
        Args:
            session: Database session
            location: Location to filter by
            
        Returns:
            List of devices at the specified location
        """
        from models.device import Device
        return session.query(Device).filter(Device.location == location).all()
    
    @staticmethod
    @time_database_query('get_online_devices_count')
    @cached_query(ttl_seconds=60)
    def get_online_devices_count(session: Session) -> int:
        """
        Get count of online devices with caching.
        
        Args:
            session: Database session
            
        Returns:
            Number of online devices
        """
        from models.device import Device
        return session.query(Device).filter(Device.status == "online").count()
    
    @staticmethod
    @time_database_query('get_dispatches_by_device')
    @cached_query(ttl_seconds=300)
    def get_dispatches_by_device(session: Session, device_id: str) -> List[Any]:
        """
        Get dispatches for a specific device with caching.
        
        Args:
            session: Database session
            device_id: Device ID to filter by
            
        Returns:
            List of dispatches for the device
        """
        from models.dispatch import Dispatch
        return session.query(Dispatch).filter(Dispatch.device_id == device_id).all()
    
    @staticmethod
    @time_database_query('get_pending_dispatches')
    @cached_query(ttl_seconds=60)
    def get_pending_dispatches(session: Session) -> List[Any]:
        """
        Get all pending dispatches with caching.
        
        Args:
            session: Database session
            
        Returns:
            List of pending dispatches
        """
        from models.dispatch import Dispatch
        return session.query(Dispatch).filter(Dispatch.status == "pending").all()
    
    @staticmethod
    @time_database_query('get_scheduled_dispatches')
    @cached_query(ttl_seconds=60)
    def get_scheduled_dispatches(session: Session) -> List[Any]:
        """
        Get all scheduled dispatches that haven't executed yet with caching.
        
        Args:
            session: Database session
            
        Returns:
            List of scheduled dispatches
        """
        from models.dispatch import Dispatch
        now = datetime.utcnow()
        return session.query(Dispatch).filter(
            and_(
                Dispatch.scheduled_time.isnot(None),
                Dispatch.scheduled_time > now,
                Dispatch.status == "pending"
            )
        ).all()
    
    @staticmethod
    @time_database_query('get_dispatch_history')
    @cached_query(ttl_seconds=300)
    def get_dispatch_history(
        session: Session,
        device_id: Optional[str] = None,
        status: Optional[str] = None,
        days: int = 7
    ) -> List[Any]:
        """
        Get dispatch history with optional filters and caching.
        
        Args:
            session: Database session
            device_id: Optional device ID filter
            status: Optional status filter
            days: Number of days to look back
            
        Returns:
            List of dispatch records matching filters
        """
        from models.dispatch import Dispatch
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = session.query(Dispatch).filter(Dispatch.created_at >= cutoff_date)
        
        if device_id:
            query = query.filter(Dispatch.device_id == device_id)
        
        if status:
            query = query.filter(Dispatch.status == status)
        
        return query.order_by(Dispatch.created_at.desc()).all()
    
    @staticmethod
    @time_database_query('get_protocol_mappings')
    @cached_query(ttl_seconds=300)
    def get_protocol_mappings(
        session: Session,
        source_protocol: Optional[str] = None,
        target_protocol: Optional[str] = None
    ) -> List[Any]:
        """
        Get protocol mappings with optional filters and caching.
        
        Args:
            session: Database session
            source_protocol: Optional source protocol filter
            target_protocol: Optional target protocol filter
            
        Returns:
            List of protocol mappings matching filters
        """
        from models.protocol_mapping import ProtocolMapping
        
        query = session.query(ProtocolMapping).filter(ProtocolMapping.is_active == True)
        
        if source_protocol:
            query = query.filter(ProtocolMapping.source_protocol == source_protocol)
        
        if target_protocol:
            query = query.filter(ProtocolMapping.target_protocol == target_protocol)
        
        return query.all()
    
    @staticmethod
    @time_database_query('get_analysis_results')
    @cached_query(ttl_seconds=300)
    def get_analysis_results(
        session: Session,
        analysis_type: Optional[str] = None,
        days: int = 7
    ) -> List[Any]:
        """
        Get analysis results with optional filters and caching.
        
        Args:
            session: Database session
            analysis_type: Optional analysis type filter
            days: Number of days to look back
            
        Returns:
            List of analysis results matching filters
        """
        from models.analysis_result import AnalysisResult
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = session.query(AnalysisResult).filter(AnalysisResult.created_at >= cutoff_date)
        
        if analysis_type:
            query = query.filter(AnalysisResult.analysis_type == analysis_type)
        
        return query.order_by(AnalysisResult.created_at.desc()).all()
    
    @staticmethod
    def invalidate_device_cache(device_id: Optional[str] = None) -> None:
        """
        Invalidate device-related cache entries.
        
        Args:
            device_id: Optional specific device ID to invalidate
        """
        # Invalidate all device queries
        invalidate_cache_for('get_all_devices')
        invalidate_cache_for('get_online_devices_count')
        
        if device_id:
            invalidate_cache_for('get_dispatches_by_device', args=(None, device_id))
            invalidate_cache_for('get_dispatch_history', args=(None, device_id))
    
    @staticmethod
    def invalidate_dispatch_cache() -> None:
        """Invalidate dispatch-related cache entries."""
        invalidate_cache_for('get_pending_dispatches')
        invalidate_cache_for('get_scheduled_dispatches')
    
    @staticmethod
    def invalidate_protocol_cache() -> None:
        """Invalidate protocol mapping cache entries."""
        invalidate_cache_for('get_protocol_mappings')
    
    @staticmethod
    def invalidate_analysis_cache() -> None:
        """Invalidate analysis result cache entries."""
        invalidate_cache_for('get_analysis_results')
