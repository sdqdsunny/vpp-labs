# Docker Compose Configuration Guide

**VPP Network Traffic Mirroring System**

---

## Overview

This guide explains the Docker Compose configuration for the complete OVS-based network traffic mirroring system.

## Quick Start

### Prerequisites

- Docker >= 20.10
- Docker Compose >= 1.29
- Linux system with OVS support
- Root/sudo privileges

### Start System

```bash
# Navigate to network-mirror directory
cd network-mirror

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# View logs
docker-compose logs -f
```

### Stop System

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Services Configuration

### 1. OVS Initialization Service (ovs-init)

**Purpose**: Initializes OVS bridge and network infrastructure

**Configuration**:
```yaml
ovs-init:
  image: ubuntu:22.04
  network_mode: host
  privileged: true
  volumes:
    - ./scripts/ovs-init.sh:/init.sh:ro
    - ./scripts/ovs-cleanup.sh:/cleanup.sh:ro
```

**Key Features**:
- Runs in host network mode (required for OVS)
- Privileged mode for network operations
- Installs OVS and initializes bridge
- Creates veth-pair ports for all components
- Configures mirror rule

**Environment Variables**:
- `BRIDGE_NAME`: br-vpp
- `SUBNET`: 10.0.1.0/24
- `GATEWAY`: 10.0.1.1

**Restart Policy**: on-failure:3

### 2. Master Station Service (vpp-master)

**Purpose**: Central control point for VPP system

**Configuration**:
```yaml
vpp-master:
  image: vpp-master:latest
  networks:
    vpp-net:
      ipv4_address: 10.0.1.10
  ports:
    - "8080:8080"
```

**Key Features**:
- Listens on port 8080
- Health check enabled
- Depends on ovs-init
- Logs to ./logs/master

**Environment Variables**:
- `LISTEN_ADDR`: 0.0.0.0:8080
- `LOG_LEVEL`: INFO

**Health Check**:
- Endpoint: http://localhost:8080/health
- Interval: 10s
- Timeout: 5s
- Retries: 3
- Start period: 10s

### 3. VCC Coordinator Service (vpp-vcc)

**Purpose**: Coordinates virtual power plant operations

**Configuration**:
```yaml
vpp-vcc:
  image: vpp-vcc:latest
  networks:
    vpp-net:
      ipv4_address: 10.0.1.20
```

**Key Features**:
- Communicates with master station
- Health check enabled
- Depends on vpp-master
- Logs to ./logs/vcc

**Environment Variables**:
- `MASTER_URL`: http://vpp-master:8080
- `LOG_LEVEL`: INFO

**Health Check**:
- Endpoint: http://localhost:8081/health
- Interval: 10s
- Timeout: 5s
- Retries: 3
- Start period: 10s

### 4. 5G UPF Service (vpp-upf)

**Purpose**: Simulates 5G network transport layer

**Configuration**:
```yaml
vpp-upf:
  image: vpp-upf:latest
  networks:
    vpp-net:
      ipv4_address: 10.0.1.30
```

**Key Features**:
- Simulates 5G UPF functionality
- Health check enabled
- Depends on vpp-master
- Logs to ./logs/upf

**Environment Variables**:
- `MASTER_URL`: http://vpp-master:8080
- `LOG_LEVEL`: INFO

**Health Check**:
- Endpoint: http://localhost:8082/health
- Interval: 10s
- Timeout: 5s
- Retries: 3
- Start period: 10s

### 5. Device Simulator Service (vpp-gen)

**Purpose**: Simulates power generation, storage, and demand devices

**Configuration**:
```yaml
vpp-gen:
  image: vpp-gen:latest
  networks:
    vpp-net:
      ipv4_address: 10.0.1.40
```

**Key Features**:
- Simulates multiple device types
- Communicates with master station
- Depends on vpp-master
- Logs to ./logs/gen

**Environment Variables**:
- `MASTER_URL`: http://vpp-master:8080
- `LOG_LEVEL`: INFO

