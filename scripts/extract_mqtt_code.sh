#!/bin/bash
# Extract working MQTT code from HA Bambulab

echo "=== Reading bambu_client.py ==="
head -100 /home/jo/homeassistant/config/custom_components/bambu_lab/pybambu/bambu_client.py 2>/dev/null || echo "File not found"

echo ""
echo "=== Looking for SSL context creation ==="
grep -A 10 "create_local_ssl_context\|create_insecure_ssl_context" /home/jo/homeassistant/config/custom_components/bambu_lab/pybambu/bambu_client.py 2>/dev/null || echo "Not found in client"

echo ""
echo "=== Checking for certificates ==="
ls -la /home/jo/homeassistant/config/custom_components/bambu_lab/pybambu/*.cert 2>/dev/null || echo "No cert files found"
