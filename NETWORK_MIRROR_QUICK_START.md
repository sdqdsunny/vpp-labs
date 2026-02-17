# Network Mirror - Quick Start Guide

## Current Status

✅ **System is running and ready for testing**

All services deployed successfully using Docker native networking.

---

## Quick Commands

### Start the system
```bash
docker-compose -f network-mirror/docker-compose.yml up -d
```

### Stop the system
```bash
docker-compose -f network-mirror/docker-compose.yml down
```

### View logs
```bash
# All services
docker-compose -f network-mirror/docker-compose.yml logs -f

# Specific service
docker logs vpp-analyzer -f
docker logs vpp-master -f
```

### Check status
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep vpp-
```

---

## Service Access

| Service | URL | Port | Purpose |
|---------|-----|------|---------|
| vpp-master | http://localhost:9080 | 9080 | Master station API |
| vpp-vcc | http://localhost:9081 | 9081 | VCC coordinator API |
| vpp-upf | http://localhost:9082 | 9082 | 5G UPF API |
| vpp-analyzer | - | - | Traffic analyzer (no HTTP) |

---

## Network Details

- **Network**: vpp-net (Docker bridge)
- **Subnet**: 10.0.1.0/24
- **Gateway**: 10.0.1.1

### Container IPs

| Container | IP |
|-----------|-----|
| vpp-master | 10.0.1.10 |
| vpp-vcc | 10.0.1.20 |
| vpp-upf | 10.0.1.30 |
| vpp-gen | 10.0.1.40 |
| vpp-analyzer | 10.0.1.50 |

---

## Analyzer Output

- **Capture Interface**: eth0 (Docker network)
- **Output Directory**: ./network-mirror/pcap/
- **Log Directory**: ./network-mirror/logs/analyzer/

### Check captured traffic
```bash
ls -lh network-mirror/pcap/
```

### View analyzer logs
```bash
docker logs vpp-analyzer
```

---

## Important Notes

⚠️ **Do NOT use OVS commands** - System uses Docker native networking

✅ **vpp-phase2-simulation is still running** on ports 8080-8081

✅ **No network disruption** - All changes are isolated to Docker

---

## Next Steps

1. **Generate test traffic** between containers
2. **Verify analyzer captures** traffic
3. **Check pcap files** are being generated
4. **Run integration tests** to validate functionality

---

## Troubleshooting

### Containers not starting?
```bash
docker-compose -f network-mirror/docker-compose.yml logs
```

### Port already in use?
```bash
lsof -i :9080
```

### Need to rebuild images?
```bash
docker-compose -f network-mirror/docker-compose.yml build --no-cache
```

---

## Key Files

- `network-mirror/docker-compose.yml` - Main configuration
- `network-mirror/analyzer/main.py` - Protocol analyzer
- `network-mirror/logs/` - Service logs
- `network-mirror/pcap/` - Captured traffic files

---

**Last Updated**: 2026-02-17 07:03  
**Status**: ✅ Ready for testing
