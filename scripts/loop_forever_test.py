#!/usr/bin/env python3
"""
Bambu Printer MQTT Bridge - Using loop_forever like HA integration
"""

import json
import ssl
import sys
import time
import threading
from datetime import datetime

import paho.mqtt.client as mqtt

# Configuration
PRINTER_IP = "192.168.1.140"
PRINTER_SERIAL = "03919c460100975"
PRINTER_ACCESS_CODE = "33125022"
PRINTER_PORT = 8883

# Topics
TOPIC_REPORT = f"device/{PRINTER_SERIAL}/report"
TOPIC_REQUEST = f"device/{PRINTER_SERIAL}/request"

# Status file for VPS to read
STATUS_FILE = "/tmp/printer_status.json"

connected = False
status = {}

def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        print(f"[{datetime.now()}] Connected!")
        connected = True
        client.subscribe(TOPIC_REPORT)
        print(f"[{datetime.now()}] Subscribed")
        # Request status
        payload = json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}})
        client.publish(TOPIC_REQUEST, payload)
    else:
        print(f"[{datetime.now()}] Failed: {rc}")
        connected = False

def on_disconnect(client, userdata, rc):
    global connected
    print(f"[{datetime.now()}] Disconnected: {rc}")
    connected = False

def on_message(client, userdata, msg):
    global status
    print(f"[{datetime.now()}] Got message!")
    try:
        data = json.loads(msg.payload.decode())
        status.update(data)
        print(json.dumps(data, indent=2)[:1000])
        # Save to file
        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=2)
    except Exception as e:
        print(f"Error: {e}")

# Create client with MQTTv311 like HA
def create_client():
    client = mqtt.Client(
        client_id=f"bambu_test_{int(time.time())}",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1
    )
    client.reconnect_delay_set(min_delay=1, max_delay=5)
    
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
    
    return client

def main():
    print("Testing MQTT with loop_forever...")
    print("=" * 40)
    
    client = create_client()
    
    try:
        print(f"Connecting to {PRINTER_IP}:{PRINTER_PORT}...")
        # Use keepalive=5 like HA
        client.connect(PRINTER_IP, PRINTER_PORT, keepalive=5)
        print("Starting loop_forever...")
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
        client.disconnect()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
