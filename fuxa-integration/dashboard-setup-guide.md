# FUXA Dashboard Setup Guide - Task 3.2

**Task**: Dashboard Creation  
**FUXA URL**: http://localhost:1881  
**Date**: 2026-02-17

---

## Overview

This guide walks through creating the VPP Traffic Visualization dashboard in FUXA with 6 widgets for real-time traffic monitoring.

---

## Prerequisites

✅ FUXA running at http://localhost:1881  
✅ Mosquitto MQTT broker running at localhost:1883  
✅ Device configuration file ready: `fuxa-device-config.json`

---

## Step 1: Access FUXA Web UI

1. Open browser and navigate to: **http://localhost:1881**
2. FUXA editor interface should load

---

## Step 2: Import Device Configuration

### Option A: Manual Device Setup

1. Click **"Devices"** in the left sidebar
2. Click **"Add Device"** button
3. Configure MQTT device:
   - **Name**: VPP Traffic Analyzer
   - **Type**: MQTT Client
   - **Broker URL**: mqtt://mosquitto:1883
   - **Client ID**: fuxa-vpp-analyzer
   - **QoS**: 1
   - **Keep Alive**: 60
4. Click **"Save"**

### Option B: Import Configuration (Recommended)

1. Click **"Project"** menu → **"Import"**
2. Select `fuxa-device-config.json`
3. Click **"Import"**
4. Verify device appears in device list

---

## Step 3: Configure MQTT Variables

For each of the 15 variables, add them to the device:

### Statistics Variables (2)
1. **total_packets**
   - Topic: `vpp/traffic/stats`
   - Path: `total_packets`
   - Type: Number

2. **packet_rate**
   - Topic: `vpp/traffic/rate`
   - Path: `rate`
   - Type: Number

### Protocol Variables (5)
3. **iec61850_count**
   - Topic: `vpp/traffic/protocols`
   - Path: `protocols.IEC61850`
   - Type: Number

4. **modbus_count**
   - Topic: `vpp/traffic/protocols`
   - Path: `protocols.Modbus`
   - Type: Number

5. **mqtt_count**
   - Topic: `vpp/traffic/protocols`
   - Path: `protocols.MQTT`
   - Type: Number

6. **dnp3_count**
   - Topic: `vpp/traffic/protocols`
   - Path: `protocols.DNP3`
   - Type: Number

7. **unknown_count**
   - Topic: `vpp/traffic/protocols`
   - Path: `protocols.Unknown`
   - Type: Number

### Component Packet Variables (4)
8. **master_packets**
   - Topic: `vpp/traffic/components/master`
   - Path: `packets`
   - Type: Number

9. **vcc_packets**
   - Topic: `vpp/traffic/components/vcc`
   - Path: `packets`
   - Type: Number

10. **upf_packets**
    - Topic: `vpp/traffic/components/upf`
    - Path: `packets`
    - Type: Number

11. **gen_packets**
    - Topic: `vpp/traffic/components/gen`
    - Path: `packets`
    - Type: Number

### Component Byte Variables (4)
12. **master_bytes**
    - Topic: `vpp/traffic/components/master`
    - Path: `bytes`
    - Type: Number

13. **vcc_bytes**
    - Topic: `vpp/traffic/components/vcc`
    - Path: `bytes`
    - Type: Number

14. **upf_bytes**
    - Topic: `vpp/traffic/components/upf`
    - Path: `bytes`
    - Type: Number

15. **gen_bytes**
    - Topic: `vpp/traffic/components/gen`
    - Path: `bytes`
    - Type: Number

---

## Step 4: Create Dashboard

1. Click **"Views"** in the left sidebar
2. Click **"Add View"** button
3. Configure dashboard:
   - **Name**: VPP Traffic Visualization
   - **Layout**: Grid (12 columns)
   - **Background**: Dark or Light (your preference)
4. Click **"Save"**

---

## Step 5: Add Widgets

### Widget 1: Total Packets Gauge

1. Click **"Add Widget"** → **"Gauge"**
2. Position: Top-right area
3. Configure:
   - **Title**: Total Packets
   - **Variable**: Select `total_packets`
   - **Min**: 0
   - **Max**: 10000000
   - **Unit**: packets
   - **Size**: Medium (3x3 grid)
4. Click **"Save"**

### Widget 2: Packet Rate Gauge

1. Click **"Add Widget"** → **"Gauge"**
2. Position: Next to Total Packets
3. Configure:
   - **Title**: Packet Rate
   - **Variable**: Select `packet_rate`
   - **Min**: 0
   - **Max**: 100000
   - **Unit**: pps
   - **Size**: Medium (3x3 grid)
4. Click **"Save"**

