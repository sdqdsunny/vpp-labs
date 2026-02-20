"""
Bottle routes for VCC real-time data reception API.

Endpoints:
- POST /api/vcc/report/power - Receive power generation data
- POST /api/vcc/report/storage - Receive storage data
- POST /api/vcc/report/demand - Receive demand data

Features:
- Request validation
- Error handling
- JSON response format
- Logging
"""

import logging
import json
from datetime import datetime
from bottle import Bottle, request, response
from uuid import uuid4

from models.realtime_data_models import (
    PowerGenerationData, StorageData, DemandData,
    PowerCommand, StorageCommand, DemandCommand
)
from services.vcc_data_reception import VCCDataReceptionService
from services.command_execution import CommandExecutionService

logger = logging.getLogger(__name__)

# Global reception service instance
_reception_service = None

# Global command execution service instances
_power_execution_service = None
_storage_execution_service = None
_demand_execution_service = None


def init_reception_service(db_session=None):
    """Initialize the reception service."""
    global _reception_service
    _reception_service = VCCDataReceptionService(db_session=db_session)
    return _reception_service


def get_reception_service():
    """Get the reception service instance."""
    global _reception_service
    if _reception_service is None:
        _reception_service = VCCDataReceptionService()
    return _reception_service


def init_power_execution_service(module_id: str = "vpp-power-generation"):
    """Initialize the power execution service."""
    global _power_execution_service
    _power_execution_service = CommandExecutionService(module_id=module_id)
    return _power_execution_service


def get_power_execution_service():
    """Get the power execution service instance."""
    global _power_execution_service
    if _power_execution_service is None:
        _power_execution_service = CommandExecutionService(module_id="vpp-power-generation")
    return _power_execution_service


def init_storage_execution_service(module_id: str = "vpp-storage"):
    """Initialize the storage execution service."""
    global _storage_execution_service
    _storage_execution_service = CommandExecutionService(module_id=module_id)
    return _storage_execution_service


def get_storage_execution_service():
    """Get the storage execution service instance."""
    global _storage_execution_service
    if _storage_execution_service is None:
        _storage_execution_service = CommandExecutionService(module_id="vpp-storage")
    return _storage_execution_service


def init_demand_execution_service(module_id: str = "vpp-demand"):
    """Initialize the demand execution service."""
    global _demand_execution_service
    _demand_execution_service = CommandExecutionService(module_id=module_id)
    return _demand_execution_service


def get_demand_execution_service():
    """Get the demand execution service instance."""
    global _demand_execution_service
    if _demand_execution_service is None:
        _demand_execution_service = CommandExecutionService(module_id="vpp-demand")
    return _demand_execution_service


