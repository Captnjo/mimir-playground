#!/usr/bin/env python3
import ssl
import paho.mqtt.client as mqtt
import time
import os

print("Starting MQTT test...")

# Check current directory and list files
print(f"Current directory: {os.getcwd()}")
print(f"Files in /tmp: {os.listdir('/tmp')}")

# Try to find cert
cert_paths = [
    "/tmp/bambu.cert",
    "/root/bambu_certs/bambu.cert",
    "/home/jo/homeassistant/config/custom_components/bambu_lab/pybambu/bambu.cert"
]

cert_file = None
for path in cert_paths:
    exists = os.path.exists(path)
    print(f"Checking {path}: {exists}")
    if exists:
        cert_file = path
        break

if not cert_file:
    print("Certificate not found in any location!")
    exit(1)

print(f"Using certificate: {cert_file}")

def on_connect(c, u, f, rc):
    print(f"Connected with result: {rc}")

def on_disconnect(c, u, rc):
    print(f"Disconnected: {rc}")

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_disconnect = on_disconnect

ctx = ssl.create_default_context()
ctx.load_verify_locations(cafile=cert_file)
ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
ctx.check_hostname = False

client.tls_set_context(ctx)
client.username_pw_set("bblp", "33125022")

print("Connecting to 192.168.1.140:8883...")
try:
    client.connect("192.168.1.140", 8883, keepalive=5)
    client.loop_start()
    time.sleep(5)
    print("Test complete")
    client.loop_stop()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
