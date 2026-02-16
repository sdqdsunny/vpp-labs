"""
Event Emitter Tests

Tests for event emission and subscription functionality.
"""

import pytest
from services.event_emitter import EventEmitter, get_event_emitter
from services.dispatch_engine import DispatchEngine
from models.device import Device
from utils.validators import DispatchRequest


class TestEventEmitter:
    """Test EventEmitter class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.emitter = EventEmitter()
        self.events_received = []
    
    def callback(self, data):
        """Test callback function"""
        self.events_received.append(data)
    
    def test_subscribe_to_event(self):
        """Test subscribing to an event"""
        self.emitter.subscribe("test.event", self.callback)
        assert "test.event" in self.emitter._listeners
        assert self.callback in self.emitter._listeners["test.event"]
    
    def test_emit_event_to_subscribers(self):
        """Test emitting event to subscribers"""
        self.emitter.subscribe("test.event", self.callback)
        
        test_data = {"key": "value"}
        self.emitter.emit("test.event", test_data)
        
        assert len(self.events_received) == 1
        assert self.events_received[0] == test_data
    
    def test_emit_event_without_subscribers(self):
        """Test emitting event without subscribers"""
        test_data = {"key": "value"}
        # Should not raise exception
        self.emitter.emit("test.event", test_data)
        assert len(self.events_received) == 0
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event"""
        events_received_2 = []
        
        def callback2(data):
            events_received_2.append(data)
        
        self.emitter.subscribe("test.event", self.callback)
        self.emitter.subscribe("test.event", callback2)
        
        test_data = {"key": "value"}
        self.emitter.emit("test.event", test_data)
        
        assert len(self.events_received) == 1
        assert len(events_received_2) == 1
        assert self.events_received[0] == test_data
        assert events_received_2[0] == test_data
    
    def test_unsubscribe_from_event(self):
        """Test unsubscribing from an event"""
        self.emitter.subscribe("test.event", self.callback)
        self.emitter.unsubscribe("test.event", self.callback)
        
        test_data = {"key": "value"}
        self.emitter.emit("test.event", test_data)
        
        assert len(self.events_received) == 0
    
    def test_unsubscribe_nonexistent_callback(self):
        """Test unsubscribing callback that doesn't exist"""
        def other_callback(data):
            pass
        
        # Should not raise exception
        self.emitter.unsubscribe("test.event", other_callback)
    
    def test_event_history_recording(self):
        """Test event history is recorded"""
        test_data = {"key": "value"}
        self.emitter.emit("test.event", test_data)
        
        history = self.emitter.get_event_history()
        assert len(history) == 1
        assert history[0]["event_type"] == "test.event"
        assert history[0]["data"] == test_data
        assert "timestamp" in history[0]
    
    def test_event_history_filtering(self):
        """Test filtering event history by event type"""
        self.emitter.emit("event.type1", {"data": 1})
        self.emitter.emit("event.type2", {"data": 2})
        self.emitter.emit("event.type1", {"data": 3})
        
        history = self.emitter.get_event_history("event.type1")
        assert len(history) == 2
        assert all(e["event_type"] == "event.type1" for e in history)
    
    def test_clear_event_history(self):
        """Test clearing event history"""
        self.emitter.emit("test.event", {"data": 1})
        self.emitter.emit("test.event", {"data": 2})
        
        assert len(self.emitter.get_event_history()) == 2
        
        self.emitter.clear_history()
        assert len(self.emitter.get_event_history()) == 0
    
    def test_event_constants(self):
        """Test event type constants are defined"""
        assert EventEmitter.DISPATCH_CREATED == "dispatch.created"
        assert EventEmitter.DISPATCH_COMPLETED == "dispatch.completed"
        assert EventEmitter.DISPATCH_FAILED == "dispatch.failed"
        assert EventEmitter.DEVICE_REGISTERED == "device.registered"
        assert EventEmitter.DEVICE_STATUS_CHANGED == "device.status_changed"
    
    def test_callback_exception_handling(self):
        """Test that callback exceptions don't break event emission"""
        def failing_callback(data):
            raise ValueError("Test error")
        
        self.emitter.subscribe("test.event", failing_callback)
        self.emitter.subscribe("test.event", self.callback)
        
        test_data = {"key": "value"}
        # Should not raise exception
        self.emitter.emit("test.event", test_data)
        
        # Second callback should still be called
        assert len(self.events_received) == 1
        assert self.events_received[0] == test_data
    
    def test_get_global_event_emitter(self):
        """Test getting global event emitter instance"""
        emitter1 = get_event_emitter()
        emitter2 = get_event_emitter()
        
        # Should return same instance
        assert emitter1 is emitter2
    
    def test_global_event_emitter_functionality(self):
        """Test global event emitter works correctly"""
        emitter = get_event_emitter()
        events = []
        
        def callback(data):
            events.append(data)
        
        emitter.subscribe("global.event", callback)
        emitter.emit("global.event", {"test": "data"})
        
        assert len(events) == 1
        assert events[0] == {"test": "data"}


