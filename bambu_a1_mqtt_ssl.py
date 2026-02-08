#!/usr/bin/env python3
"""
Bambu Lab A1 - Using mqtt.ssl module
"""

import json
import signal
import sys
import paho.mqtt.client as mqtt

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
            print(f"[STATUS] State: {p.get('gcode_state')}, Progress: {p.get('mc_percent')}%")
    except:
        pass


signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

print("Bambu Lab A1 MQTT - Using mqtt.ssl")

client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.username_pw_set("bblp", ACCESS_CODE)

# Use mqtt.ssl.PROTOCOL_TLSv1_2 as in the working example
print("[SETUP] Using mqtt.ssl.PROTOCOL_TLSv1_2")
client.tls_set(
    ca_certs=CERT_FILE,
    tls_version=mqtt.ssl.PROTOCOL_TLSv1_2
)
client.tls_insecure_set(True)

print(f"[SETUP] Connecting to {PRINTER_IP}:{PRINTER_PORT}...")
client.connect(PRINTER_IP, PRINTER_PORT, keepalive=60)
print("[SETUP] Starting loop...")
client.loop_forever()
