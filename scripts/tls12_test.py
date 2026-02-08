#!/usr/bin/env python3
"""
Bambu Printer MQTT Bridge - Using TLS 1.2 like mosquitto_sub example
"""

import json
import ssl
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt

# Configuration
PRINTER_IP = "192.168.1.140"
PRINTER_SERIAL = "03919c460100975"
PRINTER_ACCESS_CODE = "33125022"
PRINTER_PORT = 8883

# Try wildcard topic like mosquitto_sub example
TOPIC_REPORT = f"device/{PRINTER_SERIAL}/report"
# Also try just the device topic
TOPIC_WILDCARD = f"device/{PRINTER_SERIAL}/#"

connected = False

def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        print(f"[{datetime.now()}] Connected!")
        connected = True
        
        # Subscribe to wildcard topic
        result, mid = client.subscribe(TOPIC_WILDCARD)
        print(f"[{datetime.now()}] Subscribe to {TOPIC_WILDCARD} result: {result}")
    else:
        print(f"[{datetime.now()}] Connection failed: {rc}")
        connected = False

def on_disconnect(client, userdata, rc):
    global connected
    print(f"[{datetime.now()}] Disconnected: {rc}")
    connected = False

def on_message(client, userdata, msg):
    print(f"[{datetime.now()}] Got message on {msg.topic}")
    try:
        data = json.loads(msg.payload.decode())
        print(f"  Keys: {list(data.keys())}")
    except Exception as e:
        print(f"  Raw: {msg.payload[:100]}")

def main():
    print("Bambu MQTT Test - TLS 1.2 with wildcard topic")
    print("=" * 40)
    
    client = mqtt.Client(
        client_id=f"bambu_tls12_{int(time.time())}",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1
    )
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    # TLS 1.2 setup like mosquitto_sub --tls-version tlsv1.2 --insecure
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)  # Force TLS 1.2
    context.check_hostname = False  # --insecure equivalent
    context.verify_mode = ssl.CERT_NONE  # Don't verify cert
    client.tls_set_context(context)
    
    # Auth
    client.username_pw_set("bblp", PRINTER_ACCESS_CODE)
    
    client.reconnect_delay_set(min_delay=1, max_delay=3)
    
    try:
        print(f"Connecting to {PRINTER_IP}:{PRINTER_PORT} with TLS 1.2...")
        client.connect(PRINTER_IP, PRINTER_PORT, keepalive=5)
        
        print("Running... Press Ctrl+C to stop")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
