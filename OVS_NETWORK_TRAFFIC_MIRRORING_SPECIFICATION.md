# OVS网络流量镜像实现规范

**版本**: 1.0  
**日期**: 2026年2月17日  
**状态**: 设计阶段

---

## 1. 概述

本文档定义了基于Open vSwitch (OVS)的VPP系统网络流量镜像架构，用于在虚拟交换机上实现流量采集和工控协议分析。

### 1.1 目标

- 在OVS虚拟交换机上实现无损流量镜像
- 支持多个业务端口的流量采集
- 为工控协议分析工具提供实时流量
- 保证业务流量不受影响
- 提供可观测性和监控能力

### 1.2 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    OVS虚拟交换机 (br-vpp)                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 业务端口 (veth-pair)                                 │   │
│  │ ├─ veth-master (主站 CPP)                            │   │
│  │ ├─ veth-vcc (VCC协调器)                              │   │
│  │ ├─ veth-upf (5G UPF)                                 │   │
│  │ └─ veth-gen (电源/储能/需求侧)                       │   │
│  │                                                      │   │
│  │ 采集端口 (Mirror)                                    │   │
│  │ └─ mirror-port (镜像目的端口)                        │   │
│  │                                                      │   │
│  │ 分析端口 (veth-pair)                                 │   │
│  │ └─ veth-analyzer (协议分析工具)                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 网络拓扑设计

### 2.1 端口定义

| 端口名称 | 类型 | 功能 | 容器 | IP地址 |
|---------|------|------|------|--------|
| veth-master | veth-pair | 主站通信 | vpp-master | 10.0.1.10 |
| veth-vcc | veth-pair | VCC协调 | vpp-vcc | 10.0.1.20 |
| veth-upf | veth-pair | 5G传输 | vpp-upf | 10.0.1.30 |
| veth-gen | veth-pair | 设备模拟 | vpp-gen | 10.0.1.40 |
| mirror-port | internal | 镜像目的 | OVS host | N/A |
| veth-analyzer | veth-pair | 流量分析 | vpp-analyzer | 10.0.1.50 |

### 2.2 流量流向

**业务流量**:
```
主站 (10.0.1.10) ←→ VCC (10.0.1.20) ←→ UPF (10.0.1.30) ←→ 设备 (10.0.1.40)
                          ↓
                    OVS Mirror
                          ↓
                    分析工具 (10.0.1.50)
```

### 2.3 VLAN隔离（可选）

```
VLAN 100: 业务流量 (主站、VCC、UPF、设备)
VLAN 200: 管理流量 (OVS管理、监控)
VLAN 300: 分析流量 (镜像、分析工具)
```

---

## 3. 技术实现

### 3.1 OVS初始化脚本


#### 3.1.1 初始化脚本 (ovs-init.sh)

```bash
#!/bin/bash
set -e

# 配置
BRIDGE_NAME="br-vpp"
SUBNET="10.0.1.0/24"
GATEWAY="10.0.1.1"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 检查OVS是否安装
if ! command -v ovs-vsctl &> /dev/null; then
    log_error "OVS not installed. Please install openvswitch first."
    exit 1
fi

log_info "Starting OVS initialization..."

# 1. 创建OVS Bridge
log_info "Creating OVS bridge: $BRIDGE_NAME"
ovs-vsctl --if-exists del-br $BRIDGE_NAME
ovs-vsctl add-br $BRIDGE_NAME

# 2. 配置Bridge IP地址
log_info "Configuring bridge IP: $GATEWAY"
ip addr add $GATEWAY/24 dev $BRIDGE_NAME 2>/dev/null || true
ip link set $BRIDGE_NAME up

# 3. 创建业务端口 (veth-pair)
create_veth_port() {
    local port_name=$1
    local container_name=$2
    local ip_addr=$3
    
    log_info "Creating veth port: $port_name"
    
    # 创建veth-pair
    ip link add ${port_name} type veth peer name ${port_name}-br 2>/dev/null || true
    
    # 添加到OVS
    ovs-vsctl add-port $BRIDGE_NAME ${port_name}-br
    
    # 启用端口
    ip link set ${port_name} up
    ip link set ${port_name}-br up
    
    # 配置IP地址
    ip addr add ${ip_addr}/24 dev ${port_name} 2>/dev/null || true
}

# 创建所有业务端口
create_veth_port "veth-master" "vpp-master" "10.0.1.10"
create_veth_port "veth-vcc" "vpp-vcc" "10.0.1.20"
create_veth_port "veth-upf" "vpp-upf" "10.0.1.30"
create_veth_port "veth-gen" "vpp-gen" "10.0.1.40"

# 4. 创建Mirror端口
log_info "Creating mirror port"
ovs-vsctl add-port $BRIDGE_NAME mirror-port -- set Interface mirror-port type=internal

# 5. 配置Mirror规则
log_info "Configuring mirror rules"
ovs-vsctl -- --id=@m create Mirror name=m0 \
  select-all=true output-port=mirror-port \
  -- set Bridge $BRIDGE_NAME mirrors=@m

# 6. 创建分析端口
log_info "Creating analyzer veth port"
create_veth_port "veth-analyzer" "vpp-analyzer" "10.0.1.50"

# 7. 启用mirror-port
ip link set mirror-port up
ip addr add 10.0.1.100/24 dev mirror-port 2>/dev/null || true

# 8. 显示配置
log_info "OVS configuration completed"
log_info "Bridge configuration:"
ovs-vsctl show

log_info "Port statistics:"
ovs-ofctl dump-ports $BRIDGE_NAME

log_info "Mirror configuration:"
ovs-vsctl list Mirror

log_info "All ports are ready!"
```

