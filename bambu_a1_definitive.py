#!/usr/bin/env python3
"""
Bambu Lab A1 - DEFINITIVE MINIMAL WORKING SCRIPT

This is a direct adaptation of the working implementation from:
https://github.com/AlexanderBiba/bambulab-timelapse-trigger

Tested and confirmed working on Bambu Lab A1.

The KEY insight for A1: TLS 1.2 is REQUIRED
"""

import json
import ssl
import signal
import sys
import paho.mqtt.client as mqtt

# ==================== CONFIGURATION ====================
PRINTER_IP = "192.168.1.140"
PRINTER_PORT = 8883
PRINTER_SERIAL = "03919c460100975"
ACCESS_CODE = "33125022"
CERT_FILE = "/root/.openclaw/workspace/bambu_certs/bambu.cert"
# ======================================================

TOPIC_REPORT = f"device/{PRINTER_SERIAL}/report"
TOPIC_REQUEST = f"device/{PRINTER_SERIAL}/request"


def on_connect(client, userdata, flags, rc):
    """Called when connected - subscribe here!"""
    if rc == 0:
        print("[MQTT] Connected successfully!")
        # CRITICAL: Subscribe inside on_connect callback
        client.subscribe(TOPIC_REPORT)
        print(f"[MQTT] Subscribed to {TOPIC_REPORT}")
    else:
        print(f"[MQTT] Connection failed: {rc}")


def on_disconnect(client, userdata, rc):
    """Called when disconnected"""
    if rc == 0:
        print("[MQTT] Disconnected cleanly")
    else:
        print(f"[MQTT] Disconnected with error: {rc}")


def on_message(client, userdata, msg):
    """Called when message received"""
    try:
        payload = json.loads(msg.payload.decode())
        
        # Print print status
        if 'print' in payload:
            p = payload['print']
            state = p.get('gcode_state', 'unknown')
            progress = p.get('mc_percent', 0)
            layer = p.get('layer_num', 0)
            total_layers = p.get('total_layer_num', 0)
            bed_temp = p.get('bed_temper', 0)
            nozzle_temp = p.get('nozzle_temper', 0)
            
            print(f"[STATUS] State: {state} | Progress: {progress}% | "
                  f"Layer: {layer}/{total_layers} | "
                  f"Bed: {bed_temp}°C | Nozzle: {nozzle_temp}°C")
            
    except Exception as e:
        print(f"[ERROR] Failed to parse message: {e}")


def shutdown(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n[EXIT] Shutting down...")
    client.disconnect()
    client.loop_stop()
    sys.exit(0)


# Set up signal handlers
signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

print("=" * 70)
print("Bambu Lab A1 - DEFINITIVE MINIMAL WORKING SCRIPT")
print("=" * 70)
print(f"Printer: {PRINTER_IP}:{PRINTER_PORT}")
print(f"Serial: {PRINTER_SERIAL}")
print(f"Cert: {CERT_FILE}")
print()

# Create MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Set authentication
client.username_pw_set("bblp", ACCESS_CODE)

# Set up TLS with TLS 1.2 - THIS IS THE CRITICAL PART FOR A1
print("[SETUP] Configuring TLS 1.2...")
client.tls_set(
    ca_certs=CERT_FILE,
    tls_version=ssl.PROTOCOL_TLSv1_2  # CRITICAL: A1 requires TLS 1.2
)
client.tls_insecure_set(True)  # Don't verify hostname (cert doesn't match IP)

# Connect to printer
print(f"[CONNECT] Connecting to {PRINTER_IP}:{PRINTER_PORT}...")
client.connect(PRINTER_IP, PRINTER_PORT, keepalive=60)

# Start the loop - blocks forever, handles reconnection
print("[MQTT] Connected! Monitoring printer (Ctrl+C to exit)...")
print()
client.loop_forever()
