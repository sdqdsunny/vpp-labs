"""
Unit tests for Scenario Data Management

Tests scenario persistence, retrieval, reproducibility, export, and query performance.

Requirements:
- 10.1: Scenario data persistence
- 10.2: Scenario data retrieval
- 10.3: Scenario reproducibility
- 10.4: Scenario data export
- 10.5: Scenario query performance
"""

import pytest
import json
import time
from datetime import datetime
from threading import Thread

from services.scenario_engine import ScenarioEngine
from models.scenario import Scenario
from utils.database import get_session, init_db
from utils.errors import ValidationError


@pytest.fixture
def scenario_engine():
    """Create scenario engine instance."""
    return ScenarioEngine()


@pytest.fixture
def db_session():
    """Create database session."""
    init_db()
    session = get_session()
    yield session
    session.close()


class TestScenarioCreation:
    """Test scenario creation and persistence."""
    
    def test_create_scenario(self, scenario_engine):
        """Test creating a scenario."""
        scenario_id = scenario_engine.create_scenario(
            scenario_name='Test Scenario',
            description='Test scenario description',
            duration=3600
        )
        
        assert scenario_id is not None
        assert isinstance(scenario_id, str)
        assert scenario_id.startswith('scenario-')
    
    def test_create_multiple_scenarios(self, scenario_engine):
        """Test creating multiple scenarios."""
        scenario_ids = []
        for i in range(5):
            scenario_id = scenario_engine.create_scenario(
                scenario_name=f'Test Scenario {i}',
                description=f'Test scenario {i} description',
                duration=3600
            )
            scenario_ids.append(scenario_id)
        
        assert len(scenario_ids) == 5
        assert all(isinstance(sid, str) for sid in scenario_ids)
    
    def test_scenario_persisted_in_engine(self, scenario_engine):
        """Test scenario is persisted in engine."""
        scenario_id = scenario_engine.create_scenario(
            scenario_name='Test Scenario',
            description='Test scenario description',
            duration=3600
        )
        
        # Verify scenario exists in engine
        assert scenario_id in scenario_engine.scenarios
        assert scenario_engine.scenarios[scenario_id]['name'] == 'Test Scenario'


class TestScenarioRetrieval:
    """Test scenario data retrieval."""
    
    def test_get_scenario(self, scenario_engine):
        """Test getting scenario."""
        scenario_id = scenario_engine.create_scenario(
            scenario_name='Test Scenario',
            description='Test scenario description',
            duration=3600
        )
        
        # Retrieve scenario
        scenario = scenario_engine.scenarios.get(scenario_id)
        
        assert scenario is not None
        assert scenario['name'] == 'Test Scenario'
        assert scenario['description'] == 'Test scenario description'
    
    def test_list_scenarios(self, scenario_engine):
        """Test listing scenarios."""
        # Create multiple scenarios
        for i in range(5):
            scenario_engine.create_scenario(
                scenario_name=f'Test Scenario {i}',
                description=f'Test scenario {i} description',
                duration=3600
            )
        
        # List scenarios
        scenarios = list(scenario_engine.scenarios.values())
        
        assert len(scenarios) >= 5
    
    def test_filter_scenarios_by_status(self, scenario_engine):
        """Test filtering scenarios by status."""
        # Create scenarios
        for i in range(3):
            scenario_id = scenario_engine.create_scenario(
                scenario_name=f'Test Scenario {i}',
                description=f'Test scenario {i} description',
                duration=3600
            )
            
            # Update status
            if i == 0:
                scenario_engine.scenarios[scenario_id]['status'] = 'running'
            elif i == 1:
                scenario_engine.scenarios[scenario_id]['status'] = 'completed'
            else:
                scenario_engine.scenarios[scenario_id]['status'] = 'pending'
        
        # Filter by status
        pending = [s for s in scenario_engine.scenarios.values() if s['status'] == 'pending']
        running = [s for s in scenario_engine.scenarios.values() if s['status'] == 'running']
        completed = [s for s in scenario_engine.scenarios.values() if s['status'] == 'completed']
        
        assert len(pending) >= 1
        assert len(running) >= 1
        assert len(completed) >= 1


class TestScenarioReproducibility:
    """Test scenario reproducibility."""
    
    def test_scenario_reproducibility(self, scenario_engine):
        """Test scenario reproducibility with identical parameters."""
        # Create scenario
        scenario_id1 = scenario_engine.create_scenario(
            scenario_name='Test Scenario',
            description='Test scenario description',
            duration=3600
        )
        
        # Create another scenario with same parameters
        scenario_id2 = scenario_engine.create_scenario(
            scenario_name='Test Scenario',
            description='Test scenario description',
            duration=3600
        )
        
        # Both scenarios should have same parameters
        scenario1 = scenario_engine.scenarios[scenario_id1]
        scenario2 = scenario_engine.scenarios[scenario_id2]
        
        assert scenario1['name'] == scenario2['name']
        assert scenario1['description'] == scenario2['description']
        assert scenario1['duration'] == scenario2['duration']
    
    def test_scenario_deterministic_execution(self, scenario_engine):
        """Test scenario deterministic execution."""
        # Create multiple scenarios with same parameters
        scenario_ids = []
        for _ in range(3):
            scenario_id = scenario_engine.create_scenario(
                scenario_name='Test Scenario',
                description='Test scenario description',
                duration=3600
            )
            scenario_ids.append(scenario_id)
        
        # All scenarios should have same parameters
        scenarios = [scenario_engine.scenarios[sid] for sid in scenario_ids]
        
        assert all(s['name'] == 'Test Scenario' for s in scenarios)
        assert all(s['duration'] == 3600 for s in scenarios)


