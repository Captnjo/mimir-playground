#!/bin/bash
# Check how HA Bambulab is connecting to MQTT

echo "=== Checking HA Bambulab configuration ==="
cat ~/homeassistant/config/.storage/core.config_entries 2>/dev/null | grep -A 20 "bambu" | head -30 || echo "Config not found"

echo ""
echo "=== HA logs for Bambulab ==="
cd ~/homeassistant
sudo docker compose logs --tail 50 2&>1 | grep -i "bambu\|mqtt" | head -20 || echo "No relevant logs"

echo ""
echo "=== Checking if we can extract working MQTT settings ==="
ls -la ~/homeassistant/config/custom_components/bambu_lab/