### 6. Protocol Analyzer Service (vpp-analyzer)

**Purpose**: Captures and analyzes industrial control protocol traffic

**Configuration**:
```yaml
vpp-analyzer:
  image: vpp-analyzer:latest
  networks:
    vpp-net:
      ipv4_address: 10.0.1.50
  cap_add:
    - NET_ADMIN
    - NET_RAW
```

**Key Features**:
- Captures from OVS mirror port
- Identifies IEC61850, Modbus, DNP3, MQTT protocols
- Generates pcap files
- Collects real-time statistics
- Requires NET_ADMIN and NET_RAW capabilities

**Environment Variables**:
- `CAPTURE_INTERFACE`: veth-analyzer
- `OUTPUT_DIR`: /pcap
- `LOG_LEVEL`: INFO
- `PYTHONUNBUFFERED`: 1

**Volumes**:
- ./pcap:/pcap (pcap files)
- ./logs/analyzer:/var/log/vpp (logs)

## Network Configuration

### Network Details

**Network Name**: vpp-net
**Driver**: bridge
**Subnet**: 10.0.1.0/24
**Gateway**: 10.0.1.1

### IP Address Allocation

| Service | IP Address | Purpose |
|---------|-----------|---------|
| Bridge Gateway | 10.0.1.1 | Network gateway |
| vpp-master | 10.0.1.10 | Master station |
| vpp-vcc | 10.0.1.20 | VCC coordinator |
| vpp-upf | 10.0.1.30 | 5G UPF |
| vpp-gen | 10.0.1.40 | Device simulator |
| vpp-analyzer | 10.0.1.50 | Protocol analyzer |
| mirror-port | 10.0.1.100 | OVS mirror destination |

### Network Connectivity

```
vpp-master (10.0.1.10)
    ↓
vpp-vcc (10.0.1.20) ← → vpp-upf (10.0.1.30) ← → vpp-gen (10.0.1.40)
    ↓
OVS Mirror (10.0.1.100)
    ↓
vpp-analyzer (10.0.1.50)
```

## Volume Configuration

### Volumes

| Volume | Type | Purpose |
|--------|------|---------|
| pcap | local | Pcap file storage |
| logs/master | bind | Master station logs |
| logs/vcc | bind | VCC coordinator logs |
| logs/upf | bind | 5G UPF logs |
| logs/gen | bind | Device simulator logs |
| logs/analyzer | bind | Protocol analyzer logs |

### Directory Structure

```
network-mirror/
├── docker-compose.yml
├── scripts/
│   ├── ovs-init.sh
│   └── ovs-cleanup.sh
├── analyzer/
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── pcap/                    (created at runtime)
│   └── capture_*.pcap
└── logs/                    (created at runtime)
    ├── master/
    ├── vcc/
    ├── upf/
    ├── gen/
    └── analyzer/
```

## Common Commands

### View Service Status

```bash
# List all services
docker-compose ps

# View specific service logs
docker-compose logs vpp-analyzer

# Follow logs in real-time
docker-compose logs -f vpp-master

# View last 100 lines
docker-compose logs --tail=100 vpp-vcc
```

### Manage Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose stop

# Restart specific service
docker-compose restart vpp-analyzer

# Remove all containers
docker-compose down

# Remove containers and volumes
docker-compose down -v
```

### Execute Commands in Containers

```bash
# Execute command in container
docker-compose exec vpp-master bash

# Run one-off command
docker-compose run vpp-analyzer python main.py --help

# View container logs
docker-compose logs vpp-analyzer
```

### Build Images

```bash
# Build all images
docker-compose build

# Build specific image
docker-compose build vpp-analyzer

# Build without cache
docker-compose build --no-cache
```

## Health Checks

### Health Check Configuration

All services (except ovs-init) include health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:PORT/health"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 10s
```

### Check Service Health

```bash
# View health status
docker-compose ps

# Check specific service
docker inspect vpp-master | grep -A 10 "Health"

# View health check logs
docker-compose logs vpp-master
```

