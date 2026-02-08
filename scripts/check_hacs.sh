#!/bin/bash
# Check if HACS is installed correctly

echo "=== Checking HACS directory ==="
ls -la ~/homeassistant/config/custom_components/ | grep -i hacs

echo ""
echo "=== HACS files ==="
ls -la ~/homeassistant/config/custom_components/hacs/ 2>/dev/null | head -10 || echo "HACS directory not found"

echo ""
echo "=== Checking HA logs for HACS errors ==="
cd ~/homeassistant
sudo docker compose logs --tail 50 2&>1 | grep -i hacs | head -10 || echo "No HACS mentions in logs"

echo ""
echo "=== Full HA config directory ==="
ls -la ~/homeassistant/config/
