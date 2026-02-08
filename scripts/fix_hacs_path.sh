#!/bin/bash
# Fix HACS installation path

echo "=== Current situation ==="
echo "HA config is at: /home/jo/homeassistant/config"
echo "HACS was installed at: /root/homeassistant/config (WRONG)"

echo ""
echo "=== Moving HACS to correct location ==="
# Create custom_components in the right place
mkdir -p /home/jo/homeassistant/config/custom_components

# Copy HACS from wrong location to right location
if [ -d "/root/homeassistant/config/custom_components/hacs" ]; then
    sudo cp -r /root/homeassistant/config/custom_components/hacs /home/jo/homeassistant/config/custom_components/
    echo "HACS copied to correct location"
else
    echo "HACS not found in wrong location, will reinstall..."
    cd /home/jo/homeassistant
    sudo docker exec -it homeassistant bash -c "wget -O - https://get.hacs.xyz | bash -"
fi

echo ""
echo "=== Fixing permissions ==="
sudo chown -R 1000:1000 /home/jo/homeassistant/config/custom_components

echo ""
echo "=== Verifying ==="
ls -la /home/jo/homeassistant/config/custom_components/

echo ""
echo "=== Restarting HA ==="
cd /home/jo/homeassistant
sudo docker compose restart

echo ""
echo "Done! Wait 60 seconds and refresh your browser."
