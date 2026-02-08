#!/usr/bin/env python3
"""
MINIMAL working MQTT client for Bambu Lab A1

This is the simplest possible working implementation.
Based on the working example from:
https://github.com/AlexanderBiba/bambulab-timelapse-trigger

REQUIREMENTS FOR A1:
- TLS 1.2 (ssl.PROTOCOL_TLSv1_2)
- Subscribe AFTER connect, handled by loop_forever()
- Username: "bblp"
- Password: Access code from printer screen

Usage:
    python3 bambu_a1_minimal.py
"""

import json
import ssl
import sys
import signal
import paho.mqtt.client as mqtt

# Configuration
PRINTER_IP = "192.168.1.140"
PRINTER_PORT = 8883
PRINTER_SERIAL = "03919c460100975"
ACCESS_CODE = "33125022"
CERT_FILE = "/root/.openclaw/workspace/bambu_certs/bambu.cert"

TOPIC_REPORT = f"device/{PRINTER_SERIAL}/report"
TOPIC_REQUEST = f"device/{PRINTER_SERIAL}/request"

connected = False


def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        print("[MQTT] Connected!")
        connected = True
        # Subscribe inside on_connect - CRITICAL for A1
        client.subscribe(TOPIC_REPORT)
        print(f"[MQTT] Subscribed to {TOPIC_REPORT}")
    else:
        print(f"[MQTT] Connection failed: {rc}")


def on_disconnect(client, userdata, rc):
    global connected
    if rc == 0:
        print("[MQTT] Disconnected cleanly")
    else:
        print(f"[MQTT] Disconnected with error: {rc}")
    connected = False


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        
        # Print status updates
        if 'print' in payload:
            p = payload['print']
            state = p.get('gcode_state', 'unknown')
            progress = p.get('mc_percent', 0)
            layer = p.get('layer_num', 0)
            print(f"[STATUS] State: {state}, Progress: {progress}%, Layer: {layer}")
            
    except Exception as e:
        print(f"[ERROR] {e}")


def handle_exit(sig, frame):
    print("\n[EXIT] Shutting down...")
    client.disconnect()
    client.loop_stop()
    sys.exit(0)


# Set up signal handlers
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

print("=" * 60)
print("Bambu Lab A1 MQTT - Minimal Working Example")
print("=" * 60)
print()

# Create client
client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Set credentials
client.username_pw_set("bblp", ACCESS_CODE)

# Set up TLS with TLS 1.2 - CRITICAL for A1
print(f"[SETUP] Using TLS 1.2 with cert: {CERT_FILE}")
client.tls_set(
    ca_certs=CERT_FILE,
    tls_version=ssl.PROTOCOL_TLSv1_2
)
client.tls_insecure_set(True)  # Don't verify hostname

# Connect
print(f"[CONNECT] Connecting to {PRINTER_IP}:{PRINTER_PORT}...")
client.connect(PRINTER_IP, PRINTER_PORT, keepalive=60)

# Use loop_forever() - blocks until disconnect
# This is the simplest approach and works reliably
print("[MQTT] Starting message loop (Ctrl+C to exit)...")
print()
client.loop_forever()