class TestDispatchEventEmission:
    """Test dispatch event emission"""
    
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        """Setup test fixtures"""
        self.session = db_session
        self.engine = DispatchEngine()
        self.events_received = []
        
        # Create test device
        self.device = Device(
            id="device-1",
            device_type="solar",
            location="Site A",
            status="online",
            capabilities={"power_range": [0, 1000]},
            configuration={"power_limit": 500}
        )
        self.session.add(self.device)
        self.session.commit()
        
        # Subscribe to events
        self.engine.event_emitter.subscribe(
            EventEmitter.DISPATCH_CREATED,
            self.on_dispatch_created
        )
        self.engine.event_emitter.subscribe(
            EventEmitter.DISPATCH_COMPLETED,
            self.on_dispatch_completed
        )
        self.engine.event_emitter.subscribe(
            EventEmitter.DISPATCH_FAILED,
            self.on_dispatch_failed
        )
    
    def on_dispatch_created(self, data):
        """Callback for dispatch.created event"""
        self.events_received.append(("created", data))
    
    def on_dispatch_completed(self, data):
        """Callback for dispatch.completed event"""
        self.events_received.append(("completed", data))
    
    def on_dispatch_failed(self, data):
        """Callback for dispatch.failed event"""
        self.events_received.append(("failed", data))
    
    def test_dispatch_created_event_emitted(self):
        """Test dispatch.created event is emitted when dispatch is created"""
        dispatch_data = DispatchRequest(
            device_id="device-1",
            command_type="power_adjust",
            target_value=100.0,
            priority_level=1
        )
        
        dispatch = self.engine.create_dispatch(dispatch_data)
        
        # Check event was emitted
        assert len(self.events_received) == 1
        event_type, event_data = self.events_received[0]
        assert event_type == "created"
        assert event_data["dispatch_id"] == dispatch.id
        assert event_data["device_id"] == "device-1"
        assert event_data["command_type"] == "power_adjust"
        assert event_data["target_value"] == 100.0
        assert event_data["status"] == "pending"
    
    def test_dispatch_created_event_contains_all_fields(self):
        """Test dispatch.created event contains all required fields"""
        dispatch_data = DispatchRequest(
            device_id="device-1",
            command_type="mode_change",
            target_value=50.0,
            priority_level=2
        )
        
        dispatch = self.engine.create_dispatch(dispatch_data)
        
        event_type, event_data = self.events_received[0]
        assert "dispatch_id" in event_data
        assert "device_id" in event_data
        assert "command_type" in event_data
        assert "target_value" in event_data
        assert "priority_level" in event_data
        assert "status" in event_data
        assert "created_at" in event_data
    
    def test_dispatch_completed_event_emitted(self):
        """Test dispatch.completed event is emitted when dispatch completes"""
        dispatch_data = DispatchRequest(
            device_id="device-1",
            command_type="power_adjust",
            target_value=100.0,
            priority_level=1
        )
        
        dispatch = self.engine.create_dispatch(dispatch_data)
        self.events_received.clear()
        
        # Execute dispatch
        self.engine.execute_dispatch(dispatch.id)
        
        # Check completed event was emitted
        completed_events = [e for e in self.events_received if e[0] == "completed"]
        assert len(completed_events) == 1
        event_type, event_data = completed_events[0]
        assert event_data["dispatch_id"] == dispatch.id
        assert event_data["status"] == "completed"
        assert "completed_at" in event_data
    
    def test_dispatch_completed_event_contains_all_fields(self):
        """Test dispatch.completed event contains all required fields"""
        dispatch_data = DispatchRequest(
            device_id="device-1",
            command_type="power_adjust",
            target_value=100.0,
            priority_level=1
        )
        
        dispatch = self.engine.create_dispatch(dispatch_data)
        self.events_received.clear()
        
        self.engine.execute_dispatch(dispatch.id)
        
        completed_events = [e for e in self.events_received if e[0] == "completed"]
        event_type, event_data = completed_events[0]
        assert "dispatch_id" in event_data
        assert "device_id" in event_data
        assert "command_type" in event_data
        assert "status" in event_data
        assert "execution_time" in event_data
        assert "completed_at" in event_data
    
    def test_event_history_records_all_events(self):
        """Test event history records all emitted events"""
        dispatch_data = DispatchRequest(
            device_id="device-1",
            command_type="power_adjust",
            target_value=100.0,
            priority_level=1
        )
        
        dispatch = self.engine.create_dispatch(dispatch_data)
        self.engine.execute_dispatch(dispatch.id)
        
        # Check event history
        history = self.engine.event_emitter.get_event_history()
        assert len(history) >= 2
        
        # Check event types
        event_types = [e["event_type"] for e in history]
        assert EventEmitter.DISPATCH_CREATED in event_types
        assert EventEmitter.DISPATCH_COMPLETED in event_types
    
    def test_event_history_filtering_by_type(self):
        """Test filtering event history by event type"""
        dispatch_data = DispatchRequest(
            device_id="device-1",
            command_type="power_adjust",
            target_value=100.0,
            priority_level=1
        )
        
        dispatch = self.engine.create_dispatch(dispatch_data)
        self.engine.execute_dispatch(dispatch.id)
        
        # Filter by event type
        created_events = self.engine.event_emitter.get_event_history(
            EventEmitter.DISPATCH_CREATED
        )
        assert len(created_events) >= 1
        assert all(e["event_type"] == EventEmitter.DISPATCH_CREATED for e in created_events)
    
    def test_multiple_dispatches_emit_separate_events(self):
        """Test multiple dispatches emit separate events"""
        # Create second device
        device2 = Device(
            id="device-2",
            device_type="wind",
            location="Site B",
            status="online",
            capabilities={"power_range": [0, 2000]},
            configuration={"power_limit": 1000}
        )
        self.session.add(device2)
        self.session.commit()
        
        self.events_received.clear()
        
        # Create two dispatches
        dispatch_data1 = DispatchRequest(
            device_id="device-1",
            command_type="power_adjust",
            target_value=100.0,
            priority_level=1
        )
        dispatch_data2 = DispatchRequest(
            device_id="device-2",
            command_type="power_adjust",
            target_value=200.0,
            priority_level=1
        )
        
        dispatch1 = self.engine.create_dispatch(dispatch_data1)
        dispatch2 = self.engine.create_dispatch(dispatch_data2)
        
        # Check two created events
        created_events = [e for e in self.events_received if e[0] == "created"]
        assert len(created_events) == 2
        
        dispatch_ids = [e[1]["dispatch_id"] for e in created_events]
        assert dispatch1.id in dispatch_ids
        assert dispatch2.id in dispatch_ids
    
    def test_event_timestamp_is_recorded(self):
        """Test event timestamp is recorded in history"""
        dispatch_data = DispatchRequest(
            device_id="device-1",
            command_type="power_adjust",
            target_value=100.0,
            priority_level=1
        )
        
        dispatch = self.engine.create_dispatch(dispatch_data)
        
        history = self.engine.event_emitter.get_event_history(
            EventEmitter.DISPATCH_CREATED
        )
        assert len(history) >= 1
        
        event = history[0]
        assert "timestamp" in event
        # Verify timestamp is ISO format
        assert "T" in event["timestamp"]
