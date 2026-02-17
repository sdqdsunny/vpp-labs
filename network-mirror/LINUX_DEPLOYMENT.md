# OVS Network Traffic Mirroring - Linux/OVS Deployment Guide

**Complete Deployment Instructions for Linux with Open vSwitch**

---

## Overview

This guide covers deployment of the OVS Network Traffic Mirroring system on Linux using Open vSwitch (OVS) for production environments. For macOS/Docker development, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

**Deployment Time**: ~15 minutes  
**Difficulty**: Intermediate  
**Platform**: Ubuntu 20.04+ or CentOS 8+  
**OVS Version**: 2.13+

---

## Architecture

### Linux/OVS Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                      Linux Host                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              OVS Virtual Switch (br-vpp)                 │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ Business Ports (veth-pair)                         │  │   │
│  │  │ ├─ veth-master-br (10.0.1.10)                      │  │   │
│  │  │ ├─ veth-vcc-br (10.0.1.20)                         │  │   │
│  │  │ ├─ veth-upf-br (10.0.1.30)                         │  │   │
│  │  │ └─ veth-gen-br (10.0.1.40)                         │  │   │
│  │  │                                                    │  │   │
│  │  │ Mirror Configuration                              │  │   │
│  │  │ └─ Mirror Rule: select-all → mirror-port          │  │   │
│  │  │                                                    │  │   │
│  │  │ Analysis Port                                      │  │   │
│  │  │ └─ mirror-port (internal, 10.0.1.100)             │  │   │
│  │  │ └─ veth-analyzer-br (10.0.1.50)                    │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Docker Containers                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │vpp-master│ │ vpp-vcc  │ │ vpp-upf  │ │ vpp-gen  │    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │         vpp-analyzer (Protocol Analysis)         │   │   │
│  │  │  - Packet capture from mirror-port              │   │   │
│  │  │  - Protocol identification                       │   │   │
│  │  │  - Pcap file generation                          │   │   │
│  │  │  - Statistics collection                         │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Pre-Deployment Checklist

### System Requirements

- [ ] Linux system (Ubuntu 20.04+ or CentOS 8+)
- [ ] Kernel >= 4.15
- [ ] Docker >= 20.10
- [ ] Docker Compose >= 1.29
- [ ] OVS >= 2.13
- [ ] 4GB+ RAM
- [ ] 10GB+ disk space
- [ ] Root/sudo access
- [ ] Network interface available for OVS bridge

### Verify Linux System

```bash
# Check kernel version
uname -r
# Expected: 4.15 or higher

# Check OS version
cat /etc/os-release
# Expected: Ubuntu 20.04+ or CentOS 8+

# Check available memory
free -h
# Expected: 4GB+ available

# Check disk space
df -h /
# Expected: 10GB+ available
```

---

## Phase 1: System Preparation (5 minutes)

### 1.1 Install OVS

#### Ubuntu/Debian

```bash
# Update package manager
sudo apt-get update
sudo apt-get upgrade -y

# Install OVS
sudo apt-get install -y openvswitch-switch openvswitch-common

# Verify installation
ovs-vsctl --version
# Expected: ovs-vsctl (Open vSwitch) 2.13.0 or higher

# Start OVS service
sudo systemctl start openvswitch-switch
sudo systemctl enable openvswitch-switch

# Verify service is running
sudo systemctl status openvswitch-switch
```

#### CentOS/RHEL

```bash
# Update package manager
sudo yum update -y

# Install OVS
sudo yum install -y openvswitch

# Verify installation
ovs-vsctl --version

# Start OVS service
sudo systemctl start openvswitch
sudo systemctl enable openvswitch

# Verify service is running
sudo systemctl status openvswitch
```

### 1.2 Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Verify Docker installation
docker --version
# Expected: Docker version 20.10.0 or higher

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Verify Docker is running
docker ps
```

### 1.3 Install Docker Compose

```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
# Expected: Docker Compose version 1.29.0 or higher
```

### 1.4 Configure User Permissions

```bash
# Add user to docker group (optional, for non-root access)
sudo usermod -aG docker $USER
newgrp docker

# Verify docker access
docker ps