### Widget 3: Protocol Distribution (Pie Chart)

1. Click **"Add Widget"** → **"Chart"** → **"Pie"**
2. Position: Middle-right area
3. Configure:
   - **Title**: Protocol Distribution
   - **Variables**: 
     - iec61850_count (IEC61850)
     - modbus_count (Modbus)
     - mqtt_count (MQTT)
     - dnp3_count (DNP3)
     - unknown_count (Unknown)
   - **Size**: Large (6x3 grid)
4. Click **"Save"**

### Widget 4: Component Traffic (Bar Chart)

1. Click **"Add Widget"** → **"Chart"** → **"Bar"**
2. Position: Bottom-left area
3. Configure:
   - **Title**: Traffic by Component
   - **Variables**:
     - master_packets (Master)
     - vcc_packets (VCC)
     - upf_packets (UPF)
     - gen_packets (Generator)
   - **Size**: Large (6x3 grid)
4. Click **"Save"**

### Widget 5: Network Topology (Custom - Placeholder)

1. Click **"Add Widget"** → **"HTML"** or **"SVG"**
2. Position: Top-left area
3. Configure:
   - **Title**: VPP Network Topology
   - **Size**: Large (6x6 grid)
   - **Content**: Placeholder text or simple SVG
4. Click **"Save"**

Note: Custom topology widget will be developed in Task 3.3

### Widget 6: Component Health (Custom - Placeholder)

1. Click **"Add Widget"** → **"HTML"** or **"Table"**
2. Position: Bottom-right area
3. Configure:
   - **Title**: Component Health Status
   - **Size**: Large (6x3 grid)
   - **Content**: Status indicators for Master, VCC, UPF, Gen
4. Click **"Save"**

Note: Custom health widget will be developed in Task 3.3

---

## Step 6: Configure Real-Time Updates

1. Click **"Dashboard Settings"** (gear icon)
2. Configure:
   - **Refresh Rate**: 1000ms (1 second)
   - **Auto-refresh**: Enabled
3. Click **"Save"**

---

## Step 7: Test Dashboard

### Start MQTT Publisher

```bash
# Terminal 1: Start test data publisher
cd fuxa-integration
python3 mqtt-publisher.py
```

### Verify Data Flow

1. Check FUXA dashboard updates in real-time
2. Verify all gauges show values
3. Verify charts update correctly
4. Check for any errors in browser console

### Test Checklist

- [ ] Total Packets gauge displays value
- [ ] Packet Rate gauge displays value
- [ ] Protocol Distribution pie chart shows data
- [ ] Component Traffic bar chart shows data
- [ ] Dashboard refreshes every 1 second
- [ ] No errors in browser console
- [ ] All widgets responsive

---

## Step 8: Save Dashboard Configuration

1. Click **"Project"** menu → **"Export"**
2. Save configuration as `fuxa-dashboard-export.json`
3. Store in `fuxa-integration/` directory

---

## Troubleshooting

### Issue: No Data Displayed

**Solution**:
1. Check MQTT broker is running: `docker ps | grep mosquitto`
2. Check MQTT publisher is running
3. Verify MQTT topics in FUXA device configuration
4. Check browser console for errors

### Issue: Variables Not Found

**Solution**:
1. Verify device is connected in FUXA
2. Check variable names match exactly
3. Verify MQTT topic paths are correct
4. Re-import device configuration

### Issue: Dashboard Not Updating

**Solution**:
1. Check refresh rate is set to 1000ms
2. Verify auto-refresh is enabled
3. Check MQTT connection status
4. Restart FUXA container if needed

---

## Next Steps

After completing Task 3.2:
- **Task 3.3**: Develop custom network topology widget
- **Task 3.4**: Develop custom component health widget
- **Task 4.1**: Comprehensive integration testing

---

## Quick Reference

**FUXA URL**: http://localhost:1881  
**MQTT Broker**: mosquitto:1883  
**Dashboard Name**: VPP Traffic Visualization  
**Widgets**: 6 total (2 gauges, 2 charts, 2 custom)  
**Refresh Rate**: 1 second  
**Grid Layout**: 12 columns

---

## Manual Steps Summary

1. ✅ Access FUXA at http://localhost:1881
2. ✅ Import device configuration
3. ✅ Verify 15 variables configured
4. ✅ Create dashboard "VPP Traffic Visualization"
5. ✅ Add 6 widgets with data bindings
6. ✅ Configure 1-second refresh rate
7. ✅ Test with live MQTT data
8. ✅ Export dashboard configuration

---

## Automation Note

FUXA dashboard creation is primarily a manual UI process. This guide provides step-by-step instructions. For automation, consider using FUXA's REST API (if available) or configuration file import/export.
