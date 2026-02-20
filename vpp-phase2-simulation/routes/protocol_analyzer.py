"""
Protocol Analyzer API Routes

Provides REST API endpoints for protocol traffic analysis
"""

import json
import logging
from bottle import Bottle, request, response
from datetime import datetime

from services.protocol_analyzer import (
    get_analyzer, PacketInfo, ProtocolType
)
from services.vpp_realtime_data_provider import get_vpp_data_provider
from services.vpp_data_store import get_vpp_data_store
from services.protocol_traffic_generator import get_protocol_traffic_generator

logger = logging.getLogger(__name__)


def create_protocol_analyzer_routes(app: Bottle) -> None:
    """Create and register protocol analyzer routes"""
    
    @app.route("/api/analyzer/summary", method="GET")
    def get_summary():
        """Get analysis summary"""
        try:
            generator = get_protocol_traffic_generator()
            summary = generator.get_summary()
            response.content_type = "application/json"
            return json.dumps(summary)
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            response.status = 500
            return json.dumps({"error": str(e)})
    
    @app.route("/api/analyzer/stats", method="GET")
    def get_stats():
        """Get protocol statistics"""
        try:
            generator = get_protocol_traffic_generator()
            stats = generator.get_stats()
            
            response.content_type = "application/json"
            return json.dumps(stats)
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            response.status = 500
            return json.dumps({"error": str(e)})
    
    @app.route("/api/analyzer/packets", method="GET")
    def get_packets():
        """Get recent packets"""
        try:
            limit = int(request.query.get("limit", 100))
            protocol = request.query.get("protocol", None)
            
            generator = get_protocol_traffic_generator()
            packets = generator.get_packets(limit=limit, protocol=protocol)
            
            response.content_type = "application/json"
            return json.dumps(packets)
        except Exception as e:
            logger.error(f"Error getting packets: {e}")
            response.status = 500
            return json.dumps({"error": str(e)})
    
    @app.route("/api/analyzer/flows", method="GET")
    def get_flows():
        """Get active flows"""
        try:
            limit = int(request.query.get("limit", 50))
            
            generator = get_protocol_traffic_generator()
            flows = generator.get_flows(limit=limit)
            
            response.content_type = "application/json"
            return json.dumps(flows)
        except Exception as e:
            logger.error(f"Error getting flows: {e}")
            response.status = 500
            return json.dumps({"error": str(e)})
    
    @app.route("/api/analyzer/packet", method="POST")
    def add_packet():
        """Add a packet to analysis"""
        try:
            data = request.json
            
            packet = PacketInfo(
                timestamp=data.get('timestamp', datetime.now().isoformat()),
                protocol=data.get('protocol', 'Unknown'),
                src_ip=data.get('src_ip', '0.0.0.0'),
                dst_ip=data.get('dst_ip', '0.0.0.0'),
                src_port=int(data.get('src_port', 0)),
                dst_port=int(data.get('dst_port', 0)),
                size=int(data.get('size', 0)),
                payload_preview=data.get('payload_preview', ''),
                direction=data.get('direction', 'unknown')
            )
            
            analyzer = get_analyzer()
            analyzer.add_packet(packet)
            
            response.content_type = "application/json"
            return json.dumps({"status": "success"})
        except Exception as e:
            logger.error(f"Error adding packet: {e}")
            response.status = 400
            return json.dumps({"error": str(e)})
    
    @app.route("/api/analyzer/reset", method="POST")
    def reset_analyzer():
        """Reset analyzer statistics"""
        try:
            generator = get_protocol_traffic_generator()
            generator.reset()
            
            response.content_type = "application/json"
            return json.dumps({"status": "reset_complete"})
        except Exception as e:
            logger.error(f"Error resetting analyzer: {e}")
            response.status = 500
            return json.dumps({"error": str(e)})
    
    @app.route("/api/analyzer/protocols", method="GET")
    def get_supported_protocols():
        """Get list of supported protocols"""
        try:
            protocols = [p.value for p in ProtocolType]
            response.content_type = "application/json"
            return json.dumps({"protocols": protocols})
        except Exception as e:
            logger.error(f"Error getting protocols: {e}")
            response.status = 500
            return json.dumps({"error": str(e)})
    
    @app.route("/api/analyzer/status", method="GET")
    def get_analyzer_status():
        """Get analyzer status and memory usage"""
        try:
            generator = get_protocol_traffic_generator()
            status = generator.get_status()
            response.content_type = "application/json"
            return json.dumps(status, default=str)
        except Exception as e:
            logger.error(f"Error getting analyzer status: {e}")
            response.status = 500
            return json.dumps({"error": str(e)})
    
    @app.route("/api/vpp/realtime", method="GET")
    def get_vpp_realtime_data():
        """Get real-time VPP data exchange information"""
        try:
            logger.info("DEBUG: /api/vpp/realtime endpoint called from protocol_analyzer")
            store = get_vpp_data_store()
            all_data = store.get_all_data()
            
            logger.info(f"DEBUG: Retrieved data from store: {list(all_data.keys())}")
            
            # 计算能量平衡
            power_data = all_data['power_generation']
            storage_data = all_data['storage']
            demand_data = all_data['demand']
            
            total_supply = power_data.get('current_power', 0) + storage_data.get('current_power', 0)
            total_demand = demand_data.get('current_demand', 0)
            balance = total_supply - total_demand
            
            # 确定平衡状态
            if abs(balance) < 5:
                status = 'balanced'
            elif balance > 0:
                status = 'surplus'
            else:
                status = 'deficit'
            
            response_data = {
                'timestamp': all_data['timestamp'],
                'power_generation': power_data,
                'storage': storage_data,
                'demand': demand_data,
                'coordinator': all_data['coordinator'],
                'energy_balance': {
                    'total_supply': round(total_supply, 2),
                    'demand': round(total_demand, 2),
                    'balance': round(balance, 2),
                    'status': status
                },
                'system_status': {
                    'power_status': power_data.get('device_status', 'unknown'),
                    'storage_status': storage_data.get('charge_status', 'unknown'),
                    'demand_status': demand_data.get('dr_status', 'unknown'),
                    'overall_status': 'operational' if status != 'deficit' else 'warning'
                },
                '_debug': 'protocol_analyzer endpoint'
            }
            
            response.content_type = "application/json"
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return json.dumps(response_data, default=str)
        except Exception as e:
            logger.error(f"Error getting VPP realtime data: {e}")
            response.status = 500
            return json.dumps({"error": str(e)})
    
    @app.route("/api/vpp/power", method="GET")
    def get_vpp_power_data():
        """Get power generation data"""
        try:
            store = get_vpp_data_store()
            data = store.get_power_data()
            response.content_type = "application/json"
            return json.dumps(data, default=str)
        except Exception as e:
            logger.error(f"Error getting power data: {e}")
            response.status = 500
            return json.dumps({"error": str(e)})
    
    @app.route("/api/vpp/storage", method="GET")
    def get_vpp_storage_data():
        """Get storage data"""
        try:
            store = get_vpp_data_store()
            data = store.get_storage_data()
            response.content_type = "application/json"
            return json.dumps(data, default=str)
        except Exception as e:
            logger.error(f"Error getting storage data: {e}")
            response.status = 500
            return json.dumps({"error": str(e)})
    
    @app.route("/api/vpp/demand", method="GET")
    def get_vpp_demand_data():
        """Get demand data"""
        try:
            store = get_vpp_data_store()
            data = store.get_demand_data()
            response.content_type = "application/json"
            return json.dumps(data, default=str)
        except Exception as e:
            logger.error(f"Error getting demand data: {e}")
            response.status = 500
            return json.dumps({"error": str(e)})
    
    @app.route("/api/vpp/energy-balance", method="GET")
    def get_vpp_energy_balance():
        """Get energy balance information"""
        try:
            store = get_vpp_data_store()
            all_data = store.get_all_data()
            
            power_data = all_data['power_generation']
            storage_data = all_data['storage']
            demand_data = all_data['demand']
            
            total_supply = power_data.get('current_power', 0) + storage_data.get('current_power', 0)
            total_demand = demand_data.get('current_demand', 0)
            balance = total_supply - total_demand
            
            if abs(balance) < 5:
                status = 'balanced'
            elif balance > 0:
                status = 'surplus'
            else:
                status = 'deficit'
            
            response_data = {
                'total_supply': round(total_supply, 2),
                'demand': round(total_demand, 2),
                'balance': round(balance, 2),
                'status': status
            }
            
            response.content_type = "application/json"
            return json.dumps(response_data, default=str)
        except Exception as e:
            logger.error(f"Error getting energy balance: {e}")
            response.status = 500
            return json.dumps({"error": str(e)})
    
    logger.info("Protocol Analyzer routes registered")