#### 3.1.2 清理脚本 (ovs-cleanup.sh)

```bash
#!/bin/bash
set -e

BRIDGE_NAME="br-vpp"

echo "Cleaning up OVS configuration..."

# 删除Bridge
ovs-vsctl --if-exists del-br $BRIDGE_NAME

# 删除veth-pair
for port in veth-master veth-vcc veth-upf veth-gen veth-analyzer; do
    ip link del $port 2>/dev/null || true
done

echo "OVS cleanup completed"
```

### 3.2 Docker Compose配置

#### 3.2.1 docker-compose.yml

```yaml
version: '3.8'

services:
  # OVS初始化服务
  ovs-init:
    image: ubuntu:22.04
    container_name: vpp-ovs-init
    network_mode: host
    privileged: true
    volumes:
      - ./scripts/ovs-init.sh:/init.sh:ro
      - ./scripts/ovs-cleanup.sh:/cleanup.sh:ro
    command: bash -c "apt-get update && apt-get install -y openvswitch-switch && bash /init.sh"
    environment:
      - BRIDGE_NAME=br-vpp
      - SUBNET=10.0.1.0/24

  # 主站容器
  vpp-master:
    image: vpp-master:latest
    container_name: vpp-master
    networks:
      vpp-net:
        ipv4_address: 10.0.1.10
    environment:
      - LISTEN_ADDR=0.0.0.0:8080
      - LOG_LEVEL=INFO
    ports:
      - "8080:8080"
    volumes:
      - ./logs/master:/var/log/vpp
    depends_on:
      - ovs-init
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # VCC协调器容器
  vpp-vcc:
    image: vpp-vcc:latest
    container_name: vpp-vcc
    networks:
      vpp-net:
        ipv4_address: 10.0.1.20
    environment:
      - MASTER_URL=http://vpp-master:8080
      - LOG_LEVEL=INFO
    volumes:
      - ./logs/vcc:/var/log/vpp
    depends_on:
      - vpp-master
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # 5G UPF容器
  vpp-upf:
    image: vpp-upf:latest
    container_name: vpp-upf
    networks:
      vpp-net:
        ipv4_address: 10.0.1.30
    environment:
      - MASTER_URL=http://vpp-master:8080
      - LOG_LEVEL=INFO
    volumes:
      - ./logs/upf:/var/log/vpp
    depends_on:
      - vpp-master
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8082/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # 设备模拟器容器
  vpp-gen:
    image: vpp-gen:latest
    container_name: vpp-gen
    networks:
      vpp-net:
        ipv4_address: 10.0.1.40
    environment:
      - MASTER_URL=http://vpp-master:8080
      - LOG_LEVEL=INFO
    volumes:
      - ./logs/gen:/var/log/vpp
    depends_on:
      - vpp-master

  # 协议分析工具容器
  vpp-analyzer:
    image: vpp-analyzer:latest
    container_name: vpp-analyzer
    networks:
      vpp-net:
        ipv4_address: 10.0.1.50
    environment:
      - CAPTURE_INTERFACE=veth-analyzer
      - OUTPUT_DIR=/pcap
      - LOG_LEVEL=INFO
    volumes:
      - ./pcap:/pcap
      - ./logs/analyzer:/var/log/vpp
    depends_on:
      - ovs-init
    cap_add:
      - NET_ADMIN
      - NET_RAW

networks:
  vpp-net:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br-docker
    ipam:
      config:
        - subnet: 10.0.1.0/24
          gateway: 10.0.1.1

volumes:
  pcap:
    driver: local
```