# Note: You may need to log out and log back in for group changes to take effect
```

---

## Phase 2: OVS Configuration (5 minutes)

### 2.1 Create OVS Bridge

```bash
# Create bridge
sudo ovs-vsctl add-br br-vpp

# Configure bridge IP
sudo ip addr add 10.0.1.1/24 dev br-vpp

# Bring up bridge
sudo ip link set br-vpp up

# Verify bridge
sudo ovs-vsctl show
# Expected output should show:
# Bridge "br-vpp"
#     Port "br-vpp"
#         Interface "br-vpp"
#             type: internal
```

### 2.2 Create Veth-Pair Ports

```bash
# Create veth-pair for master
sudo ip link add veth-master-br type veth peer name veth-master-ns
sudo ovs-vsctl add-port br-vpp veth-master-br
sudo ip addr add 10.0.1.10/24 dev veth-master-br
sudo ip link set veth-master-br up

# Create veth-pair for VCC
sudo ip link add veth-vcc-br type veth peer name veth-vcc-ns
sudo ovs-vsctl add-port br-vpp veth-vcc-br
sudo ip addr add 10.0.1.20/24 dev veth-vcc-br
sudo ip link set veth-vcc-br up

# Create veth-pair for UPF
sudo ip link add veth-upf-br type veth peer name veth-upf-ns
sudo ovs-vsctl add-port br-vpp veth-upf-br
sudo ip addr add 10.0.1.30/24 dev veth-upf-br
sudo ip link set veth-upf-br up

# Create veth-pair for generator
sudo ip link add veth-gen-br type veth peer name veth-gen-ns
sudo ovs-vsctl add-port br-vpp veth-gen-br
sudo ip addr add 10.0.1.40/24 dev veth-gen-br
sudo ip link set veth-gen-br up

# Create veth-pair for analyzer
sudo ip link add veth-analyzer-br type veth peer name veth-analyzer-ns
sudo ovs-vsctl add-port br-vpp veth-analyzer-br
sudo ip addr add 10.0.1.50/24 dev veth-analyzer-br
sudo ip link set veth-analyzer-br up

# Verify ports
sudo ovs-vsctl show
```

### 2.3 Create Mirror Port

```bash
# Create internal mirror port
sudo ovs-vsctl add-port br-vpp mirror-port -- set Interface mirror-port type=internal

# Configure mirror port IP
sudo ip addr add 10.0.1.100/24 dev mirror-port
sudo ip link set mirror-port up

# Verify mirror port
sudo ip link show mirror-port
```

### 2.4 Configure Mirror Rule

```bash
# Create mirror rule
sudo ovs-vsctl -- --id=@m create Mirror name=m0 select-all=true output-port=@mirror-port -- set Bridge br-vpp mirrors=@m

# Verify mirror configuration
sudo ovs-vsctl list Mirror
# Expected output should show:
# _uuid               : <uuid>
# name                : "m0"
# output-port         : <port-uuid>
# select-all          : true
# statistics          : {}
```

### 2.5 Verify OVS Configuration

```bash
# Display complete OVS configuration
sudo ovs-vsctl show

# Check bridge status
sudo ovs-vsctl get-br-status br-vpp

# Check port statistics
sudo ovs-ofctl dump-ports br-vpp

# Check flow table
sudo ovs-ofctl dump-flows br-vpp

# Test connectivity
ping -c 3 10.0.1.10
ping -c 3 10.0.1.50
```

---

## Phase 3: Docker Configuration (3 minutes)

### 3.1 Create Docker Network

```bash
# Create Docker network connected to OVS bridge
docker network create \
  --driver bridge \
  --subnet=10.0.1.0/24 \
  --gateway=10.0.1.1 \
  --opt "com.docker.network.bridge.name=br-vpp" \
  vpp-net

# Verify network
docker network inspect vpp-net
```

### 3.2 Update docker-compose.yml

```bash
# Update docker-compose.yml to use OVS bridge
# Change network configuration from:
# networks:
#   vpp-net:
#     driver: bridge
#     ipam:
#       config:
#         - subnet: 10.0.1.0/24
#           gateway: 10.0.1.1
#
# To:
# networks:
#   vpp-net:
#     external: true

