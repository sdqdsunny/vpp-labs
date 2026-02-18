# OVS Network Infrastructure Scripts

This directory contains scripts for managing the Open vSwitch (OVS) network infrastructure for the VPP network traffic mirroring system.

## Scripts

### ovs-init.sh

**Purpose**: Initialize OVS bridge and network infrastructure

**Functionality**:
- Checks OVS installation
- Creates OVS bridge (br-vpp)
- Configures bridge IP address (10.0.1.1/24)
- Creates veth-pair ports for all components:
  - veth-master (10.0.1.10) - Master station
  - veth-vcc (10.0.1.20) - VCC coordinator
  - veth-upf (10.0.1.30) - 5G UPF
  - veth-gen (10.0.1.40) - Device simulator
  - veth-analyzer (10.0.1.50) - Protocol analyzer
- Creates mirror port (10.0.1.100)
- Configures mirror rule to clone all traffic
- Verifies configuration
- Displays final configuration

**Usage**:
```bash
sudo ./ovs-init.sh
```

**Requirements**:
- Root/sudo privileges
- OVS installed and running
- Linux kernel >= 4.15

**Output**:
- Colored log messages indicating progress
- Bridge configuration summary
- Port statistics
- Mirror configuration details

**Error Handling**:
- Checks OVS installation before proceeding
- Handles existing resources gracefully
- Verifies configuration after setup
- Provides informative error messages

### ovs-cleanup.sh

**Purpose**: Clean up OVS bridge and network infrastructure

**Functionality**:
- Deletes OVS bridge (br-vpp)
- Deletes all veth-pair ports
- Verifies cleanup completion

**Usage**:
```bash
sudo ./ovs-cleanup.sh
```

**Requirements**:
- Root/sudo privileges
- OVS installed

**Output**:
- Colored log messages indicating progress
- Cleanup verification results

**Error Handling**:
- Handles non-existent resources gracefully
- Verifies cleanup completion
- Provides informative warning messages

## Network Configuration

### Bridge Details
- **Name**: br-vpp
- **IP Address**: 10.0.1.1/24
- **Subnet**: 10.0.1.0/24

### Port Configuration

| Port Name | Type | IP Address | Purpose |
|-----------|------|-----------|---------|
| veth-master-br | veth-pair | 10.0.1.10 | Master station connection |
| veth-vcc-br | veth-pair | 10.0.1.20 | VCC coordinator connection |
| veth-upf-br | veth-pair | 10.0.1.30 | 5G UPF connection |
| veth-gen-br | veth-pair | 10.0.1.40 | Device simulator connection |
| mirror-port | internal | 10.0.1.100 | Mirror destination |
| veth-analyzer-br | veth-pair | 10.0.1.50 | Analyzer connection |

### Mirror Configuration
- **Mirror Name**: m0
- **Select All**: true (captures all traffic)
- **Output Port**: mirror-port
- **Purpose**: Clone all business traffic for analysis

## Quick Start

### Initialize Network
```bash
# Run initialization script
sudo ./ovs-init.sh

# Verify bridge creation
ovs-vsctl show

# Verify mirror configuration
ovs-vsctl list Mirror

# Check port statistics
ovs-ofctl dump-ports br-vpp
```

### Clean Up Network
```bash
# Run cleanup script
sudo ./ovs-cleanup.sh

# Verify cleanup
ovs-vsctl show
```

## Troubleshooting

### OVS Not Installed
**Error**: "OVS not installed"
**Solution**: Install OVS with `sudo apt-get install -y openvswitch-switch`

### Permission Denied
**Error**: "Permission denied"
**Solution**: Run scripts with sudo: `sudo ./ovs-init.sh`

### Bridge Already Exists
**Error**: "Bridge already exists"
**Solution**: The script automatically deletes existing bridge. If issues persist, manually delete with:
```bash
sudo ovs-vsctl del-br br-vpp
```

### Veth Port Already Exists
**Error**: "Veth pair already exists"
**Solution**: The script skips existing ports. To recreate, manually delete with:
```bash
sudo ip link del veth-master
```

### Mirror Rule Not Active
**Error**: "Mirror rule not found"
**Solution**: Re-run initialization script or manually configure:
```bash
sudo ovs-vsctl -- --id=@m create Mirror name=m0 \
  select-all=true output-port=mirror-port \
  -- set Bridge br-vpp mirrors=@m
```

## Monitoring Commands

### View Bridge Configuration
```bash
ovs-vsctl show
```

### View Port Statistics
```bash
ovs-ofctl dump-ports br-vpp
```

### View Flow Table
```bash
ovs-ofctl dump-flows br-vpp
```

### View Mirror Configuration
```bash
ovs-vsctl list Mirror
```

### Monitor Traffic in Real-Time
```bash
ovs-ofctl snoop br-vpp
```

### Check Specific Port Status
```bash
ovs-vsctl get-port br-vpp veth-master-br
```

## Advanced Configuration

### Enable DPDK Acceleration (Optional)
```bash
sudo ovs-vsctl set Open_vSwitch . other_config:dpdk-init=true
```

### Configure Flow Table Cache
```bash
sudo ovs-vsctl set Open_vSwitch . other_config:flow-limit=200000
```

### Enable Multi-threading
```bash
sudo ovs-vsctl set Open_vSwitch . other_config:n-handler-threads=4
```

## Performance Tuning

### Increase MTU for Better Throughput
```bash
sudo ip link set br-vpp mtu 9000
```

### Enable Jumbo Frames on Ports
```bash
sudo ip link set veth-master mtu 9000
```

## Security Considerations

### Restrict Port Access
```bash
# Disable port learning (optional)
ovs-vsctl set port veth-master-br no-recv-from-self=true
```

### Enable Port Security
```bash
# Configure port security rules (optional)
ovs-vsctl set port veth-master-br other-config:port-security=true
```

## Integration with Docker

The scripts are designed to work with Docker Compose. The `ovs-init` service in docker-compose.yml automatically runs these scripts during container startup.

### Docker Compose Integration
```yaml
ovs-init:
  image: ubuntu:22.04
  network_mode: host
  privileged: true
  volumes:
    - ./scripts/ovs-init.sh:/init.sh:ro
    - ./scripts/ovs-cleanup.sh:/cleanup.sh:ro
  command: bash -c "apt-get update && apt-get install -y openvswitch-switch && bash /init.sh"
```

## Maintenance

### Regular Checks
- Monitor bridge status: `ovs-vsctl show`
- Check port statistics: `ovs-ofctl dump-ports br-vpp`
- Verify mirror rule: `ovs-vsctl list Mirror`

### Backup Configuration
```bash
# Export current configuration
ovs-vsctl get-config > ovs-config-backup.txt
```

### Restore Configuration
```bash
# Restore from backup (manual steps required)
# Use the backup file as reference for manual configuration
```

## References

- [Open vSwitch Documentation](http://openvswitch.org/)
- [OVS Man Pages](http://openvswitch.org/support/dist-docs/)
- [Linux veth Documentation](https://man7.org/linux/man-pages/man4/veth.4.html)

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review OVS logs: `journalctl -u openvswitch-switch`
3. Check system logs: `dmesg | tail -20`
4. Consult OVS documentation

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-17 | Initial version |
