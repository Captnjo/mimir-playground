#!/bin/bash
# Check HACS installation status

echo "=== Checking HACS location ==="
ls -la /home/jo/homeassistant/config/custom_components/ 2>/dev/null || echo "custom_components not found"

echo ""
echo "=== HACS directory contents ==="
ls -la /home/jo/homeassistant/config/custom_components/hacs/ 2>/dev/null | head -10 || echo "HACS not found"

echo ""
echo "=== HA logs for HACS ==="
cd /home/jo/homeassistant
sudo docker compose logs --tail 30 2&>1 | grep -i "hacs\|error\|warning" | head -10 || echo "No relevant logs"

echo ""
echo "=== Checking if HACS is in configuration ==="
grep -r "hacs" /home/jo/homeassistant/config/.storage/ 2>/dev/null | head -5 || echo "HACS not in storage yet"
