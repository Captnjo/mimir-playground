#!/usr/bin/env python3
import ssl
import paho.mqtt.client as mqtt
import time

print("Starting MQTT test...")

def on_connect(c, u, f, rc):
    print(f"Connected with result: {rc}")

def on_disconnect(c, u, rc):
    print(f"Disconnected: {rc}")

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_disconnect = on_disconnect

# Load certs
ctx = ssl.create_default_context()
ctx.load_verify_locations(cafile="/home/jo/bambu_certs/bambu.cert")
ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
ctx.check_hostname = False

client.tls_set_context(ctx)
client.username_pw_set("bblp", "33125022")

print("Connecting...")
try:
    client.connect("192.168.1.140", 8883, keepalive=5)
    client.loop_start()
    time.sleep(5)
    print("Test complete")
    client.loop_stop()
except Exception as e:
    print(f"Error: {e}")
