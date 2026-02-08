#!/usr/bin/env python3
"""
Bambu Printer MQTT Bridge - With proper SSL certificates
"""

import json
import ssl
import sys
import time
import os
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

# Status file
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
        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=2)
    except Exception as e:
        print(f"Error: {e}")

def download_cert():
    """Download Bambu CA certificate from HA integration"""
    import urllib.request
    url = "https://raw.githubusercontent.com/greghesp/ha-bambulab/main/custom_components/bambu_lab/pybambu/bambu.cert"
    cert_path = "/tmp/bambu_ca.crt"
    try:
        urllib.request.urlretrieve(url, cert_path)
        print(f"Downloaded cert to {cert_path}")
        return cert_path
    except Exception as e:
        print(f"Failed to download cert: {e}")
        return None

def create_ssl_context(cert_path):
    """Create SSL context with Bambu CA cert"""
    context = ssl.create_default_context(cafile=cert_path)
    context.check_hostname = False  # IP address mismatch workaround
    # Ignore "CA cert does not include key usage extension" error
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return context

def main():
    print("Testing MQTT with Bambu CA certificate...")
    print("=" * 40)
    
    # Download cert
    cert_path = download_cert()
    if not cert_path:
        print("Failed to get certificate")
        return
    
    client = mqtt.Client(
        client_id=f"bambu_test_{int(time.time())}",
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1
    )
    client.reconnect_delay_set(min_delay=1, max_delay=5)
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    # TLS with Bambu CA cert
    try:
        context = create_ssl_context(cert_path)
        client.tls_set_context(context)
    except Exception as e:
        print(f"SSL context error: {e}")
        print("Falling back to no verification...")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        client.tls_set_context(context)
    
    # Auth
    client.username_pw_set("bblp", PRINTER_ACCESS_CODE)
    
    try:
        print(f"Connecting to {PRINTER_IP}:{PRINTER_PORT}...")
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
