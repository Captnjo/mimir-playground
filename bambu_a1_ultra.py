#!/usr/bin/env python3
"""
Bambu Lab A1 - Ultra minimal working script

Based exactly on https://github.com/AlexanderBiba/bambulab-timelapse-trigger
which is confirmed working on A1.
"""

import json
import ssl
import signal
import sys
import paho.mqtt.client as mqtt

# Configuration
PRINTER_IP = "192.168.1.140"
PRINTER_PORT = 8883
PRINTER_SERIAL = "03919c460100975"
ACCESS_CODE = "33125022"
CERT_FILE = "bambu.cert"

TOPIC_REPORT = f"device/{PRINTER_SERIAL}/report"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Connected!")
        client.subscribe(TOPIC_REPORT)
        print(f"[MQTT] Subscribed to {TOPIC_REPORT}")
    else:
        print(f"[MQTT] Connection failed: {rc}")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"[MQTT] Disconnected with error: {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if 'print' in payload:
            p = payload['print']
            state = p.get('gcode_state', 'unknown')
            progress = p.get('mc_percent', 0)
            print(f"[STATUS] State: {state}, Progress: {progress}%")
    except Exception as e:
        print(f"[ERROR] {e}")


def shutdown(signum, frame):
    print("\n[EXIT] Shutting down...")
    client.disconnect()
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

print("Bambu Lab A1 MQTT Client")
print(f"Connecting to {PRINTER_IP}:{PRINTER_PORT}")

# Create client - NO client_id specified (let paho generate one)
client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Set credentials
client.username_pw_set("bblp", ACCESS_CODE)

# Set up TLS 1.2 with tls_insecure_set BEFORE tls_set
client.tls_insecure_set(True)
client.tls_set(
    ca_certs=CERT_FILE,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

# Connect and loop
print("Connecting...")
client.connect(PRINTER_IP, PRINTER_PORT, keepalive=60)
print("Starting loop (Ctrl+C to exit)...")
client.loop_forever()
