#!/bin/bash
# Fix Home Assistant - ensure docker-compose.yaml exists

cd ~

# Create directory structure
mkdir -p ~/homeassistant/config

# Create docker-compose.yaml in the right place
cat > ~/homeassistant/docker-compose.yaml << 'EOF'
services:
  homeassistant:
    container_name: homeassistant
    image: "ghcr.io/home-assistant/home-assistant:stable"
    volumes:
      - /home/jo/homeassistant/config:/config
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro
    restart: unless-stopped
    privileged: true
    network_mode: host
EOF

cd ~/homeassistant

echo "=== Fixing Home Assistant ==="
echo ""

# Stop and remove any existing containers
echo "Stopping old containers..."
sudo docker stop homeassistant 2>/dev/null || true
sudo docker rm homeassistant 2>/dev/null || true

echo ""
echo "Starting Home Assistant..."
sudo docker compose up -d

echo ""
echo "Waiting 10 seconds for startup..."
sleep 10

echo ""
echo "Container status:"
sudo docker ps | grep homeassistant || echo "Container not running"

echo ""
echo "Recent logs:"
sudo docker compose logs --tail 30 2>&1 || echo "No logs available"

echo ""
echo "=== Done ==="
echo "Access HA at: http://$(hostname -I | awk '{print $1}'):8123"
