#!/bin/bash
# Install Home Assistant on Pine A64

set -e

echo "=== Installing Home Assistant on Pine A64 ==="
echo ""

# Update system
echo "[1/6] Updating system..."
sudo apt-get update

# Install dependencies
echo "[2/6] Installing dependencies..."
sudo apt-get install -y \
    jq \
    curl \
    avahi-daemon \
    dbus \
    apparmor-utils

# Install Docker if not present
echo "[3/6] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "Docker installed. You may need to log out and back in."
fi

# Create HA directory
echo "[4/6] Creating Home Assistant directory..."
mkdir -p ~/homeassistant/config
mkdir -p ~/homeassistant/docker

# Create docker-compose file
echo "[5/6] Creating docker-compose configuration..."
cat > ~/homeassistant/docker/docker-compose.yaml << 'EOF'
version: '3'
services:
  homeassistant:
    container_name: homeassistant
    image: "ghcr.io/home-assistant/home-assistant:stable"
    volumes:
      - ~/homeassistant/config:/config
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro
    restart: unless-stopped
    privileged: true
    network_mode: host
EOF

# Start Home Assistant
echo "[6/6] Starting Home Assistant..."
cd ~/homeassistant/docker
sudo docker compose up -d

echo ""
echo "=== Home Assistant installation complete! ==="
echo ""
echo "Access it at: http://$(hostname -I | awk '{print $1}'):8123"
echo ""
echo "Wait 1-2 minutes for it to fully start."
echo "Then run: cd ~/homeassistant/docker && sudo docker compose logs -f"
