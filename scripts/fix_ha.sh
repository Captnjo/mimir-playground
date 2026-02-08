#!/bin/bash
# Fix Home Assistant container

cd ~/homeassistant

echo "Stopping and removing old container..."
sudo docker stop homeassistant 2>/dev/null || true
sudo docker rm homeassistant 2>/dev/null || true

echo "Starting fresh..."
sudo docker compose up -d

echo ""
echo "Checking status..."
sudo docker compose ps

echo ""
echo "Recent logs:"
sudo docker compose logs --tail 20
