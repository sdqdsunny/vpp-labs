"""
Scenario Management API Routes

Provides REST endpoints for scenario creation, execution, data retrieval, and export.

Requirements:
- 10.1: Scenario data persistence
- 10.2: Scenario data retrieval
- 10.3: Scenario reproducibility
- 10.4: Scenario data export
- 10.5: Scenario query performance
"""

from bottle import Bottle, request, response, HTTPError
from typing import Dict, Any, List, Optional
import json
import csv
import io
from datetime import datetime
import logging

from services.scenario_engine import ScenarioEngine
from models.scenario import Scenario
from utils.errors import ValidationError, SimulatorError
from utils.logger import get_logger
from utils.database import get_session

logger = get_logger(__name__)

# Global scenario engine instance
scenario_engine = ScenarioEngine()


def create_scenario_routes(app: Bottle) -> None:
    """
    Register scenario management API routes.
    
    Args:
        app: Bottle application instance
    """
    
    @app.post('/api/v1/scenarios')
    def create_scenario():
        """
        Create a new scenario.
        
        Request body:
        {
            "name": "Test Scenario 1",
            "description": "Test scenario description",
            "definition": {...}
        }
        """
        try:
            data = request.json
            
            # Validate required fields
            if not data.get('name'):
                raise ValidationError("name is required")
            if not data.get('definition'):
                raise ValidationError("definition is required")
            
            name = data['name']
            description = data.get('description', '')
            definition = data['definition']
            
            # Create scenario
            scenario = scenario_engine.create_scenario({
                'name': name,
                'description': description,
                'definition': definition
            })
            
            response.status = 201
            return {
                'scenario_id': scenario.id,
                'name': scenario.name,
                'status': scenario.status,
                'created_at': scenario.created_at.isoformat()
            }
            
        except ValidationError as e:
            response.status = 400
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to create scenario: {str(e)}")
            response.status = 500
            return {'error': 'Failed to create scenario'}
    
    @app.get('/api/v1/scenarios/<scenario_id>')
    def get_scenario(scenario_id: str):
        """
        Get scenario details.
        
        Returns:
        {
            "scenario_id": "scenario-001",
            "name": "Test Scenario 1",
            "status": "completed",
            "definition": {...},
            "results": {...}
        }
        """
        try:
            session = get_session()
            scenario = session.query(Scenario).filter_by(id=scenario_id).first()
            
            if not scenario:
                raise ValidationError(f"Scenario not found: {scenario_id}")
            
            return {
                'scenario_id': scenario.id,
                'name': scenario.name,
                'description': scenario.description,
                'status': scenario.status,
                'definition': scenario.definition,
                'created_at': scenario.created_at.isoformat(),
                'start_time': scenario.start_time.isoformat() if scenario.start_time else None,
                'end_time': scenario.end_time.isoformat() if scenario.end_time else None
            }
            
        except ValidationError as e:
            response.status = 404
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to get scenario: {str(e)}")
            response.status = 500
            return {'error': 'Failed to get scenario'}
    
    @app.get('/api/v1/scenarios')
    def list_scenarios():
        """
        List all scenarios.
        
        Query parameters:
        - status: Filter by status (pending, running, completed, failed)
        - limit: Maximum number of results (default: 100)
        - offset: Offset for pagination (default: 0)
        
        Returns:
        {
            "scenarios": [...],
            "total": 10,
            "limit": 100,
            "offset": 0
        }
        """
        try:
            session = get_session()
            
            # Get query parameters
            status = request.query.get('status')
            limit = int(request.query.get('limit', 100))
            offset = int(request.query.get('offset', 0))
            
            # Build query
            query = session.query(Scenario)
            
            if status:
                query = query.filter_by(status=status)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            scenarios = query.order_by(Scenario.created_at.desc()).limit(limit).offset(offset).all()
            
            return {
                'scenarios': [
                    {
                        'scenario_id': s.id,
                        'name': s.name,
                        'status': s.status,
                        'created_at': s.created_at.isoformat()
                    }
                    for s in scenarios
                ],
                'total': total,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            logger.error(f"Failed to list scenarios: {str(e)}")
            response.status = 500
            return {'error': 'Failed to list scenarios'}
    
    @app.post('/api/v1/scenarios/<scenario_id>/execute')
    def execute_scenario(scenario_id: str):
        """
        Execute a scenario.
        
        Returns:
        {
            "scenario_id": "scenario-001",
            "status": "running",
            "execution_id": "exec-001"
        }
        """
        try:
            session = get_session()
            scenario = session.query(Scenario).filter_by(id=scenario_id).first()
            
            if not scenario:
                raise ValidationError(f"Scenario not found: {scenario_id}")
            
            # Execute scenario
            result = scenario_engine.execute_scenario(scenario_id)
            
            return {
                'scenario_id': scenario_id,
                'status': result.status,
                'execution_time_ms': result.execution_time,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ValidationError as e:
            response.status = 404
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to execute scenario: {str(e)}")
            response.status = 500
            return {'error': 'Failed to execute scenario'}
    
    @app.get('/api/v1/scenarios/<scenario_id>/status')
    def get_scenario_status(scenario_id: str):
        """
        Get scenario execution status.
        
        Returns:
        {
            "scenario_id": "scenario-001",
            "status": "running",
            "progress": 0.5,
            "events_executed": 50,
            "total_events": 100
        }
        """
        try:
            status = scenario_engine.get_scenario_status(scenario_id)
            
            return {
                'scenario_id': scenario_id,
                'status': status.get('status'),
                'progress': status.get('progress', 0),
                'events_executed': status.get('events_executed', 0),
                'total_events': status.get('total_events', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get scenario status: {str(e)}")
            response.status = 500
            return {'error': 'Failed to get scenario status'}
    
    @app.get('/api/v1/scenarios/<scenario_id>/results')
    def get_scenario_results(scenario_id: str):
        """
        Get scenario execution results.
        
        Returns:
        {
            "scenario_id": "scenario-001",
            "status": "completed",
            "results": {...},
            "metrics": {...}
        }
        """
        try:
            session = get_session()
            scenario = session.query(Scenario).filter_by(id=scenario_id).first()
            
            if not scenario:
                raise ValidationError(f"Scenario not found: {scenario_id}")
            
            results = scenario_engine.get_scenario_results(scenario_id)
            
            return {
                'scenario_id': scenario_id,
                'status': scenario.status,
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ValidationError as e:
            response.status = 404
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to get scenario results: {str(e)}")
            response.status = 500
            return {'error': 'Failed to get scenario results'}
    
    @app.post('/api/v1/scenarios/<scenario_id>/export')
    def export_scenario(scenario_id: str):
        """
        Export scenario data.
        
        Query parameters:
        - format: Export format (json, csv) - default: json
        
        Returns:
        - JSON format: Scenario data as JSON
        - CSV format: Scenario data as CSV
        """
        try:
            session = get_session()
            scenario = session.query(Scenario).filter_by(id=scenario_id).first()
            
            if not scenario:
                raise ValidationError(f"Scenario not found: {scenario_id}")
            
            export_format = request.query.get('format', 'json')
            
            if export_format == 'json':
                response.content_type = 'application/json'
                return {
                    'scenario_id': scenario.id,
                    'name': scenario.name,
                    'description': scenario.description,
                    'definition': scenario.definition,
                    'status': scenario.status,
                    'created_at': scenario.created_at.isoformat()
                }
            
            elif export_format == 'csv':
                response.content_type = 'text/csv'
                response.headers['Content-Disposition'] = f'attachment; filename="scenario-{scenario_id}.csv"'
                
                # Create CSV output
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(['Field', 'Value'])
                
                # Write data
                writer.writerow(['Scenario ID', scenario.id])
                writer.writerow(['Name', scenario.name])
                writer.writerow(['Description', scenario.description])
                writer.writerow(['Status', scenario.status])
                writer.writerow(['Created At', scenario.created_at.isoformat()])
                
                return output.getvalue()
            
            else:
                raise ValidationError(f"Unknown export format: {export_format}")
            
        except ValidationError as e:
            response.status = 400 if "Unknown" in str(e) else 404
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to export scenario: {str(e)}")
            response.status = 500
            return {'error': 'Failed to export scenario'}
    
    @app.post('/api/v1/scenarios/<scenario_id>/replay')
    def replay_scenario(scenario_id: str):
        """
        Replay a scenario with identical parameters.
        
        Returns:
        {
            "scenario_id": "scenario-001",
            "replay_id": "replay-001",
            "status": "running"
        }
        """
        try:
            session = get_session()
            scenario = session.query(Scenario).filter_by(id=scenario_id).first()
            
            if not scenario:
                raise ValidationError(f"Scenario not found: {scenario_id}")
            
            # Replay scenario with identical parameters
            replay_result = scenario_engine.replay_scenario(scenario_id)
            
            return {
                'scenario_id': scenario_id,
                'replay_id': replay_result.get('replay_id'),
                'status': replay_result.get('status'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ValidationError as e:
            response.status = 404
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to replay scenario: {str(e)}")
            response.status = 500
            return {'error': 'Failed to replay scenario'}
    
    @app.delete('/api/v1/scenarios/<scenario_id>')
    def delete_scenario(scenario_id: str):
        """
        Delete a scenario.
        """
        try:
            session = get_session()
            scenario = session.query(Scenario).filter_by(id=scenario_id).first()
            
            if not scenario:
                raise ValidationError(f"Scenario not found: {scenario_id}")
            
            session.delete(scenario)
            session.commit()
            
            return {
                'scenario_id': scenario_id,
                'status': 'deleted',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ValidationError as e:
            response.status = 404
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to delete scenario: {str(e)}")
            response.status = 500
            return {'error': 'Failed to delete scenario'}
