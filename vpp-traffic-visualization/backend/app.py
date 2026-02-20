"""
VPP Traffic Visualization Engine - Flask Application Entry Point

This is the main Flask application that serves as the backend for the
VPP traffic visualization engine. It handles WebSocket connections,
REST API endpoints, and traffic collection/transformation.
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.websocket_broadcaster import WebSocketBroadcaster
from routes.websocket_routes import WebSocketRoutes
from routes.rest_api_routes import RestAPIRoutes
from services.traffic_collector import TrafficCollectorService
from services.event_generator import EventGenerator
from services.vpp_data_connector import VPPDataConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__, 
            template_folder='../frontend',
            static_folder='../frontend')

# Configure Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize services
broadcaster = WebSocketBroadcaster()
ws_routes = WebSocketRoutes(socketio, broadcaster)
traffic_collector = TrafficCollectorService()
event_generator = EventGenerator()
rest_api_routes = RestAPIRoutes(traffic_collector, event_generator)

# Initialize VPP data connector
vpp_connector = VPPDataConnector()

# Global variable to track if VPP data fetching is running
vpp_fetch_thread = None


@app.route('/')
def index():
    """Serve the main dashboard page"""
    return render_template('index.html')


@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'VPP Traffic Visualization Engine'
    })


@app.route('/api/visualization/components')
def get_components():
    """Get VPP system components information"""
    return jsonify(rest_api_routes.get_components())


@app.route('/api/visualization/statistics')
def get_statistics():
    """Get traffic visualization statistics"""
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    return jsonify(rest_api_routes.get_statistics(start_time, end_time))


@app.route('/api/vpp/status')
def get_vpp_status():
    """Get VPP connector status"""
    return jsonify(vpp_connector.get_connection_status())


def push_vpp_data_to_clients():
    """Background task to push VPP data to connected clients"""
    import threading
    
    def fetch_and_push():
        while True:
            try:
                # Fetch real-time data from VPP
                realtime_data = vpp_connector.fetch_realtime_data()
                if realtime_data:
                    # Convert to visualization events
                    events = vpp_connector.convert_realtime_to_events(realtime_data)
                    
                    # Broadcast events to all connected clients
                    for event in events:
                        socketio.emit('traffic_event', {
                            'from': event.from_component,
                            'to': event.to_component,
                            'type': event.traffic_type,
                            'intensity': event.intensity,
                            'packet_size': event.packet_size,
                            'timestamp': event.timestamp.isoformat()
                        }, namespace='/', skip_sid=None)
                
                # Also fetch and convert packet data
                packets = vpp_connector.fetch_packets(limit=50)
                if packets:
                    events = vpp_connector.convert_packets_to_events(packets)
                    for event in events:
                        socketio.emit('traffic_event', {
                            'from': event.from_component,
                            'to': event.to_component,
                            'type': event.traffic_type,
                            'intensity': event.intensity,
                            'packet_size': event.packet_size,
                            'timestamp': event.timestamp.isoformat()
                        }, namespace='/', skip_sid=None)
                
                # Sleep before next push
                import time
                time.sleep(1)
            
            except Exception as e:
                logger.error(f"Error pushing VPP data: {e}")
                import time
                time.sleep(2)
    
    thread = threading.Thread(target=fetch_and_push, daemon=True)
    thread.start()
    return thread


if __name__ == '__main__':
    logger.info('Starting VPP Traffic Visualization Engine...')
    
    # Try to connect to VPP
    if vpp_connector.connect():
        logger.info('Connected to VPP system')
        # Start pushing VPP data to clients
        vpp_fetch_thread = push_vpp_data_to_clients()
    else:
        logger.warning('Could not connect to VPP system - visualization will not show real-time data')
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
