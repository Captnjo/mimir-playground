#!/bin/bash
# Fix docker-compose.yaml - remove obsolete version attribute

cd ~/homeassistant

# Create fixed docker-compose.yaml without version
cat > docker-compose.yaml << 'EOF'
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

echo "Fixed docker-compose.yaml"
cat docker-compose.yaml
