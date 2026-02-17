# OVS Network Traffic Mirroring - Deployment Guide

**Complete Step-by-Step Deployment Instructions for macOS/Docker**

---

## Overview

This guide covers deployment of the OVS Network Traffic Mirroring system on macOS using Docker native bridge networking. For Linux/OVS deployment, see [LINUX_DEPLOYMENT.md](LINUX_DEPLOYMENT.md).

**Deployment Time**: ~10 minutes  
**Difficulty**: Beginner-friendly  
**Platform**: macOS 10.15+ or Linux with Docker

---

## Pre-Deployment Checklist

### System Requirements

- [ ] macOS 10.15+ or Linux system
- [ ] Docker Desktop 4.0+ (macOS) or Docker 20.10+ (Linux)
- [ ] Docker Compose 1.29+
- [ ] 4GB+ RAM available
- [ ] 5GB+ disk space
- [ ] Internet connection (for pulling images)

### Verify Installation

```bash
# Check Docker
docker --version
# Expected: Docker version 20.10.0 or higher

# Check Docker Compose
docker-compose --version
# Expected: Docker Compose version 1.29.0 or higher

# Check Docker daemon
docker ps
# Expected: No errors, shows running containers
```

### Prepare System

```bash
# Create project directory
mkdir -p ~/projects/network-mirror
cd ~/projects/network-mirror

# Clone repository (or download files)
git clone <repository-url> .

# Verify files
ls -la
# Should show: docker-compose.yml, analyzer/, scripts/, tests/, etc.
```

---

## Phase 1: Preparation (2 minutes)

### 1.1 Verify Project Structure

```bash
# Check required files
test -f docker-compose.yml && echo "✓ docker-compose.yml"
test -f analyzer/main.py && echo "✓ analyzer/main.py"
test -f analyzer/Dockerfile && echo "✓ analyzer/Dockerfile"
test -d tests && echo "✓ tests directory"
test -d scripts && echo "✓ scripts directory"

# Create required directories
mkdir -p logs/{master,vcc,upf,gen,analyzer}
mkdir -p pcap
mkdir -p scripts

# Verify structure
tree -L 2 -I '__pycache__|*.pyc'
```

### 1.2 Validate Configuration

```bash
# Validate docker-compose.yml
docker-compose config > /dev/null && echo "✓ docker-compose.yml is valid"

# Check for syntax errors
docker-compose config 2>&1 | head -20

# List services
docker-compose config --services
# Expected output:
# vpp-master
# vpp-vcc
# vpp-upf
# vpp-gen
# vpp-analyzer
```

### 1.3 Check Docker Resources

```bash
# Check available disk space
df -h | grep -E "Filesystem|/$"
# Need at least 5GB free

# Check available memory
docker info | grep "Memory:"
# Need at least 4GB

# Check Docker daemon status
docker info | grep "Server Version"
```

---

## Phase 2: Build (3 minutes)

### 2.1 Build Docker Images

```bash
# Build all images
docker-compose build

# Expected output:
# Building vpp-master
# Building vpp-vcc
# Building vpp-upf
# Building vpp-gen
# Building vpp-analyzer
```

### 2.2 Verify Images

```bash
# List built images
docker images | grep vpp

# Expected output:
# vpp-analyzer          latest    <image-id>    <size>
# vpp-master-vpp-master latest    <image-id>    <size>
# alpine                latest    <image-id>    <size>

# Check image details
docker inspect vpp-analyzer:latest | grep -E "Id|Size|Architecture"

# Verify image can run
docker run --rm vpp-analyzer:latest python -c "import scapy; print('✓ Scapy installed')"
```

### 2.3 Handle Build Issues

```bash
# If build fails, rebuild without cache
docker-compose build --no-cache

# If specific image fails, rebuild just that image
docker-compose build --no-cache vpp-analyzer

# Check build logs
docker-compose build 2>&1 | tail -50
```

---

## Phase 3: Deployment (3 minutes)

### 3.1 Start Services

```bash
# Start all services in background
docker-compose up -d

# Expected output:
# Creating network "network-mirror_vpp-net" with driver "bridge"
# Creating vpp-master ... done
# Creating vpp-vcc ... done
# Creating vpp-upf ... done
# Creating vpp-gen ... done
# Creating vpp-analyzer ... done
```

### 3.2 Monitor Startup

```bash
# Watch service startup (30-60 seconds)
docker-compose logs -f

# In another terminal, check status
watch -n 2 'docker-compose ps'

# Wait for all services to be healthy
sleep 30
docker-compose ps
```

### 3.3 Verify Services Running

