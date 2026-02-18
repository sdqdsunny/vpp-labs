"""
Security Testing API Routes

Provides REST API endpoints for security testing tools
"""

import json
import logging
from bottle import Bottle, request, response

from services.security_tester import get_security_manager

logger = logging.getLogger(__name__)


def create_security_tester_routes(app: Bottle) -> None:
    """Create and register security tester routes"""
    
    @app.route("/api/security/tools", method="GET")
    def get_available_tools():
        """Get available security testing tools"""
        try:
            manager = get_security_manager()
            tools = manager.get_available_tools()
            
            response.content_type = "application/json"
            return json.dumps({
                "tools": tools,
                "timestamp": __import__('datetime').datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting tools: {e}")
            response.status = 500
            return json.dumps({"error": str(e)})
    
    @app.route("/api/security/modbus/test", method="POST")
    def modbus_test():
        """Run Modbus security test"""
        try:
            data = request.json
            test_type = data.get("test_type", "scan")
            host = data.get("host", "localhost")
            port = int(data.get("port", 502))
            
            manager = get_security_manager()
            result = manager.run_modbus_test(test_type, host, port, **data)
            
            response.content_type = "application/json"
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Modbus test error: {e}")
            response.status = 400
            return json.dumps({"error": str(e)})
    
    @app.route("/api/security/dnp3/test", method="POST")
    def dnp3_test():
        """Run DNP3 security test"""
        try:
            data = request.json
            test_type = data.get("test_type", "connection")
            host = data.get("host", "localhost")
            port = int(data.get("port", 20000))
            
            manager = get_security_manager()
            result = manager.run_dnp3_test(test_type, host, port, **data)
            
            response.content_type = "application/json"
            return json.dumps(result)
        except Exception as e:
            logger.error(f"DNP3 test error: {e}")
            response.status = 400
            return json.dumps({"error": str(e)})
    
    @app.route("/api/security/opcua/test", method="POST")
    def opcua_test():
        """Run OPC UA security test"""
        try:
            data = request.json
            test_type = data.get("test_type", "connection")
            url = data.get("url", "opc.tcp://localhost:4840")
            
            manager = get_security_manager()
            result = manager.run_opcua_test(test_type, url, **data)
            
            response.content_type = "application/json"
            return json.dumps(result)
        except Exception as e:
            logger.error(f"OPC UA test error: {e}")
            response.status = 400
            return json.dumps({"error": str(e)})
    
    @app.route("/api/security/can/test", method="POST")
    def can_test():
        """Run CAN security test"""
        try:
            data = request.json
            test_type = data.get("test_type", "status")
            interface = data.get("interface", "can0")
            
            manager = get_security_manager()
            result = manager.run_can_test(test_type, interface, **data)
            
            response.content_type = "application/json"
            return json.dumps(result)
        except Exception as e:
            logger.error(f"CAN test error: {e}")
            response.status = 400
            return json.dumps({"error": str(e)})
    
    @app.route("/api/security/boofuzz/test", method="POST")
    def boofuzz_test():
        """Run Boofuzz fuzzing test"""
        try:
            data = request.json
            test_type = data.get("test_type", "modbus_fuzz")
            host = data.get("host", "localhost")
            port = int(data.get("port", 502))
            
            manager = get_security_manager()
            result = manager.run_boofuzz_test(test_type, host, port, **data)
            
            response.content_type = "application/json"
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Boofuzz test error: {e}")
            response.status = 400
            return json.dumps({"error": str(e)})
    
    logger.info("Security Tester routes registered")