def create_realtime_data_routes(app: Bottle):
    """Register realtime data routes with Bottle app."""
    
    @app.route('/api/vcc/report/power', method='POST')
    def report_power_generation():
        """
        Receive power generation data from power side module.
        
        Expected JSON:
        {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_power": 150.5,
            "solar_power": 100.0,
            "wind_power": 50.5,
            "efficiency": 95.5,
            "device_status": "running"
        }
        
        Returns:
        {
            "status": "success",
            "message": "Data received and stored",
            "request_id": "uuid"
        }
        """
        request_id = str(uuid4())
        response.content_type = 'application/json'
        
        try:
            # Get JSON data
            try:
                data = request.json
            except:
                data = None
                
            if not data:
                logger.warning(f"[{request_id}] Empty request body for power data")
                response.status = 400
                return json.dumps({
                    "status": "error",
                    "message": "Empty request body",
                    "request_id": request_id
                })
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                timestamp = datetime.now()
            
            # Create data model
            power_data = PowerGenerationData(
                timestamp=timestamp,
                current_power=float(data.get('current_power', 0)),
                solar_power=float(data.get('solar_power', 0)),
                wind_power=float(data.get('wind_power', 0)),
                efficiency=float(data.get('efficiency', 0)),
                device_status=str(data.get('device_status', 'unknown'))
            )
            
            # Receive data
            service = get_reception_service()
            result = service.receive_power_generation_data(power_data)
            
            if result:
                logger.info(f"[{request_id}] Power generation data received successfully")
                response.status = 200
                return json.dumps({
                    "status": "success",
                    "message": "Data received and stored",
                    "request_id": request_id
                })
            else:
                logger.error(f"[{request_id}] Failed to receive power generation data")
                response.status = 500
                return json.dumps({
                    "status": "error",
                    "message": "Failed to store data",
                    "request_id": request_id
                })
                
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"[{request_id}] Invalid power data format: {str(e)}")
            response.status = 400
            return json.dumps({
                "status": "error",
                "message": f"Invalid data format: {str(e)}",
                "request_id": request_id
            })
        except Exception as e:
            logger.error(f"[{request_id}] Unexpected error: {str(e)}")
            response.status = 500
            return json.dumps({
                "status": "error",
                "message": "Internal server error",
                "request_id": request_id
            })
    
    @app.route('/api/vcc/report/storage', method='POST')
    def report_storage():
        """
        Receive storage data from storage side module.
        
        Expected JSON:
        {
            "timestamp": "2024-01-15T10:30:00Z",
            "soc": 75.5,
            "soh": 98.0,
            "current_power": 50.0,
            "charge_status": "charging",
            "temperature": 25.5
        }
        
        Returns:
        {
            "status": "success",
            "message": "Data received and stored",
            "request_id": "uuid"
        }
        """
        request_id = str(uuid4())
        response.content_type = 'application/json'
        
        try:
            # Get JSON data
            try:
                data = request.json
            except:
                data = None
                
            if not data:
                logger.warning(f"[{request_id}] Empty request body for storage data")
                response.status = 400
                return json.dumps({
                    "status": "error",
                    "message": "Empty request body",
                    "request_id": request_id
                })
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                timestamp = datetime.now()
            
            # Create data model
            storage_data = StorageData(
                timestamp=timestamp,
                soc=float(data.get('soc', 0)),
                soh=float(data.get('soh', 0)),
                current_power=float(data.get('current_power', 0)),
                charge_status=str(data.get('charge_status', 'idle')),
                temperature=float(data.get('temperature', 0))
            )
            
            # Receive data
            service = get_reception_service()
            result = service.receive_storage_data(storage_data)
            
            if result:
                logger.info(f"[{request_id}] Storage data received successfully")
                response.status = 200
                return json.dumps({
                    "status": "success",
                    "message": "Data received and stored",
                    "request_id": request_id
                })
            else:
                logger.error(f"[{request_id}] Failed to receive storage data")
                response.status = 500
                return json.dumps({
                    "status": "error",
                    "message": "Failed to store data",
                    "request_id": request_id
                })
                
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"[{request_id}] Invalid storage data format: {str(e)}")
            response.status = 400
            return json.dumps({
                "status": "error",
                "message": f"Invalid data format: {str(e)}",
                "request_id": request_id
            })
        except Exception as e:
            logger.error(f"[{request_id}] Unexpected error: {str(e)}")
            response.status = 500
            return json.dumps({
                "status": "error",
                "message": "Internal server error",
                "request_id": request_id
            })
    
    @app.route('/api/vcc/report/demand', method='POST')
    def report_demand():
        """
        Receive demand data from demand side module.
        
        Expected JSON:
        {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_load": 200.0,
            "forecast_load": 210.0,
            "adjustable_range": [180.0, 220.0],
            "dr_status": "active"
        }
        
        Returns:
        {
            "status": "success",
            "message": "Data received and stored",
            "request_id": "uuid"
        }
        """
        request_id = str(uuid4())
        response.content_type = 'application/json'
        
        try:
            # Get JSON data
            try:
                data = request.json
            except:
                data = None
                
            if not data:
                logger.warning(f"[{request_id}] Empty request body for demand data")
                response.status = 400
                return json.dumps({
                    "status": "error",
                    "message": "Empty request body",
                    "request_id": request_id
                })
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                timestamp = datetime.now()
            
            # Parse adjustable range
            adjustable_range = data.get('adjustable_range', [0, 0])
            if isinstance(adjustable_range, list) and len(adjustable_range) == 2:
                adjustable_range = tuple(adjustable_range)
            else:
                adjustable_range = (0, 0)
            
            # Create data model
            demand_data = DemandData(
                timestamp=timestamp,
                current_load=float(data.get('current_load', 0)),
                forecast_load=float(data.get('forecast_load', 0)),
                adjustable_range=adjustable_range,
                dr_status=str(data.get('dr_status', 'inactive'))
            )
            
            # Receive data
            service = get_reception_service()
            result = service.receive_demand_data(demand_data)
            
            if result:
                logger.info(f"[{request_id}] Demand data received successfully")
                response.status = 200
                return json.dumps({
                    "status": "success",
                    "message": "Data received and stored",
                    "request_id": request_id
                })
            else:
                logger.error(f"[{request_id}] Failed to receive demand data")
                response.status = 500
                return json.dumps({
                    "status": "error",
                    "message": "Failed to store data",
                    "request_id": request_id
                })
                
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"[{request_id}] Invalid demand data format: {str(e)}")
            response.status = 400
            return json.dumps({
                "status": "error",
                "message": f"Invalid data format: {str(e)}",
                "request_id": request_id
            })
        except Exception as e:
            logger.error(f"[{request_id}] Unexpected error: {str(e)}")
            response.status = 500
            return json.dumps({
                "status": "error",
                "message": "Internal server error",
                "request_id": request_id
            })
    
    logger.info("Real-time data reception routes registered")


