#!/bin/bash
# Check Home Assistant status

echo "=== Docker container status ==="
sudo docker ps | grep homeassistant

echo ""
echo "=== Recent logs ==="
cd ~/homeassistant
sudo docker compose logs --tail 20 2&>1 | tail -20

echo ""
echo "=== Checking if port 8123 is responding ==="
curl -s --connect-timeout 3 http://localhost:8123/auth/providers 2>/dev/null | head -1 || echo "Not responding yet"