### 3.3 协议分析工具实现

#### 3.3.1 分析工具主程序 (analyzer/main.py)

```python
#!/usr/bin/env python3
"""
VPP Protocol Analyzer - 工控协议分析工具

功能:
- 捕获OVS镜像的网络流量
- 识别工控协议 (IEC61850, Modbus, DNP3, MQTT)
- 保存pcap文件
- 生成统计报告
- 提供REST API查询
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import threading
import queue

try:
    from scapy.all import sniff, IP, TCP, UDP, wrpcap, rdpcap
    from scapy.layers.inet import IP
except ImportError:
    print("Error: scapy not installed. Install with: pip install scapy")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProtocolIdentifier:
    """工控协议识别器"""
    
    # 协议端口映射
    PROTOCOL_PORTS = {
        102: 'IEC61850',
        502: 'Modbus',
        20000: 'DNP3',
        1883: 'MQTT',
        8883: 'MQTT-TLS',
    }
    
    @staticmethod
    def identify(packet) -> Optional[str]:
        """识别数据包中的工控协议"""
        try:
            if not packet.haslayer(IP):
                return None
            
            ip_layer = packet[IP]
            
            # TCP协议
            if ip_layer.proto == 6 and packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                dport = tcp_layer.dport
                sport = tcp_layer.sport
                
                # 检查目的端口
                if dport in ProtocolIdentifier.PROTOCOL_PORTS:
                    return ProtocolIdentifier.PROTOCOL_PORTS[dport]
                
                # 检查源端口
                if sport in ProtocolIdentifier.PROTOCOL_PORTS:
                    return ProtocolIdentifier.PROTOCOL_PORTS[sport]
            
            # UDP协议
            elif ip_layer.proto == 17 and packet.haslayer(UDP):
                udp_layer = packet[UDP]
                dport = udp_layer.dport
                sport = udp_layer.sport
                
                if dport in ProtocolIdentifier.PROTOCOL_PORTS:
                    return ProtocolIdentifier.PROTOCOL_PORTS[dport]
                
                if sport in ProtocolIdentifier.PROTOCOL_PORTS:
                    return ProtocolIdentifier.PROTOCOL_PORTS[sport]
            
            return 'Unknown'
        except Exception as e:
            logger.error(f"Error identifying protocol: {e}")
            return None


class PacketAnalyzer:
    """数据包分析器"""
    
    def __init__(self, interface: str, output_dir: str = '/pcap'):
        self.interface = interface
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.packet_count = 0
        self.protocol_stats: Dict[str, int] = {}
        self.flow_stats: Dict[str, int] = {}
        self.packet_queue = queue.Queue(maxsize=1000)
        
        self.current_pcap_file = None
        self.current_pcap_packets = []
        self.pcap_rotation_count = 100  # 每100个包轮转一次
        
        logger.info(f"PacketAnalyzer initialized on interface: {interface}")
    
    def packet_callback(self, packet):
        """处理每个捕获的数据包"""
        try:
            self.packet_count += 1
            
            # 识别协议
            protocol = ProtocolIdentifier.identify(packet)
            
            # 更新统计
            if protocol:
                self.protocol_stats[protocol] = self.protocol_stats.get(protocol, 0) + 1
            
            # 提取流信息
            if packet.haslayer(IP):
                ip_layer = packet[IP]
                flow_key = f"{ip_layer.src}->{ip_layer.dst}"
                self.flow_stats[flow_key] = self.flow_stats.get(flow_key, 0) + 1
            
            # 保存到pcap
            self.current_pcap_packets.append(packet)
            
            # 定期输出统计
            if self.packet_count % 100 == 0:
                self._log_stats()
            
            # 定期轮转pcap文件
            if len(self.current_pcap_packets) >= self.pcap_rotation_count:
                self._save_pcap()
        
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
    
    def _save_pcap(self):
        """保存pcap文件"""
        try:
            if not self.current_pcap_packets:
                return
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.output_dir / f"capture_{timestamp}.pcap"
            
            wrpcap(str(filename), self.current_pcap_packets)
            logger.info(f"Saved {len(self.current_pcap_packets)} packets to {filename}")
            
            self.current_pcap_packets = []
        except Exception as e:
            logger.error(f"Error saving pcap: {e}")
    
    def _log_stats(self):
        """输出统计信息"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'total_packets': self.packet_count,
            'protocol_distribution': self.protocol_stats,
            'top_flows': sorted(
                self.flow_stats.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
        logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
    
    def start_capture(self):
        """开始捕获"""
        logger.info(f"Starting packet capture on {self.interface}...")
        try:
            sniff(
                iface=self.interface,
                prn=self.packet_callback,
                store=False
            )
        except Exception as e:
            logger.error(f"Capture error: {e}")
            raise
    
    def stop_capture(self):
        """停止捕获"""
        logger.info("Stopping packet capture...")
        self._save_pcap()
        logger.info(f"Total packets captured: {self.packet_count}")


def main():
    """主函数"""
    interface = os.getenv('CAPTURE_INTERFACE', 'veth-analyzer')
    output_dir = os.getenv('OUTPUT_DIR', '/pcap')
    
    logger.info(f"VPP Protocol Analyzer starting...")
    logger.info(f"Interface: {interface}")
    logger.info(f"Output directory: {output_dir}")
    
    analyzer = PacketAnalyzer(interface, output_dir)
    
    try:
        analyzer.start_capture()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        analyzer.stop_capture()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
```

