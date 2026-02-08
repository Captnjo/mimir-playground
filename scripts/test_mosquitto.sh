#!/bin/bash
# Test MQTT with mosquitto_sub like the working example

echo "Installing mosquitto clients..."
sudo apt-get update && sudo apt-get install -y mosquitto-clients

echo ""
echo "Testing connection with mosquitto_sub..."
echo "This should show raw MQTT messages if it works:"
echo ""

# Try the exact command from the blog post
mosquitto_sub -h 192.168.1.140 -p 8883 -u bblp -P 33125022 -t "device/03919c460100975/#" --tls-version tlsv1.2 --insecure -d
