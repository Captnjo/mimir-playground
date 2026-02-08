#!/usr/bin/env python3
"""
Simple MQTT test for Bambu printer
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

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    if rc == 0:
        print("SUCCESS! Connection established.")
        # Don't subscribe yet, just stay connected
    else:
        print(f"Failed to connect: {rc}")

def on_disconnect(client, userdata, rc):
    print(f"Disconnected with result code {rc}")
    if rc != 0:
        print("Unexpected disconnection")

def on_message(client, userdata, msg):
    print(f"Message received on {msg.topic}")

# Create client with specific settings
client = mqtt.Client(
    client_id="bambu_bridge_test",
    callback_api_version=mqtt.CallbackAPIVersion.VERSION1
)

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# TLS setup
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
client.tls_set_context(context)

# Auth
client.username_pw_set("bblp", PRINTER_ACCESS_CODE)

print("Connecting to printer...")
print(f"IP: {PRINTER_IP}")
print(f"Port: {PRINTER_PORT}")
print(f"Username: bblp")
print(f"Password: {PRINTER_ACCESS_CODE}")

try:
    client.connect(PRINTER_IP, PRINTER_PORT, 60)
    client.loop_start()
    
    # Stay connected for 10 seconds
    time.sleep(10)
    
    if client.is_connected():
        print("\nStill connected after 10 seconds!")
        print("Now trying to subscribe...")
        result, mid = client.subscribe(f"device/{PRINTER_SERIAL}/report")
        print(f"Subscribe result: {result}")
        
        # Wait another 10 seconds
        time.sleep(10)
        
        if client.is_connected():
            print("\nStill connected after subscribe!")
        else:
            print("\nDisconnected after subscribe")
    else:
        print("\nConnection lost within 10 seconds")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    client.loop_stop()
    client.disconnect()
    print("\nTest complete")