# Or use the provided docker-compose-ovs.yml
cp docker-compose.yml docker-compose-ovs.yml

# Edit docker-compose-ovs.yml to use external network
cat > docker-compose-ovs.yml << 'EOF'
version: '3.8'

services:
  vpp-master:
    image: vpp-master-vpp-master:latest
    container_name: vpp-master
    networks:
      vpp-net:
        ipv4_address: 10.0.1.10
    environment:
      - PYTHONUNBUFFERED=1
    ports:
      - "8090:8090"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8090/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    depends_on:
      - vpp-analyzer

  vpp-vcc:
    image: alpine:latest
    container_name: vpp-vcc
    networks:
      vpp-net:
        ipv4_address: 10.0.1.20
    command: sleep infinity
    depends_on:
      - vpp-master

  vpp-upf:
    image: alpine:latest
    container_name: vpp-upf
    networks:
      vpp-net:
        ipv4_address: 10.0.1.30
    command: sleep infinity
    depends_on:
      - vpp-master

  vpp-gen:
    image: alpine:latest
    container_name: vpp-gen
    networks:
      vpp-net:
        ipv4_address: 10.0.1.40
    command: sleep infinity
    depends_on:
      - vpp-master

  vpp-analyzer:
    image: vpp-analyzer:latest
    container_name: vpp-analyzer
    networks:
      vpp-net:
        ipv4_address: 10.0.1.50
    environment:
      - CAPTURE_INTERFACE=veth-analyzer-br
      - OUTPUT_DIR=/pcap
      - PYTHONUNBUFFERED=1
    volumes:
      - ./pcap:/pcap
      - ./logs/analyzer:/var/log/vpp
    cap_add:
      - NET_ADMIN
      - NET_RAW
    depends_on:
      - vpp-master

networks:
  vpp-net:
    external: true
EOF
```

---

## Phase 4: Deployment (3 minutes)

### 4.1 Build Docker Images

```bash
# Build all images
docker-compose build

# Verify images
docker images | grep vpp
```

### 4.2 Start Services

```bash
# Start all services
docker-compose -f docker-compose-ovs.yml up -d

# Monitor startup
docker-compose -f docker-compose-ovs.yml logs -f

# Wait for services to be ready
sleep 30
```

### 4.3 Verify Services

```bash
# Check service status
docker-compose -f docker-compose-ovs.yml ps

# Expected output:
# NAME                COMMAND             STATUS              PORTS
# vpp-master          python app.py       Up (healthy)        0.0.0.0:8090->8090/tcp
# vpp-vcc             sleep infinity      Up                   
# vpp-upf             sleep infinity      Up                   
# vpp-gen             sleep infinity      Up                   
# vpp-analyzer        python main.py      Up                   
```

---

## Phase 5: Verification (2 minutes)

### 5.1 Verify OVS Configuration

```bash
# Check bridge
sudo ovs-vsctl show

# Check mirror rule
sudo ovs-vsctl list Mirror

# Check port statistics
sudo ovs-ofctl dump-ports br-vpp
```

### 5.2 Verify Network Connectivity

```bash
# Test ping between services
docker-compose -f docker-compose-ovs.yml exec vpp-master ping -c 3 vpp-analyzer

# Test DNS resolution
docker-compose -f docker-compose-ovs.yml exec vpp-master nslookup vpp-analyzer

# Check network
docker network inspect vpp-net
```

### 5.3 Verify Analyzer

```bash
# Check analyzer logs
docker-compose -f docker-compose-ovs.yml logs vpp-analyzer

# Check pcap files
ls -lh pcap/

