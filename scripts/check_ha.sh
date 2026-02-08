#!/bin/bash
# Check and open firewall for Home Assistant

echo "=== Checking firewall status ==="
sudo ufw status 2>/dev/null || echo "UFW not installed or not active"

echo ""
echo "=== Checking if port 8123 is listening ==="
sudo ss -tlnp | grep 8123 || echo "Port 8123 not found in listening state"

echo ""
echo "=== Home Assistant container status ==="
sudo docker ps | grep homeassistant

echo ""
echo "=== Opening port 8123 in firewall ==="
sudo ufw allow 8123/tcp 2>/dev/null || echo "UFW not available, trying iptables..."
sudo iptables -I INPUT -p tcp --dport 8123 -j ACCEPT 2>/dev/null || true

echo ""
echo "=== Testing local access ==="
curl -s http://localhost:8123/auth/providers 2>&1 | head -1

echo ""
echo "=== Network interfaces ==="
ip addr show | grep "inet " | head -3
