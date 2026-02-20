"""
协议流量生成服务

模拟各种工控协议的实时流量数据，用于协议分析器的测试和演示。
"""

import random
import threading
import time
from datetime import datetime
from typing import Dict, List, Any
from enum import Enum

class ProtocolType(Enum):
    """支持的协议类型"""
    IEC61850 = "IEC61850"
    MODBUS = "Modbus"
    DNP3 = "DNP3"
    MQTT = "MQTT"
    OPC_UA = "OPC UA"
    CAN = "CAN"
    RS232 = "RS-232"
    RS485 = "RS-485"
    LORAWAN = "LoRaWAN"
    XMPP = "XMPP"
    DLT = "DL/T"

class PacketInfo:
    """数据包信息"""
    def __init__(self, protocol: str, src_ip: str, dst_ip: str, 
                 src_port: int, dst_port: int, size: int, 
                 direction: str = "upstream"):
        self.timestamp = datetime.now().isoformat()
        self.protocol = protocol
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.src_port = src_port
        self.dst_port = dst_port
        self.size = size
        self.direction = direction
        self.payload_preview = self._generate_payload_preview()
    
    def _generate_payload_preview(self) -> str:
        """生成数据包预览"""
        hex_chars = "0123456789ABCDEF"
        return "".join(random.choice(hex_chars) for _ in range(16))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp,
            'protocol': self.protocol,
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'size': self.size,
            'direction': self.direction,
            'payload_preview': self.payload_preview
        }

