#!/usr/bin/env python3
"""
Bambu Printer MQTT Bridge - Test without pushall
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

# Topics
TOPIC_REPORT = f"device/{PRINTER_SERIAL}/report"

connected = False

def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        print(f"[{datetime.now()}] Connected!")
        connected = True
        
        # Subscribe ONLY - don't send anything
        result, mid = client.subscribe(TOPIC_REPORT)
        print(f"[{datetime.now()}] Subscribe result: {result}")
        print(f"[{datetime.now()}] Waiting for messages...")
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
        print(f"  Data: {json.dumps(data, indent=2)[:500]}")
    except Exception as e:
        print(f"  Raw: {msg.payload[:200]}")

def main():
    print("Bambu MQTT Test - Subscribe Only")
    print("=" * 40)
    
    client = mqtt.Client(
        client_id=f"bambu_sub_{int(time.time())}",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1
    )
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    # TLS
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    client.tls_set_context(context)
    
    # Auth
    client.username_pw_set("bblp", PRINTER_ACCESS_CODE)
    
    client.reconnect_delay_set(min_delay=1, max_delay=3)
    
    try:
        print(f"Connecting to {PRINTER_IP}:{PRINTER_PORT}...")
        client.connect(PRINTER_IP, PRINTER_PORT, keepalive=5)
        
        print("Running for 30 seconds (subscribe only)...")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