## Logging Configuration

### Log Driver

All services use JSON file logging driver:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Log Locations

- Master: ./logs/master/
- VCC: ./logs/vcc/
- UPF: ./logs/upf/
- Gen: ./logs/gen/
- Analyzer: ./logs/analyzer/

### View Logs

```bash
# View all logs
docker-compose logs

# Follow logs
docker-compose logs -f

# View specific service
docker-compose logs vpp-analyzer

# View last N lines
docker-compose logs --tail=50 vpp-master

# View logs since timestamp
docker-compose logs --since 2026-02-17T12:00:00
```

## Restart Policies

All services use restart policy: `on-failure:3`

This means:
- Automatically restart on failure
- Maximum 3 restart attempts
- Prevents infinite restart loops

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs SERVICE_NAME

# Check service status
docker-compose ps

# Restart service
docker-compose restart SERVICE_NAME

# Rebuild image
docker-compose build --no-cache SERVICE_NAME
```

### Network Issues

```bash
# Check network
docker network ls

# Inspect network
docker network inspect network-mirror_vpp-net

# Test connectivity
docker-compose exec vpp-master ping vpp-analyzer
```

### Volume Issues

```bash
# Check volumes
docker volume ls

# Inspect volume
docker volume inspect network-mirror_pcap

# Check disk space
df -h ./pcap
```

### OVS Issues

```bash
# Check OVS status
docker-compose exec ovs-init ovs-vsctl show

# Check bridge
docker-compose exec ovs-init ovs-vsctl list-br

# Check ports
docker-compose exec ovs-init ovs-vsctl list-ports br-vpp
```

## Performance Tuning

### Resource Limits

Add resource limits to services:

```yaml
services:
  vpp-analyzer:
    resources:
      limits:
        cpus: '1'
        memory: 512M
      reservations:
        cpus: '0.5'
        memory: 256M
```

### Network Optimization

```yaml
networks:
  vpp-net:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.enable_ip_masquerade: 'false'
      com.docker.network.driver.mtu: 9000
```

## Security Considerations

### Capabilities

Only vpp-analyzer requires special capabilities:

```yaml
cap_add:
  - NET_ADMIN    # Required for packet capture
  - NET_RAW      # Required for raw sockets
```

### Privileged Mode

Only ovs-init runs in privileged mode (required for OVS):

```yaml
privileged: true
```

### Read-Only Volumes

Scripts are mounted as read-only:

```yaml
volumes:
  - ./scripts/ovs-init.sh:/init.sh:ro
```

## Deployment Checklist

- [ ] Docker and Docker Compose installed
- [ ] OVS support enabled on host
- [ ] Sufficient disk space for pcap files
- [ ] Network ports available (8080, 8081, 8082)
- [ ] All Docker images built or available
- [ ] Log directories created
- [ ] Pcap directory created
- [ ] docker-compose.yml validated
- [ ] All services start successfully
- [ ] Health checks passing
- [ ] Network connectivity verified
- [ ] Traffic mirroring working

## Validation Commands

```bash
# Validate docker-compose.yml
docker-compose config

# Check service status
docker-compose ps

# Verify network
docker network inspect network-mirror_vpp-net

# Test connectivity
docker-compose exec vpp-master ping vpp-analyzer

# Check OVS configuration
docker-compose exec ovs-init ovs-vsctl show

# Verify analyzer is capturing
docker-compose logs vpp-analyzer | grep "Starting packet capture"
```

## References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Networking](https://docs.docker.com/network/)
- [Docker Volumes](https://docs.docker.com/storage/volumes/)
- [Open vSwitch Documentation](http://openvswitch.org/)

## Support

For issues or questions:
1. Check logs: `docker-compose logs SERVICE_NAME`
2. Verify configuration: `docker-compose config`
3. Check network: `docker network inspect network-mirror_vpp-net`
4. Review troubleshooting section above