def create_command_execution_routes(app: Bottle):
    """Register command execution routes with Bottle app."""
    
    @app.route('/api/side/command/power', method='POST')
    def execute_power_command():
        """
        Execute power generation control command.
        
        Expected JSON:
        {
            "command_id": "power_001",
            "target_power": 160.0,
            "duration": 300,
            "priority": 1
        }
        
        Returns:
        {
            "status": "success",
            "command_id": "power_001",
            "execution_status": "completed",
            "result": {...}
        }
        """
        request_id = str(uuid4())
        response.content_type = 'application/json'
        
        try:
            # Get JSON data
            try:
                data = request.json
            except:
                data = None
                
            if not data:
                logger.warning(f"[{request_id}] Empty request body for power command")
                response.status = 400
                return json.dumps({
                    "status": "error",
                    "message": "Empty request body",
                    "request_id": request_id
                })
            
            # Create power command
            power_cmd = PowerCommand(
                command_id=str(data.get('command_id', str(uuid4()))),
                target_power=float(data.get('target_power', 0)),
                duration=int(data.get('duration', 300)),
                priority=int(data.get('priority', 1))
            )
            
            # Execute command
            service = get_power_execution_service()
            result = service.execute_power_command(power_cmd)
            
            logger.info(f"[{request_id}] Power command executed: {result.command_id}, "
                       f"status={result.status}")
            response.status = 200
            return json.dumps({
                "status": "success",
                "command_id": result.command_id,
                "execution_status": result.status,
                "result": result.result,
                "error_message": result.error_message,
                "request_id": request_id
            })
                
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"[{request_id}] Invalid power command format: {str(e)}")
            response.status = 400
            return json.dumps({
                "status": "error",
                "message": f"Invalid command format: {str(e)}",
                "request_id": request_id
            })
        except Exception as e:
            logger.error(f"[{request_id}] Unexpected error: {str(e)}")
            response.status = 500
            return json.dumps({
                "status": "error",
                "message": "Internal server error",
                "request_id": request_id
            })
    
    @app.route('/api/side/command/storage', method='POST')
    def execute_storage_command():
        """
        Execute storage control command.
        
        Expected JSON:
        {
            "command_id": "storage_001",
            "action": "charging",
            "target_power": 80.0,
            "duration": 300
        }
        
        Returns:
        {
            "status": "success",
            "command_id": "storage_001",
            "execution_status": "completed",
            "result": {...}
        }
        """
        request_id = str(uuid4())
        response.content_type = 'application/json'
        
        try:
            # Get JSON data
            try:
                data = request.json
            except:
                data = None
                
            if not data:
                logger.warning(f"[{request_id}] Empty request body for storage command")
                response.status = 400
                return json.dumps({
                    "status": "error",
                    "message": "Empty request body",
                    "request_id": request_id
                })
            
            # Create storage command
            storage_cmd = StorageCommand(
                command_id=str(data.get('command_id', str(uuid4()))),
                action=str(data.get('action', 'idle')),
                target_power=float(data.get('target_power', 0)),
                duration=int(data.get('duration', 300))
            )
            
            # Execute command
            service = get_storage_execution_service()
            result = service.execute_storage_command(storage_cmd)
            
            logger.info(f"[{request_id}] Storage command executed: {result.command_id}, "
                       f"status={result.status}")
            response.status = 200
            return json.dumps({
                "status": "success",
                "command_id": result.command_id,
                "execution_status": result.status,
                "result": result.result,
                "error_message": result.error_message,
                "request_id": request_id
            })
                
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"[{request_id}] Invalid storage command format: {str(e)}")
            response.status = 400
            return json.dumps({
                "status": "error",
                "message": f"Invalid command format: {str(e)}",
                "request_id": request_id
            })
        except Exception as e:
            logger.error(f"[{request_id}] Unexpected error: {str(e)}")
            response.status = 500
            return json.dumps({
                "status": "error",
                "message": "Internal server error",
                "request_id": request_id
            })
    
    @app.route('/api/side/command/demand', method='POST')
    def execute_demand_command():
        """
        Execute demand response control command.
        
        Expected JSON:
        {
            "command_id": "demand_001",
            "action": "increase",
            "target_load": 220.0,
            "duration": 300
        }
        
        Returns:
        {
            "status": "success",
            "command_id": "demand_001",
            "execution_status": "completed",
            "result": {...}
        }
        """
        request_id = str(uuid4())
        response.content_type = 'application/json'
        
        try:
            # Get JSON data
            try:
                data = request.json
            except:
                data = None
                
            if not data:
                logger.warning(f"[{request_id}] Empty request body for demand command")
                response.status = 400
                return json.dumps({
                    "status": "error",
                    "message": "Empty request body",
                    "request_id": request_id
                })
            
            # Create demand command
            demand_cmd = DemandCommand(
                command_id=str(data.get('command_id', str(uuid4()))),
                action=str(data.get('action', 'maintain')),
                target_load=float(data.get('target_load', 0)),
                duration=int(data.get('duration', 300))
            )
            
            # Execute command
            service = get_demand_execution_service()
            result = service.execute_demand_command(demand_cmd)
            
            logger.info(f"[{request_id}] Demand command executed: {result.command_id}, "
                       f"status={result.status}")
            response.status = 200
            return json.dumps({
                "status": "success",
                "command_id": result.command_id,
                "execution_status": result.status,
                "result": result.result,
                "error_message": result.error_message,
                "request_id": request_id
            })
                
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"[{request_id}] Invalid demand command format: {str(e)}")
            response.status = 400
            return json.dumps({
                "status": "error",
                "message": f"Invalid command format: {str(e)}",
                "request_id": request_id
            })
        except Exception as e:
            logger.error(f"[{request_id}] Unexpected error: {str(e)}")
            response.status = 500
            return json.dumps({
                "status": "error",
                "message": "Internal server error",
                "request_id": request_id
            })
    
    logger.info("Command execution routes registered")
