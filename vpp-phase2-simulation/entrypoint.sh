#!/bin/bash

# Get NODE_TYPE from environment, default to 'master'
NODE_TYPE=${NODE_TYPE:-master}

# Map NODE_TYPE to app file
case $NODE_TYPE in
  master)
    python3 app_coordinator.py
    ;;
  generation)
    python3 app_power_generation.py
    ;;
  storage)
    python3 app_battery_system.py
    ;;
  demand)
    python3 app_load_manager.py
    ;;
  *)
    echo "Unknown NODE_TYPE: $NODE_TYPE"
    python3 app_coordinator.py
    ;;
esac