class ProtocolTrafficGenerator:
    """协议流量生成器"""
    
    # 配置常量
    MAX_PACKETS_BUFFER = 1000  # 最大缓冲数据包数
    MAX_COUNTER_VALUE = 2**63 - 1  # Python int 最大值（实际上无限制，但这是安全值）
    COUNTER_RESET_THRESHOLD = 2**31  # 当计数器达到此值时重置（约21亿）
    
    def __init__(self):
        self.packets: List[PacketInfo] = []
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        
        # 协议配置
        self.protocols = [p.value for p in ProtocolType]
        self.ip_ranges = [
            ("192.168.1", "192.168.1"),
            ("10.0.0", "10.0.1"),
            ("172.16.0", "172.16.1"),
        ]
        
        # 统计计数器（带溢出保护）
        self.total_packets_generated = 0
        self.total_bytes_generated = 0
        self.generation_start_time = datetime.now()
        self.last_reset_time = datetime.now()
    
    def start(self):
        """启动流量生成"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._generate_traffic, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止流量生成"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _generate_traffic(self):
        """生成流量的主循环"""
        while self.running:
            try:
                # 每次生成 1-5 个数据包
                num_packets = random.randint(1, 5)
                for _ in range(num_packets):
                    packet = self._generate_packet()
                    with self.lock:
                        self.packets.append(packet)
                        # 保持最多 1000 个数据包
                        if len(self.packets) > 1000:
                            self.packets = self.packets[-1000:]
                        
                        # 更新计数器并检查溢出
                        self.total_packets_generated += num_packets
                        self.total_bytes_generated += sum(p.size for p in [packet])
                        self._check_counter_overflow()
                
                # 随机延迟 0.5-2 秒
                time.sleep(random.uniform(0.5, 2))
            except Exception as e:
                print(f"Error generating traffic: {e}")
    
    def _generate_packet(self) -> PacketInfo:
        """生成单个数据包"""
        protocol = random.choice(self.protocols)
        
        # 随机选择 IP 范围
        src_range, dst_range = random.choice(self.ip_ranges)
        src_ip = f"{src_range}.{random.randint(1, 254)}"
        dst_ip = f"{dst_range}.{random.randint(1, 254)}"
        
        # 根据协议生成端口
        src_port = random.randint(1024, 65535)
        dst_port = self._get_protocol_port(protocol)
        
        # 生成数据包大小
        size = random.randint(64, 1500)
        
        # 生成方向
        direction = random.choice(["upstream", "downstream"])
        
        return PacketInfo(
            protocol=protocol,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            size=size,
            direction=direction
        )
    
    def _get_protocol_port(self, protocol: str) -> int:
        """获取协议的默认端口"""
        port_map = {
            "IEC61850": 102,
            "Modbus": 502,
            "DNP3": 20000,
            "MQTT": 1883,
            "OPC UA": 4840,
            "CAN": 29536,
            "RS-232": 9600,
            "RS-485": 9600,
            "LoRaWAN": 1700,
            "XMPP": 5222,
            "DL/T": 645,
        }
        return port_map.get(protocol, random.randint(1024, 65535))
    
    def get_packets(self, limit: int = 100, protocol: str = None) -> List[Dict[str, Any]]:
        """获取数据包列表"""
        with self.lock:
            packets = self.packets[-limit:]
            if protocol:
                packets = [p for p in packets if p.protocol == protocol]
            return [p.to_dict() for p in packets]
    
    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        with self.lock:
            if not self.packets:
                return {
                    'total_packets': 0,
                    'total_bytes': 0,
                    'total_protocols': 0,
                    'total_flows': 0
                }
            
            total_packets = len(self.packets)
            total_bytes = sum(p.size for p in self.packets)
            protocols = set(p.protocol for p in self.packets)
            total_protocols = len(protocols)
            
            # 计算活跃流（源IP+目标IP+协议的组合）
            flows = set()
            for p in self.packets:
                flow_key = f"{p.src_ip}:{p.dst_ip}:{p.protocol}"
                flows.add(flow_key)
            total_flows = len(flows)
            
            return {
                'total_packets': total_packets,
                'total_bytes': total_bytes,
                'total_protocols': total_protocols,
                'total_flows': total_flows
            }
    
    def get_stats(self) -> List[Dict[str, Any]]:
        """获取协议统计"""
        with self.lock:
            if not self.packets:
                return []
            
            # 按协议分组统计
            stats_dict = {}
            for packet in self.packets:
                protocol = packet.protocol
                if protocol not in stats_dict:
                    stats_dict[protocol] = {
                        'protocol': protocol,
                        'packet_count': 0,
                        'total_bytes': 0,
                        'last_seen': None,
                        'error_count': 0
                    }
                
                stats_dict[protocol]['packet_count'] += 1
                stats_dict[protocol]['total_bytes'] += packet.size
                stats_dict[protocol]['last_seen'] = packet.timestamp
            
            # 计算平均包大小和包/秒
            stats_list = []
            for protocol, stat in stats_dict.items():
                avg_size = stat['total_bytes'] // stat['packet_count'] if stat['packet_count'] > 0 else 0
                pps = stat['packet_count'] / 10  # 假设 10 秒的时间窗口
                
                stats_list.append({
                    'protocol': protocol,
                    'packet_count': stat['packet_count'],
                    'total_bytes': stat['total_bytes'],
                    'avg_packet_size': avg_size,
                    'packets_per_second': round(pps, 2),
                    'last_seen': stat['last_seen'],
                    'error_count': stat['error_count']
                })
            
            return sorted(stats_list, key=lambda x: x['packet_count'], reverse=True)
    
    def get_flows(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取流量分析"""
        with self.lock:
            if not self.packets:
                return []
            
            # 按流分组
            flows_dict = {}
            for packet in self.packets:
                flow_key = f"{packet.src_ip}:{packet.dst_ip}:{packet.protocol}"
                if flow_key not in flows_dict:
                    flows_dict[flow_key] = {
                        'source': packet.src_ip,
                        'destination': packet.dst_ip,
                        'protocol': packet.protocol,
                        'packet_count': 0,
                        'total_bytes': 0,
                        'start_time': packet.timestamp,
                        'last_seen': packet.timestamp
                    }
                
                flows_dict[flow_key]['packet_count'] += 1
                flows_dict[flow_key]['total_bytes'] += packet.size
                flows_dict[flow_key]['last_seen'] = packet.timestamp
            
            # 按数据包数排序
            flows_list = sorted(
                flows_dict.values(),
                key=lambda x: x['packet_count'],
                reverse=True
            )[:limit]
            
            return flows_list
    
    def reset(self):
        """重置统计数据"""
        with self.lock:
            self.packets = []
    
    def _check_counter_overflow(self):
        """检查计数器是否接近溢出阈值并重置"""
        if self.total_packets_generated >= self.COUNTER_RESET_THRESHOLD:
            print(f"⚠️  计数器达到阈值 ({self.total_packets_generated}), 执行重置...")
            self.total_packets_generated = 0
            self.total_bytes_generated = 0
            self.last_reset_time = datetime.now()
            print(f"✅ 计数器已重置")
    
    def get_status(self) -> Dict[str, Any]:
        """获取生成器状态和内存使用情况"""
        import psutil
        import os
        
        with self.lock:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            uptime = datetime.now() - self.generation_start_time
            uptime_seconds = uptime.total_seconds()
            
            return {
                'running': self.running,
                'packets_in_buffer': len(self.packets),
                'buffer_capacity': self.MAX_PACKETS_BUFFER,
                'buffer_usage_percent': (len(self.packets) / self.MAX_PACKETS_BUFFER) * 100,
                'total_packets_generated': self.total_packets_generated,
                'total_bytes_generated': self.total_bytes_generated,
                'counter_threshold': self.COUNTER_RESET_THRESHOLD,
                'counter_usage_percent': (self.total_packets_generated / self.COUNTER_RESET_THRESHOLD) * 100,
                'memory_usage_mb': memory_info.rss / (1024 * 1024),
                'uptime_seconds': uptime_seconds,
                'generation_start_time': self.generation_start_time.isoformat(),
                'last_reset_time': self.last_reset_time.isoformat()
            }


# 全局实例
_generator_instance = None

def get_protocol_traffic_generator() -> ProtocolTrafficGenerator:
    """获取或创建协议流量生成器实例"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = ProtocolTrafficGenerator()
        _generator_instance.start()
    return _generator_instance