---

## 4. 部署步骤

### 4.1 前置条件

```bash
# 检查系统要求
- Linux kernel >= 4.15
- Docker >= 20.10
- Docker Compose >= 1.29
- OVS >= 2.13

# 安装OVS
sudo apt-get update
sudo apt-get install -y openvswitch-switch openvswitch-common

# 启动OVS服务
sudo systemctl start openvswitch-switch
sudo systemctl enable openvswitch-switch
```

### 4.2 部署流程

```bash
# 1. 克隆项目
git clone <repo-url>
cd vpp-network-mirror

# 2. 构建Docker镜像
docker-compose build

# 3. 启动服务
docker-compose up -d

# 4. 验证部署
docker-compose ps
docker exec vpp-ovs-init ovs-vsctl show

# 5. 查看日志
docker-compose logs -f vpp-analyzer
```

### 4.3 验证检查清单

- [ ] OVS bridge创建成功
- [ ] 所有veth-pair端口已创建
- [ ] Mirror规则已配置
- [ ] 所有容器正常运行
- [ ] 分析工具正在捕获流量
- [ ] pcap文件正在生成

---

## 5. 监控和维护

### 5.1 OVS命令参考

```bash
# 查看bridge配置
ovs-vsctl show

# 查看端口统计
ovs-ofctl dump-ports br-vpp

# 查看流表
ovs-ofctl dump-flows br-vpp

# 查看Mirror配置
ovs-vsctl list Mirror

# 实时监控流量
ovs-ofctl snoop br-vpp
```

### 5.2 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 无法创建bridge | OVS未启动 | `systemctl start openvswitch-switch` |
| veth-pair创建失败 | 权限不足 | 使用`sudo`或`privileged: true` |
| 分析工具无法捕获 | 接口名称错误 | 检查`CAPTURE_INTERFACE`环境变量 |
| 流量未镜像 | Mirror规则未生效 | 重新配置Mirror规则 |

---

## 6. 性能优化

### 6.1 OVS性能调优

```bash
# 启用DPDK加速（可选）
ovs-vsctl set Open_vSwitch . other_config:dpdk-init=true

# 配置流表缓存
ovs-vsctl set Open_vSwitch . other_config:flow-limit=200000

# 启用多线程
ovs-vsctl set Open_vSwitch . other_config:n-handler-threads=4
```

### 6.2 分析工具优化

- 使用AF_PACKET加速捕获
- 配置采样率降低负载
- 异步处理数据包
- 定期轮转pcap文件

---

## 7. 安全考虑

### 7.1 网络隔离

- 使用VLAN隔离业务流量
- 限制分析工具的网络访问
- 启用OVS防火墙规则

### 7.2 数据保护

- 加密pcap文件传输
- 限制pcap文件访问权限
- 定期清理旧的pcap文件

---

## 8. 扩展功能

### 8.1 实时分析API

```python
# 提供REST API查询实时统计
GET /api/stats - 获取统计信息
GET /api/protocols - 获取协议分布
GET /api/flows - 获取流量信息
POST /api/export - 导出pcap文件
```

### 8.2 告警系统

- 异常流量检测
- 协议异常告警
- 性能指标告警

---

## 9. 参考资源

- [Open vSwitch官方文档](http://openvswitch.org/)
- [Scapy文档](https://scapy.readthedocs.io/)
- [Docker Compose文档](https://docs.docker.com/compose/)

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-02-17 | 初始版本 |

