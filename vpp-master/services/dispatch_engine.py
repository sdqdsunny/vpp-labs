"""
Dispatch Engine Service

Handles dispatch command creation, execution, scheduling, and tracking.
"""

import uuid
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError
from utils.database import SessionLocal
from utils.logger import setup_logger
from utils.errors import (
    ValidationError, DeviceNotFoundError, DispatchExecutionError,
    DatabaseError
)
from utils.metrics import (
    dispatch_total, dispatch_duration_seconds, dispatch_retry_total,
    record_dispatch_command, record_dispatch_retry, time_database_query
)
from models.dispatch import Dispatch
from models.device import Device
from utils.validators import DispatchRequest, ScheduledDispatchRequest
from services.device_manager import DeviceManager
from services.event_emitter import get_event_emitter, EventEmitter

logger = setup_logger(__name__)


class DispatchEngine:
    """Manages dispatch command creation, execution, scheduling, and tracking"""
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_BACKOFF = [1, 2, 4]  # Exponential backoff in seconds
    
    def __init__(self):
        """Initialize dispatch engine"""
        self.session = SessionLocal()
        self.device_manager = DeviceManager()
        self.event_emitter = get_event_emitter()
    
    def __del__(self):
        """Cleanup session"""
        if self.session:
            self.session.close()
    
    @time_database_query("dispatch_creation")
    def create_dispatch(self, dispatch_data: DispatchRequest) -> Dispatch:
        """
        Create a new dispatch command
        
        Args:
            dispatch_data: Dispatch request data
        
        Returns:
            Created Dispatch instance
        
        Raises:
            ValidationError: If dispatch data is invalid
            DeviceNotFoundError: If device not found
            DispatchExecutionError: If device is offline
            DatabaseError: If database operation fails
        """
        try:
            # Check if device exists
            device = self.session.query(Device).filter_by(
                id=dispatch_data.device_id
            ).first()
            
            if not device:
                logger.warning(
                    f"Dispatch creation failed: device not found: {dispatch_data.device_id}"
                )
                raise DeviceNotFoundError(
                    f"Device with ID '{dispatch_data.device_id}' not found",
                    details={"device_id": dispatch_data.device_id}
                )
            
            # Check if device is online
            if device.status != "online":
                logger.warning(
                    f"Dispatch creation failed: device offline: {dispatch_data.device_id}"
                )
                raise DispatchExecutionError(
                    f"Device '{dispatch_data.device_id}' is not online (status: {device.status})",
                    details={"device_id": dispatch_data.device_id, "status": device.status}
                )
            
            # Create dispatch
            dispatch = Dispatch(
                id=str(uuid.uuid4()),
                device_id=dispatch_data.device_id,
                command_type=dispatch_data.command_type,
                target_value=dispatch_data.target_value,
                priority_level=dispatch_data.priority_level,
                status="pending",
                retry_count=0
            )
            
            self.session.add(dispatch)
            self.session.commit()
            
            logger.info(
                f"Dispatch created: {dispatch.id}",
                extra={
                    "dispatch_id": dispatch.id,
                    "device_id": dispatch_data.device_id,
                    "command_type": dispatch_data.command_type,
                    "target_value": dispatch_data.target_value
                }
            )
            
            # Record metrics
            record_dispatch_command("pending")
            
            # Emit dispatch.created event
            self.event_emitter.emit(EventEmitter.DISPATCH_CREATED, {
                "dispatch_id": dispatch.id,
                "device_id": dispatch_data.device_id,
                "command_type": dispatch_data.command_type,
                "target_value": dispatch_data.target_value,
                "priority_level": dispatch_data.priority_level,
                "status": dispatch.status,
                "created_at": dispatch.created_at.isoformat()
            })
            
            return dispatch
        
        except (ValidationError, DeviceNotFoundError, DispatchExecutionError):
            raise
        except Exception as e:
            logger.error(f"Failed to create dispatch: {str(e)}")
            raise DatabaseError(f"Failed to create dispatch: {str(e)}")
    
    @time_database_query("dispatch_execution")
    def execute_dispatch(self, dispatch_id: str) -> Dict[str, Any]:
        """
        Execute a dispatch command
        
        Args:
            dispatch_id: Dispatch ID to execute
        
        Returns:
            Dispatch result dictionary
        
        Raises:
            DeviceNotFoundError: If dispatch not found
            DispatchExecutionError: If execution fails
            DatabaseError: If database operation fails
        """
        try:
            # Retrieve dispatch
            dispatch = self.session.query(Dispatch).filter_by(id=dispatch_id).first()
            
            if not dispatch:
                logger.warning(f"Dispatch execution failed: dispatch not found: {dispatch_id}")
                raise DeviceNotFoundError(
                    f"Dispatch with ID '{dispatch_id}' not found",
                    details={"dispatch_id": dispatch_id}
                )
            
            # Update status to executing
            dispatch.mark_executing()
            self.session.commit()
            
            logger.info(f"Dispatch executing: {dispatch_id}")
            
            # Simulate command execution (in real implementation, would send to Protocol_Converter)
            try:
                # Simulate execution delay
                time.sleep(0.1)
                
                # Mark as completed
                result_data = {
                    "status": "success",
                    "executed_at": datetime.utcnow().isoformat(),
                    "target_value": dispatch.target_value
                }
                dispatch.mark_completed(result_data)
                self.session.commit()
                
                logger.info(f"Dispatch completed: {dispatch_id}")
                record_dispatch_command("completed")
                
                # Emit dispatch.completed event
                self.event_emitter.emit(EventEmitter.DISPATCH_COMPLETED, {
                    "dispatch_id": dispatch.id,
                    "device_id": dispatch.device_id,
                    "command_type": dispatch.command_type,
                    "status": dispatch.status,
                    "execution_time": dispatch.execution_time.isoformat() if dispatch.execution_time else None,
                    "completed_at": datetime.utcnow().isoformat()
                })
                
                return result_data
            
            except Exception as e:
                logger.error(f"Dispatch execution failed: {str(e)}")
                dispatch.mark_failed(str(e))
                self.session.commit()
                record_dispatch_command("failed")
                
                # Emit dispatch.failed event
                self.event_emitter.emit(EventEmitter.DISPATCH_FAILED, {
                    "dispatch_id": dispatch.id,
                    "device_id": dispatch.device_id,
                    "command_type": dispatch.command_type,
                    "status": dispatch.status,
                    "error_message": str(e),
                    "retry_count": dispatch.retry_count,
                    "failed_at": datetime.utcnow().isoformat()
                })
                
                raise DispatchExecutionError(f"Dispatch execution failed: {str(e)}")
        
        except (DeviceNotFoundError, DispatchExecutionError):
            raise
        except Exception as e:
            logger.error(f"Failed to execute dispatch: {str(e)}")
            raise DatabaseError(f"Failed to execute dispatch: {str(e)}")
    
    @time_database_query("dispatch_scheduling")
    def schedule_dispatch(
        self,
        dispatch_data: ScheduledDispatchRequest
    ) -> Dispatch:
        """
        Schedule a dispatch for future execution
        
        Args:
            dispatch_data: Scheduled dispatch request data
        
        Returns:
            Created Dispatch instance
        
        Raises:
            ValidationError: If dispatch data is invalid
            DeviceNotFoundError: If device not found
            DispatchExecutionError: If device is offline
            DatabaseError: If database operation fails
        """
        try:
            # Check if device exists
            device = self.session.query(Device).filter_by(
                id=dispatch_data.device_id
            ).first()
            
            if not device:
                logger.warning(
                    f"Dispatch scheduling failed: device not found: {dispatch_data.device_id}"
                )
                raise DeviceNotFoundError(
                    f"Device with ID '{dispatch_data.device_id}' not found",
                    details={"device_id": dispatch_data.device_id}
                )
            
            # Create scheduled dispatch
            dispatch = Dispatch(
                id=str(uuid.uuid4()),
                device_id=dispatch_data.device_id,
                command_type=dispatch_data.command_type,
                target_value=dispatch_data.target_value,
                priority_level=dispatch_data.priority_level,
                status="pending",
                scheduled_time=dispatch_data.execution_time,
                retry_count=0
            )
            
            self.session.add(dispatch)
            self.session.commit()
            
            logger.info(
                f"Dispatch scheduled: {dispatch.id}",
                extra={
                    "dispatch_id": dispatch.id,
                    "device_id": dispatch_data.device_id,
                    "scheduled_time": dispatch_data.execution_time.isoformat()
                }
            )
            
            record_dispatch_command("pending")
            
            return dispatch
        
        except (ValidationError, DeviceNotFoundError, DispatchExecutionError):
            raise
        except Exception as e:
            logger.error(f"Failed to schedule dispatch: {str(e)}")
            raise DatabaseError(f"Failed to schedule dispatch: {str(e)}")
    
    @time_database_query("dispatch_status_query")
    def get_dispatch_status(self, dispatch_id: str) -> Dict[str, Any]:
        """
        Get dispatch status
        
        Args:
            dispatch_id: Dispatch ID
        
        Returns:
            Dispatch status dictionary
        
        Raises:
            DeviceNotFoundError: If dispatch not found
            DatabaseError: If database operation fails
        """
        try:
            dispatch = self.session.query(Dispatch).filter_by(id=dispatch_id).first()
            
            if not dispatch:
                logger.warning(f"Dispatch status query failed: dispatch not found: {dispatch_id}")
                raise DeviceNotFoundError(
                    f"Dispatch with ID '{dispatch_id}' not found",
                    details={"dispatch_id": dispatch_id}
                )
            
            return {
                "dispatch_id": dispatch.id,
                "status": dispatch.status,
                "execution_time": dispatch.execution_time.isoformat() if dispatch.execution_time else None,
                "retry_count": dispatch.retry_count,
                "error_message": dispatch.error_message,
                "updated_at": dispatch.updated_at.isoformat()
            }
        
        except DeviceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get dispatch status: {str(e)}")
            raise DatabaseError(f"Failed to get dispatch status: {str(e)}")
    
    @time_database_query("dispatch_history_query")
    def get_dispatch_history(
        self,
        device_id: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get dispatch history with filters and pagination
        
        Args:
            device_id: Filter by device ID
            status: Filter by status
            start_time: Filter by start time
            end_time: Filter by end time
            page: Page number (1-indexed)
            page_size: Number of results per page
        
        Returns:
            Dictionary with dispatch records and pagination metadata
        
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = self.session.query(Dispatch)
            
            # Apply filters
            if device_id:
                query = query.filter_by(device_id=device_id)
            if status:
                query = query.filter_by(status=status)
            if start_time:
                query = query.filter(Dispatch.created_at >= start_time)
            if end_time:
                query = query.filter(Dispatch.created_at <= end_time)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            dispatches = query.order_by(Dispatch.created_at.desc()).offset(offset).limit(page_size).all()
            
            logger.info(
                f"Dispatch history query completed",
                extra={
                    "total_count": total_count,
                    "page": page,
                    "page_size": page_size,
                    "results": len(dispatches)
                }
            )
            
            return {
                "dispatches": [d.to_dict() for d in dispatches],
                "pagination": {
                    "total_count": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to get dispatch history: {str(e)}")
            raise DatabaseError(f"Failed to get dispatch history: {str(e)}")
    
    @time_database_query("dispatch_cancellation")
    def cancel_scheduled_dispatch(self, dispatch_id: str) -> None:
        """
        Cancel a scheduled dispatch
        
        Args:
            dispatch_id: Dispatch ID to cancel
        
        Raises:
            DeviceNotFoundError: If dispatch not found
            DispatchExecutionError: If dispatch cannot be cancelled
            DatabaseError: If database operation fails
        """
        try:
            dispatch = self.session.query(Dispatch).filter_by(id=dispatch_id).first()
            
            if not dispatch:
                logger.warning(f"Dispatch cancellation failed: dispatch not found: {dispatch_id}")
                raise DeviceNotFoundError(
                    f"Dispatch with ID '{dispatch_id}' not found",
                    details={"dispatch_id": dispatch_id}
                )
            
            # Check if dispatch is scheduled
            if not dispatch.scheduled_time:
                logger.warning(f"Dispatch cancellation failed: dispatch not scheduled: {dispatch_id}")
                raise DispatchExecutionError(
                    f"Dispatch '{dispatch_id}' is not scheduled",
                    details={"dispatch_id": dispatch_id}
                )
            
            # Check if dispatch has already executed
            if dispatch.status in ["completed", "failed"]:
                logger.warning(f"Dispatch cancellation failed: dispatch already executed: {dispatch_id}")
                raise DispatchExecutionError(
                    f"Cannot cancel dispatch '{dispatch_id}' with status '{dispatch.status}'",
                    details={"dispatch_id": dispatch_id, "status": dispatch.status}
                )
            
            # Update status to cancelled
            dispatch.status = "cancelled"
            dispatch.updated_at = datetime.utcnow()
            self.session.commit()
            
            logger.info(f"Dispatch cancelled: {dispatch_id}")
            record_dispatch_command("cancelled")
        
        except (DeviceNotFoundError, DispatchExecutionError):
            raise
        except Exception as e:
            logger.error(f"Failed to cancel dispatch: {str(e)}")
            raise DatabaseError(f"Failed to cancel dispatch: {str(e)}")
    
    @time_database_query("dispatch_retry")
    def retry_failed_dispatch(self, dispatch_id: str) -> Dict[str, Any]:
        """
        Retry a failed dispatch with exponential backoff
        
        Args:
            dispatch_id: Dispatch ID to retry
        
        Returns:
            Dispatch result dictionary
        
        Raises:
            DeviceNotFoundError: If dispatch not found
            DispatchExecutionError: If dispatch cannot be retried
            DatabaseError: If database operation fails
        """
        try:
            dispatch = self.session.query(Dispatch).filter_by(id=dispatch_id).first()
            
            if not dispatch:
                logger.warning(f"Dispatch retry failed: dispatch not found: {dispatch_id}")
                raise DeviceNotFoundError(
                    f"Dispatch with ID '{dispatch_id}' not found",
                    details={"dispatch_id": dispatch_id}
                )
            
            # Check if dispatch is failed
            if dispatch.status != "failed":
                logger.warning(f"Dispatch retry failed: dispatch not failed: {dispatch_id}")
                raise DispatchExecutionError(
                    f"Cannot retry dispatch '{dispatch_id}' with status '{dispatch.status}'",
                    details={"dispatch_id": dispatch_id, "status": dispatch.status}
                )
            
            # Check if max retries exceeded
            if dispatch.retry_count >= self.MAX_RETRIES:
                logger.warning(f"Dispatch retry failed: max retries exceeded: {dispatch_id}")
                raise DispatchExecutionError(
                    f"Dispatch '{dispatch_id}' has exceeded maximum retries ({self.MAX_RETRIES})",
                    details={"dispatch_id": dispatch_id, "retry_count": dispatch.retry_count}
                )
            
            # Perform retry with exponential backoff
            backoff_time = self.RETRY_BACKOFF[dispatch.retry_count]
            logger.info(f"Retrying dispatch {dispatch_id} after {backoff_time}s backoff")
            time.sleep(backoff_time)
            
            # Increment retry count
            dispatch.increment_retry()
            self.session.commit()
            
            record_dispatch_retry(dispatch.command_type)
            
            # Execute dispatch
            try:
                dispatch.mark_executing()
                self.session.commit()
                
                # Simulate execution
                time.sleep(0.1)
                
                result_data = {
                    "status": "success",
                    "executed_at": datetime.utcnow().isoformat(),
                    "target_value": dispatch.target_value,
                    "retry_count": dispatch.retry_count
                }
                dispatch.mark_completed(result_data)
                self.session.commit()
                
                logger.info(f"Dispatch retry succeeded: {dispatch_id}")
                record_dispatch_command("completed")
                
                # Emit dispatch.completed event
                self.event_emitter.emit(EventEmitter.DISPATCH_COMPLETED, {
                    "dispatch_id": dispatch.id,
                    "device_id": dispatch.device_id,
                    "command_type": dispatch.command_type,
                    "status": dispatch.status,
                    "execution_time": dispatch.execution_time.isoformat() if dispatch.execution_time else None,
                    "retry_count": dispatch.retry_count,
                    "completed_at": datetime.utcnow().isoformat()
                })
                
                return result_data
            
            except Exception as e:
                logger.error(f"Dispatch retry execution failed: {str(e)}")
                dispatch.mark_failed(str(e))
                self.session.commit()
                record_dispatch_command("failed")
                
                # Emit dispatch.failed event
                self.event_emitter.emit(EventEmitter.DISPATCH_FAILED, {
                    "dispatch_id": dispatch.id,
                    "device_id": dispatch.device_id,
                    "command_type": dispatch.command_type,
                    "status": dispatch.status,
                    "error_message": str(e),
                    "retry_count": dispatch.retry_count,
                    "failed_at": datetime.utcnow().isoformat()
                })
                
                raise DispatchExecutionError(f"Dispatch retry execution failed: {str(e)}")
        
        except (DeviceNotFoundError, DispatchExecutionError):
            raise
        except Exception as e:
            logger.error(f"Failed to retry dispatch: {str(e)}")
            raise DatabaseError(f"Failed to retry dispatch: {str(e)}")