# Verify pcap file format
file pcap/*.pcap
```

### 5.4 Verify Traffic Capture

```bash
# Generate test traffic
docker-compose -f docker-compose-ovs.yml exec vpp-master ping -c 10 vpp-gen

# Check analyzer logs for captured traffic
docker-compose -f docker-compose-ovs.yml logs vpp-analyzer | grep "Statistics"

# Check pcap files
ls -lh pcap/
```

---

## Post-Deployment Checklist

- [ ] OVS bridge created (br-vpp)
- [ ] All veth-pair ports created
- [ ] Mirror port created
- [ ] Mirror rule configured
- [ ] All services running
- [ ] Network connectivity verified
- [ ] Analyzer capturing traffic
- [ ] Pcap files being generated
- [ ] No errors in logs

---

## OVS Management Commands

### Bridge Management

```bash
# Show bridge configuration
sudo ovs-vsctl show

# Show bridge status
sudo ovs-vsctl get-br-status br-vpp

# Delete bridge
sudo ovs-vsctl del-br br-vpp
```

### Port Management

```bash
# List ports
sudo ovs-vsctl list-ports br-vpp

# Add port
sudo ovs-vsctl add-port br-vpp <port-name>

# Remove port
sudo ovs-vsctl del-port br-vpp <port-name>

# Show port statistics
sudo ovs-ofctl dump-ports br-vpp
```

### Mirror Management

```bash
# List mirrors
sudo ovs-vsctl list Mirror

# Create mirror
sudo ovs-vsctl -- --id=@m create Mirror name=m0 select-all=true output-port=@mirror-port -- set Bridge br-vpp mirrors=@m

# Delete mirror
sudo ovs-vsctl clear Bridge br-vpp mirrors
```

### Flow Management

```bash
# Show flow table
sudo ovs-ofctl dump-flows br-vpp

# Clear flow table
sudo ovs-ofctl del-flows br-vpp

# Monitor flows
sudo ovs-ofctl snoop br-vpp
```

---

## Troubleshooting

### OVS Bridge Not Created

**Problem**: Bridge creation fails

**Solution**:
```bash
# Check OVS service
sudo systemctl status openvswitch-switch

# Restart OVS service
sudo systemctl restart openvswitch-switch

# Try creating bridge again
sudo ovs-vsctl add-br br-vpp
```

### Veth-Pair Creation Fails

**Problem**: Permission denied or interface exists

**Solution**:
```bash
# Check if interface exists
ip link show veth-master-br

# Delete existing interface
sudo ip link del veth-master-br

# Try creating again
sudo ip link add veth-master-br type veth peer name veth-master-ns
```

### Mirror Rule Not Working

**Problem**: Traffic not being mirrored

**Solution**:
```bash
# Verify mirror configuration
sudo ovs-vsctl list Mirror

# Check mirror port
sudo ovs-vsctl list-ports br-vpp | grep mirror-port

# Recreate mirror rule
sudo ovs-vsctl clear Bridge br-vpp mirrors
sudo ovs-vsctl -- --id=@m create Mirror name=m0 select-all=true output-port=@mirror-port -- set Bridge br-vpp mirrors=@m
```

### Docker Network Issues

**Problem**: Containers can't communicate

**Solution**:
```bash
# Check network
docker network inspect vpp-net

# Test connectivity
docker-compose -f docker-compose-ovs.yml exec vpp-master ping vpp-analyzer

# Restart network
docker network disconnect vpp-net vpp-master
docker network connect vpp-net vpp-master
```

### Analyzer Not Capturing

**Problem**: No pcap files being generated

**Solution**:
```bash
# Check analyzer logs
docker-compose -f docker-compose-ovs.yml logs vpp-analyzer

# Check interface
docker-compose -f docker-compose-ovs.yml exec vpp-analyzer ip link show

# Verify mirror port is receiving traffic
sudo tcpdump -i mirror-port -c 10

# Restart analyzer
docker-compose -f docker-compose-ovs.yml restart vpp-analyzer
```

---

## Cleanup

### Remove Services

```bash
# Stop services
docker-compose -f docker-compose-ovs.yml down

# Remove containers
docker-compose -f docker-compose-ovs.yml down -v

# Remove images
docker-compose -f docker-compose-ovs.yml down --rmi all
```

### Remove OVS Configuration

```bash
# Delete mirror rule
sudo ovs-vsctl clear Bridge br-vpp mirrors

# Delete mirror port
sudo ovs-vsctl del-port br-vpp mirror-port

# Delete veth-pair ports
sudo ovs-vsctl del-port br-vpp veth-master-br
sudo ovs-vsctl del-port br-vpp veth-vcc-br
sudo ovs-vsctl del-port br-vpp veth-upf-br
sudo ovs-vsctl del-port br-vpp veth-gen-br
sudo ovs-vsctl del-port br-vpp veth-analyzer-br

# Delete bridge
sudo ovs-vsctl del-br br-vpp

# Delete veth-pair interfaces
sudo ip link del veth-master-br
sudo ip link del veth-vcc-br
sudo ip link del veth-upf-br
sudo ip link del veth-gen-br
sudo ip link del veth-analyzer-br
```

### Remove Docker Network

```bash
# Remove Docker network
docker network rm vpp-net
```

---

## Performance Optimization

### OVS Tuning

```bash
# Increase OVS memory
sudo ovs-vsctl set Open_vSwitch . other_config:max-idle=60000

# Enable flow caching
sudo ovs-vsctl set Open_vSwitch . other_config:flow-cache-size=256

# Increase datapath threads
sudo ovs-vsctl set Open_vSwitch . other_config:n-handler-threads=4
```

### Network Optimization

```bash
# Increase MTU
sudo ip link set br-vpp mtu 9000

# Enable jumbo frames
sudo ip link set veth-master-br mtu 9000
sudo ip link set veth-analyzer-br mtu 9000
```

### Storage Optimization

```bash
# Clean up old pcap files
find pcap -name "*.pcap" -mtime +30 -delete

# Compress old logs
gzip logs/*/*.log
```

---

## Monitoring

### Real-Time Monitoring

```bash
# Monitor OVS statistics
watch -n 1 'sudo ovs-ofctl dump-ports br-vpp'

