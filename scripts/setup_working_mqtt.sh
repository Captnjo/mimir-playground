#!/bin/bash
# Find and copy Bambu certificates

echo "=== Finding certificate files ==="
find /home/jo/homeassistant/config/custom_components/bambu_lab -name "*.cert" -o -name "*.crt" 2>/dev/null

echo ""
echo "=== Copying certificates to working directory ==="
mkdir -p ~/bambu_certs
cp /home/jo/homeassistant/config/custom_components/bambu_lab/pybambu/*.cert ~/bambu_certs/ 2>/dev/null || echo "No cert files found in pybambu"

echo ""
echo "=== Creating working MQTT script with proper SSL ==="
cat > ~/working_mqtt.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
Working MQTT script based on HA Bambulab integration
"""

import json
import ssl
import sys
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt

# Config
PRINTER_IP = "192.168.1.140"
PRINTER_SERIAL = "03919c460100975"
PRINTER_ACCESS_CODE = "33125022"
PRINTER_PORT = 8883
TOPIC_REPORT = f"device/{PRINTER_SERIAL}/report"
TOPIC_REQUEST = f"device/{PRINTER_SERIAL}/request"

# Certificate paths
CERT_DIR = "/home/jo/bambu_certs"

def create_local_ssl_context():
    """Create SSL context with Bambu CA certs like HA does"""
    import os
    context = ssl.create_default_context()
    for filename in ("bambu.cert", "bambu_p2s_250626.cert", "bambu_h2c_251122.cert"):
        path = os.path.join(CERT_DIR, filename)
        if os.path.exists(path):
            context.load_verify_locations(cafile=path)
            print(f"Loaded cert: {filename}")
    
    # Ignore "CA cert does not include key usage extension" error
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    # Workaround for IP address mismatch
    context.check_hostname = False
    return context

connected = False

def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        print(f"[{datetime.now()}] Connected!")
        connected = True
        client.subscribe(f"device/{PRINTER_SERIAL}/report")
        print(f"[{datetime.now()}] Subscribed")
    else:
        print(f"[{datetime.now()}] Failed: {rc}")

def on_disconnect(client, userdata, rc):
    global connected
    print(f"[{datetime.now()}] Disconnected: {rc}")
    connected = False

def on_message(client, userdata, msg):
    print(f"[{datetime.now()}] Message on {msg.topic}")
    try:
        data = json.loads(msg.payload.decode())
        print(f"  Keys: {list(data.keys())}")
    except:
        pass

# Setup client
client = mqtt.Client(
    client_id=f"mimir_{int(time.time())}",
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION1
)

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Setup TLS like HA does
context = create_local_ssl_context()
client.tls_set_context(context)

# Auth
client.username_pw_set("bblp", PRINTER_ACCESS_CODE)

# Connect
print(f"Connecting to {PRINTER_IP}:{PRINTER_PORT}...")
client.connect(PRINTER_IP, PRINTER_PORT, keepalive=5)

print("Running... Press Ctrl+C to stop")
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\nStopping...")
    client.disconnect()
PYTHON_EOF

chmod +x ~/working_mqtt.py
echo ""
echo "=== Created ~/working_mqtt.py ==="
echo "Run with: python3 ~/working_mqtt.py"
