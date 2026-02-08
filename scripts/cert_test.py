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

# Bambu CA certificate
BAMBU_CERT = """-----BEGIN CERTIFICATE-----
MIIDZTCCAk2gAwIBAgIUV1FckwXElyek1onFnQ9kL7Bk4N8wDQYJKoZIhvcNAQEL
BQAwQjELMAkGA1UEBhMCQ04xIjAgBgNVBAoMGUJCTCBUZWNobm9sb2dpaWVzIENv
LiwgTHRkMQ8wDQYDVQQDDAZCQkwgQ0EwHhcNMjIwNDA0MDM0MjExWhcNMzIwNDAx
MDM0MjExWjBCMQswCQYDVQQGEwJDTjEiMCAGA1UECgwZQkJMIFRlY2hub2xvZ2ll
cyBDby4sIEx0ZDEPMA0GA1UEAwwGQkJMIENBMIIBIjANBgkqhkiG9w0BAQEFAAOC
AQ8AMIIBCgKCAQEAy96Zw3cRjpOWeq7oIk+HaTNI7vt12rcc9PVGO5m4+LZCHW8u
B6HhHYmEmY3OSyZ4Cbgh8LRGwSbdQa4kXUlaxe+jvQ9lGgQ8mphKNHccEmlcWYg1
Vgnngj3RC6RWXRIUjU2k+Du84L3JxbHxzGv9LzAJLxO4tKqd5oxM2C38+tGsXA6C
S5Ke5+kSl+PuCWwOCJU6BY6UpXT5gvs5zqO2ADrF7ewGCmOhpz9AcFFc0icVPv/l
Rcv0K5mBjcJa0LXURB3kYtEjSt9sdfmzp3XyT9LKI7iKw4yrHQi8nugkmSL6p26M
MFtY0cGYEwUdvWadp8wqMSWHFPU0kKf+CmbljVUCAwEAAaNTMFEwHQYDVR0OBBYE
FI80QmjcZ06PxCKexXxJ5avdRL4eMB8GA1UdIwQYMBaAFI80QmjcZ06PxCKexXxJ
5avdRL4eMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBAAGUhE+W
Xhn4HCtS1odQjfbE88TAi27UzxRdTRhgNd5gKbuo9YeWBC2yinFqn18zJ1XgG9Oh
7btygKjHvsI+y4jUzRTvvrwZtv4n+ibfw1MNQgBHDeqnoehEtDV/CyUVUn9KnU8T
ybgAXTqKPel1+K0T6MXnndXKauYWcG3pGt/giRle+orVqd+VKua5lKq5ckDq/1ms
eorLSMzGzDH4YFM1OdQNj/4Upw9zQzF7/sFGPwL6oCC+7u32wyp5LtRsxCiJH8/I
ZkbOnfEglPPccq8M0ND0fOd4qx2rN1qx1amm9z/qjcEdGIqy9EJO17f6tztYK4jY
NhaW44N6G6R6PQ==
-----END CERTIFICATE-----"""

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

def create_ssl_context():
    """Create SSL context with Bambu CA cert"""
    # Write cert to temp file
    cert_path = "/tmp/bambu_ca.crt"
    with open(cert_path, 'w') as f:
        f.write(BAMBU_CERT)
    
    # Create context
    context = ssl.create_default_context(cafile=cert_path)
    context.check_hostname = False  # IP address mismatch workaround
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT  # Ignore key usage extension error
    return context

def main():
    print("Testing MQTT with Bambu CA certificate...")
    print("=" * 40)
    
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
    context = create_ssl_context()
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