```bash
# Check all services are running
docker-compose ps

# Expected output:
# NAME                COMMAND             STATUS              PORTS
# vpp-master          python app.py       Up (healthy)        0.0.0.0:8090->8090/tcp
# vpp-vcc             python app.py       Up (healthy)        
# vpp-upf             python app.py       Up (healthy)        
# vpp-gen             python app.py       Up                   
# vpp-analyzer        python main.py      Up                   

# If any service is not running, check logs
docker-compose logs [service-name]
```

---

## Phase 4: Verification (2 minutes)

### 4.1 Verify Network Connectivity

```bash
# Test ping between services
docker-compose exec vpp-master ping -c 3 vpp-analyzer
# Expected: 3 packets transmitted, 3 received, 0% packet loss

# Test DNS resolution
docker-compose exec vpp-master nslookup vpp-analyzer
# Expected: Address: 10.0.1.50

# Check network details
docker network inspect network-mirror_vpp-net | grep -A 20 "Containers"
```

### 4.2 Verify Analyzer

```bash
# Check analyzer logs
docker-compose logs vpp-analyzer | head -20

# Expected output:
# VPP Protocol Analyzer starting...
# Interface: eth0
# Output directory: /pcap
# PacketAnalyzer initialized on interface: eth0
# Starting packet capture on eth0...

# Check for errors
docker-compose logs vpp-analyzer | grep -i error
# Should return no results
```

### 4.3 Verify Traffic Capture

```bash
# Generate test traffic
docker-compose exec vpp-master ping -c 10 vpp-gen

# Check analyzer logs for captured traffic
docker-compose logs vpp-analyzer | grep "Statistics"

# Check pcap files
ls -lh pcap/
# Should show pcap files being created

# Verify pcap file format
file pcap/*.pcap
# Expected: pcap capture file - version 2.4
```

### 4.4 Complete Verification

```bash
# Run verification script
cat > verify.sh << 'EOF'
#!/bin/bash
echo "=== Service Status ==="
docker-compose ps

echo -e "\n=== Network Status ==="
docker network inspect network-mirror_vpp-net | grep -A 5 "Containers"

echo -e "\n=== Analyzer Logs (last 10 lines) ==="
docker-compose logs vpp-analyzer | tail -10

echo -e "\n=== Pcap Files ==="
ls -lh pcap/

echo -e "\n=== Connectivity Test ==="
docker-compose exec vpp-master ping -c 1 vpp-analyzer && echo "✓ Connectivity OK"

echo -e "\n=== Verification Complete ==="
EOF

chmod +x verify.sh
./verify.sh
```

---

## Post-Deployment Checklist

- [ ] All services running (`docker-compose ps`)
- [ ] All services healthy (no "Unhealthy" status)
- [ ] Network connectivity verified (ping test)
- [ ] Analyzer capturing traffic (pcap files created)
- [ ] No errors in logs (`docker-compose logs`)
- [ ] Disk space available (`df -h`)
- [ ] Memory available (`docker stats`)

---

## Common Operations

### View Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs vpp-analyzer

# View last N lines
docker-compose logs --tail=50

# Follow logs in real-time
docker-compose logs -f

# View logs with timestamps
docker-compose logs -f --timestamps

# View logs since specific time
docker-compose logs --since 10m
```

### Manage Services

```bash
# Stop all services
docker-compose stop

# Start all services
docker-compose start

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart vpp-analyzer

# Remove containers (keep images)
docker-compose down

# Remove everything (containers, volumes, networks)
docker-compose down -v
```

### Access Containers

```bash
# Open shell in container
docker-compose exec vpp-analyzer bash

# Run command in container
docker-compose exec vpp-master curl http://localhost:8090/health

# Check environment variables
docker-compose exec vpp-analyzer env | grep CAPTURE
```

### Monitor Performance

```bash
# Monitor resource usage
docker stats

# Monitor specific container
docker stats vpp-analyzer

# Monitor disk usage
du -sh pcap/ logs/

# Monitor in real-time
watch -n 1 'du -sh pcap/ logs/'
```

---

## Troubleshooting

### Services Won't Start

**Problem**: Services show "Exited" status

**Solution**:
```bash
# Check logs
docker-compose logs [service-name]

# Rebuild image
docker-compose build --no-cache [service-name]

# Restart service
docker-compose restart [service-name]

# Check Docker daemon
docker ps
```

### Health Check Failing

**Problem**: Service shows "Unhealthy" status

**Solution**:
```bash
# Check health status
docker inspect vpp-master | grep -A 10 "Health"

# Check service logs
docker-compose logs vpp-master

# Restart service
docker-compose restart vpp-master

