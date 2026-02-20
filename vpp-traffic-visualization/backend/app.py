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


if __name__ == '__main__':
    logger.info('Starting VPP Traffic Visualization Engine...')
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
