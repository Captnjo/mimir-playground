#!/bin/bash
# Install Home Assistant on Pine A64 - Fixed version

set -e

echo "=== Installing Home Assistant on Pine A64 ==="
echo ""

# Update system
echo "[1/5] Updating system..."
sudo apt-get update

# Install Docker if not present
echo "[2/5] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# Create HA directory
echo "[3/5] Creating Home Assistant directory..."
mkdir -p ~/homeassistant/config

# Create docker-compose file directly in homeassistant folder
echo "[4/5] Creating docker-compose configuration..."
cat > ~/homeassistant/docker-compose.yaml << 'EOF'
version: '3'
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

# Start Home Assistant
echo "[5/5] Starting Home Assistant..."
cd ~/homeassistant
sudo docker compose up -d

echo ""
echo "=== Home Assistant installation complete! ==="
echo ""
echo "Access it at: http://$(hostname -I | awk '{print $1}'):8123"
echo ""
echo "Wait 1-2 minutes for it to fully start."
echo "Then check logs with: cd ~/homeassistant && sudo docker compose logs -f"