# Wait for startup
sleep 30
docker-compose ps
```

### Network Issues

**Problem**: Services can't communicate

**Solution**:
```bash
# Test connectivity
docker-compose exec vpp-master ping vpp-analyzer

# Check network
docker network inspect network-mirror_vpp-net

# Check DNS
docker-compose exec vpp-master nslookup vpp-analyzer

# Restart network
docker-compose down
docker-compose up -d
```

### Analyzer Not Capturing

**Problem**: No pcap files being generated

**Solution**:
```bash
# Check analyzer logs
docker-compose logs vpp-analyzer

# Check interface
docker-compose exec vpp-analyzer ip link show

# Generate test traffic
docker-compose exec vpp-master ping vpp-gen

# Check pcap files
ls -la pcap/

# Restart analyzer
docker-compose restart vpp-analyzer
```

### Disk Space Issues

**Problem**: Disk full or running out of space

**Solution**:
```bash
# Check disk usage
df -h

# Check pcap directory size
du -sh pcap/

# Clean old pcap files
find pcap -name "*.pcap" -mtime +7 -delete

# Clean old logs
find logs -name "*.log" -mtime +7 -delete

# Remove Docker unused resources
docker system prune -a
```

### Permission Issues

**Problem**: Permission denied errors

**Solution**:
```bash
# Check file permissions
ls -la pcap/ logs/

# Fix permissions
chmod 755 pcap logs
chmod 644 pcap/*.pcap logs/*/*.log

# Run with sudo if needed
sudo docker-compose up -d
```

---

## Testing

### Run Test Suite

```bash
# Install test dependencies
pip3 install pytest hypothesis scapy docker pyyaml

# Run all tests
python3 -m pytest network-mirror/tests/ -v

# Expected: 78 passed, 2 skipped in ~130 seconds
```

### Run Specific Tests

```bash
# Unit tests
python3 -m pytest network-mirror/tests/test_analyzer.py -v

# Integration tests
python3 -m pytest network-mirror/tests/test_analyzer_integration.py -v

# Property-based tests
python3 -m pytest network-mirror/tests/test_properties.py -v

# Docker tests
python3 -m pytest network-mirror/tests/test_docker_integration.py -v
```

---

## Maintenance

### Regular Tasks

```bash
# Daily: Check logs
docker-compose logs --since 24h

# Weekly: Clean old pcap files
find pcap -name "*.pcap" -mtime +7 -delete

# Monthly: Backup data
tar -czf backup_$(date +%Y%m%d).tar.gz pcap/ logs/
```

### Backup

```bash
# Backup pcap files
tar -czf pcap_backup_$(date +%Y%m%d).tar.gz pcap/

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# Backup configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz docker-compose.yml
```

### Updates

```bash
# Pull latest images
docker-compose pull

# Rebuild images
docker-compose build --no-cache

# Restart services
docker-compose restart
```

---

## Shutdown

### Graceful Shutdown

```bash
# Stop all services
docker-compose stop

# Verify stopped
docker-compose ps

# Wait for graceful shutdown
sleep 10
```

### Complete Cleanup

```bash
# Remove containers and volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Verify cleanup
docker ps -a
docker images | grep vpp
```

---

## Performance Optimization

### Resource Limits

Add to docker-compose.yml:

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
      com.docker.network.driver.mtu: 9000
```

### Storage Optimization

```bash
# Clean up old pcap files
find pcap -name "*.pcap" -mtime +30 -delete

# Compress old logs
gzip logs/*/*.log
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start | `docker-compose up -d` |
| Stop | `docker-compose stop` |
| Status | `docker-compose ps` |
| Logs | `docker-compose logs -f` |
| Build | `docker-compose build` |
| Clean | `docker-compose down -v` |
| Verify | `docker-compose config` |
| Test | `pytest network-mirror/tests/ -v` |
| Verify Network | `docker network inspect network-mirror_vpp-net` |
| Verify Analyzer | `docker-compose logs vpp-analyzer` |

---

## Next Steps

1. **Deploy**: Follow Phase 1-4 above
2. **Test**: Run `pytest network-mirror/tests/ -v`
3. **Monitor**: Check logs with `docker-compose logs -f`
4. **Analyze**: Review pcap files in `pcap/` directory
5. **Scale**: Add more services or analyzers as needed

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs [service-name]`
2. Review troubleshooting section above
3. Verify configuration: `docker-compose config`
4. Check system resources: `docker stats`
5. Run tests: `pytest network-mirror/tests/ -v`

---

## See Also

- [README.md](README.md) - Project overview
- [LINUX_DEPLOYMENT.md](LINUX_DEPLOYMENT.md) - Linux/OVS deployment
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing procedures
- [DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md) - Docker Compose reference
