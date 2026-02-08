#!/usr/bin/env python3
"""
Minimal Bambu MQTT test - just maintain connection
"""

import json
import ssl
import sys
import time
import paho.mqtt.client as mqtt

PRINTER_IP = "192.168.1.140"
PRINTER_ACCESS_CODE = "33125022"
PRINTER_SERIAL = "03919c460100975"
PRINTER_PORT = 8883
TOPIC_REPORT = f"device/{PRINTER_SERIAL}/report"

connected = False

def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        print(f"[{time.time()}] Connected!")
        connected = True
        # Subscribe only, don't request anything yet
        client.subscribe(TOPIC_REPORT)
        print(f"[{time.time()}] Subscribed")
    else:
        print(f"[{time.time()}] Failed: {rc}")
        connected = False

def on_disconnect(client, userdata, rc):
    global connected
    print(f"[{time.time()}] Disconnected: {rc}")
    connected = False

def on_message(client, userdata, msg):
    print(f"[{time.time()}] Got message: {msg.topic}")
    try:
        data = json.loads(msg.payload.decode())
        print(json.dumps(data, indent=2)[:500])  # Print first 500 chars
    except:
        print(msg.payload[:200])

client = mqtt.Client(
    client_id="bambu_test_minimal",
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

# Connect with longer keepalive
print("Connecting...")
client.connect(PRINTER_IP, PRINTER_PORT, keepalive=60)

client.loop_start()

# Wait and see
print("Waiting 30 seconds...")
time.sleep(30)

if connected:
    print("Still connected!")
else:
    print("Connection lost")

client.loop_stop()
client.disconnect()