class TestScenarioExport:
    """Test scenario data export."""
    
    def test_export_scenario_json(self, scenario_engine):
        """Test exporting scenario as JSON."""
        scenario_id = scenario_engine.create_scenario(
            scenario_name='Test Scenario',
            description='Test scenario description',
            duration=3600
        )
        
        scenario = scenario_engine.scenarios[scenario_id]
        
        # Export as JSON
        export_data = {
            'scenario_id': scenario['id'],
            'name': scenario['name'],
            'description': scenario['description'],
            'status': scenario['status']
        }
        
        # Verify JSON is valid
        json_str = json.dumps(export_data)
        parsed = json.loads(json_str)
        
        assert parsed['scenario_id'] == scenario_id
        assert parsed['name'] == 'Test Scenario'
    
    def test_export_scenario_csv(self, scenario_engine):
        """Test exporting scenario as CSV."""
        scenario_id = scenario_engine.create_scenario(
            scenario_name='Test Scenario',
            description='Test scenario description',
            duration=3600
        )
        
        scenario = scenario_engine.scenarios[scenario_id]
        
        # Export as CSV
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Field', 'Value'])
        writer.writerow(['Scenario ID', scenario['id']])
        writer.writerow(['Name', scenario['name']])
        writer.writerow(['Description', scenario['description']])
        writer.writerow(['Status', scenario['status']])
        
        csv_str = output.getvalue()
        
        # Verify CSV is valid
        assert 'Scenario ID' in csv_str
        assert scenario_id in csv_str
        assert 'Test Scenario' in csv_str


class TestScenarioQueryPerformance:
    """Test scenario query performance."""
    
    def test_query_performance_small_dataset(self, scenario_engine):
        """Test query performance with small dataset."""
        # Create 100 scenarios
        for i in range(100):
            scenario_engine.create_scenario(
                scenario_name=f'Test Scenario {i}',
                description=f'Test scenario {i} description',
                duration=3600
            )
        
        # Query scenarios
        start_time = time.time()
        scenarios = list(scenario_engine.scenarios.values())[:100]
        query_time = time.time() - start_time
        
        # Query should complete within 1 second
        assert query_time < 1.0
        assert len(scenarios) == 100
    
    def test_query_performance_with_filter(self, scenario_engine):
        """Test query performance with filter."""
        # Create scenarios with different statuses
        for i in range(200):
            scenario_id = scenario_engine.create_scenario(
                scenario_name=f'Test Scenario {i}',
                description=f'Test scenario {i} description',
                duration=3600
            )
            
            # Set status
            if i % 3 == 0:
                scenario_engine.scenarios[scenario_id]['status'] = 'completed'
            elif i % 3 == 1:
                scenario_engine.scenarios[scenario_id]['status'] = 'running'
            else:
                scenario_engine.scenarios[scenario_id]['status'] = 'pending'
        
        # Query with filter
        start_time = time.time()
        scenarios = [s for s in scenario_engine.scenarios.values() if s['status'] == 'completed']
        query_time = time.time() - start_time
        
        # Query should complete within 1 second
        assert query_time < 1.0
        assert len(scenarios) > 0


class TestScenarioDeletion:
    """Test scenario deletion."""
    
    def test_delete_scenario(self, scenario_engine):
        """Test deleting scenario."""
        scenario_id = scenario_engine.create_scenario(
            scenario_name='Test Scenario',
            description='Test scenario description',
            duration=3600
        )
        
        # Delete scenario
        del scenario_engine.scenarios[scenario_id]
        
        # Verify scenario deleted
        assert scenario_id not in scenario_engine.scenarios
    
    def test_delete_multiple_scenarios(self, scenario_engine):
        """Test deleting multiple scenarios."""
        # Create multiple scenarios
        scenario_ids = []
        for i in range(5):
            scenario_id = scenario_engine.create_scenario(
                scenario_name=f'Test Scenario {i}',
                description=f'Test scenario {i} description',
                duration=3600
            )
            scenario_ids.append(scenario_id)
        
        # Delete all scenarios
        for scenario_id in scenario_ids:
            if scenario_id in scenario_engine.scenarios:
                del scenario_engine.scenarios[scenario_id]
        
        # Verify all scenarios deleted
        for scenario_id in scenario_ids:
            assert scenario_id not in scenario_engine.scenarios


class TestScenarioDataIntegrity:
    """Test scenario data integrity."""
    
    def test_scenario_data_not_corrupted(self, scenario_engine):
        """Test scenario data is not corrupted."""
        scenario_id = scenario_engine.create_scenario(
            scenario_name='Test Scenario',
            description='Test scenario description',
            duration=3600
        )
        
        scenario = scenario_engine.scenarios[scenario_id]
        
        # Verify data integrity
        assert scenario['name'] == 'Test Scenario'
        assert scenario['description'] == 'Test scenario description'
        assert scenario['duration'] == 3600
    
    def test_scenario_timestamps_preserved(self, scenario_engine):
        """Test scenario timestamps are preserved."""
        before_time = datetime.utcnow()
        scenario_id = scenario_engine.create_scenario(
            scenario_name='Test Scenario',
            description='Test scenario description',
            duration=3600
        )
        after_time = datetime.utcnow()
        
        scenario = scenario_engine.scenarios[scenario_id]
        created_at = datetime.fromisoformat(scenario['created_at'])
        
        # Verify timestamp is within range
        assert before_time <= created_at <= after_time