# Monitor Docker logs
docker-compose -f docker-compose-ovs.yml logs -f

# Monitor disk usage
watch -n 1 'du -sh pcap/ logs/'
```

### Performance Monitoring

```bash
# Monitor traffic on mirror port
sudo tcpdump -i mirror-port -n

# Monitor OVS flows
sudo ovs-ofctl snoop br-vpp

# Monitor system resources
docker stats
```

---

## Maintenance

### Regular Tasks

```bash
# Daily: Check logs
docker-compose -f docker-compose-ovs.yml logs --since 24h

# Weekly: Clean old pcap files
find pcap -name "*.pcap" -mtime +7 -delete

# Monthly: Backup configuration
tar -czf backup_$(date +%Y%m%d).tar.gz pcap/ logs/ docker-compose-ovs.yml
```

### Backup

```bash
# Backup OVS configuration
sudo ovs-vsctl show > ovs_config_$(date +%Y%m%d).txt

# Backup pcap files
tar -czf pcap_backup_$(date +%Y%m%d).tar.gz pcap/

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Create bridge | `sudo ovs-vsctl add-br br-vpp` |
| Show config | `sudo ovs-vsctl show` |
| Add port | `sudo ovs-vsctl add-port br-vpp <port>` |
| Create mirror | `sudo ovs-vsctl -- --id=@m create Mirror name=m0 select-all=true output-port=@mirror-port -- set Bridge br-vpp mirrors=@m` |
| Start services | `docker-compose -f docker-compose-ovs.yml up -d` |
| Check status | `docker-compose -f docker-compose-ovs.yml ps` |
| View logs | `docker-compose -f docker-compose-ovs.yml logs -f` |
| Test traffic | `docker-compose -f docker-compose-ovs.yml exec vpp-master ping vpp-gen` |
| Check pcap | `ls -lh pcap/` |
| Monitor flows | `sudo ovs-ofctl snoop br-vpp` |

---

## See Also

- [README.md](README.md) - Project overview
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - macOS/Docker deployment
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing procedures
- [DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md) - Docker Compose reference

---

## Support

For issues or questions:
1. Check OVS configuration: `sudo ovs-vsctl show`
2. Check Docker logs: `docker-compose -f docker-compose-ovs.yml logs`
3. Verify network: `docker network inspect vpp-net`
4. Test connectivity: `docker-compose -f docker-compose-ovs.yml exec vpp-master ping vpp-analyzer`
5. Review troubleshooting section above
