#!/usr/bin/env python3
"""
Bambu Printer MQTT Bridge - Debug version
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
TOPIC_REQUEST = f"device/{PRINTER_SERIAL}/request"

connected = False
last_ping = 0

def on_connect(client, userdata, flags, rc):
    global connected, last_ping
    if rc == 0:
        print(f"[{datetime.now()}] Connected!")
        connected = True
        last_ping = time.time()
        
        # Subscribe
        result, mid = client.subscribe(TOPIC_REPORT)
        print(f"[{datetime.now()}] Subscribe result: {result}")
        
        # Request status
        payload = json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}})
        client.publish(TOPIC_REQUEST, payload)
        print(f"[{datetime.now()}] Sent pushall request")
    else:
        print(f"[{datetime.now()}] Connection failed: {rc}")
        connected = False

def on_disconnect(client, userdata, rc):
    global connected
    print(f"[{datetime.now()}] Disconnected: {rc}")
    connected = False

def on_message(client, userdata, msg):
    global last_ping
    last_ping = time.time()
    print(f"[{datetime.now()}] Got message on {msg.topic}")
    try:
        data = json.loads(msg.payload.decode())
        # Print just the keys to see structure
        print(f"  Keys: {list(data.keys())}")
        if 'print' in data:
            print(f"  Print state: {data['print'].get('gcode_state', 'unknown')}")
    except Exception as e:
        print(f"  Error parsing: {e}")

def on_publish(client, userdata, mid):
    print(f"[{datetime.now()}] Published message {mid}")

def main():
    print("Bambu MQTT Debug Test")
    print("=" * 40)
    
    client = mqtt.Client(
        client_id=f"bambu_debug_{int(time.time())}",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1
    )
    
    # Enable logging
    client.enable_logger()
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_publish = on_publish
    
    # TLS - no verification for now
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    client.tls_set_context(context)
    
    # Auth
    client.username_pw_set("bblp", PRINTER_ACCESS_CODE)
    
    # Short reconnect delay
    client.reconnect_delay_set(min_delay=1, max_delay=3)
    
    try:
        print(f"Connecting to {PRINTER_IP}:{PRINTER_PORT}...")
        client.connect(PRINTER_IP, PRINTER_PORT, keepalive=5)
        
        print("Running for 60 seconds...")
        start = time.time()
        while time.time() - start < 60:
            client.loop(timeout=1.0)
            
            # Check if we've been disconnected for too long
            if not connected and time.time() - last_ping > 10:
                print(f"[{datetime.now()}] Not connected, waiting...")
                last_ping = time.time()
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        client.disconnect()
        print(f"[{datetime.now()}] Final status: connected={connected}")

if __name__ == "__main__":
    main()
