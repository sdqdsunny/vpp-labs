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

logger = logging.getLogger(__name__)


def create_protocol_analyzer_routes(app: Bottle) -> None:
    """Create and register protocol analyzer routes"""
    
    @app.route("/api/analyzer/summary", method="GET")
    def get_summary():
        """Get analysis summary"""
        try:
            analyzer = get_analyzer()
            summary = analyzer.get_summary()
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
            analyzer = get_analyzer()
            stats = analyzer.get_protocol_stats()
            
            # Convert to dict for JSON serialization
            stats_list = [
                {
                    'protocol': s.protocol,
                    'packet_count': s.packet_count,
                    'total_bytes': s.total_bytes,
                    'avg_packet_size': s.avg_packet_size,
                    'packets_per_second': s.packets_per_second,
                    'last_seen': s.last_seen,
                    'error_count': s.error_count
                }
                for s in stats
            ]
            
            response.content_type = "application/json"
            return json.dumps(stats_list)
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
            
            analyzer = get_analyzer()
            packets = analyzer.get_recent_packets(limit=limit, protocol=protocol)
            
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
            
            analyzer = get_analyzer()
            flows = analyzer.get_flows(limit=limit)
            
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
            analyzer = get_analyzer()
            analyzer.reset()
            
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
    
    logger.info("Protocol Analyzer routes registered")
