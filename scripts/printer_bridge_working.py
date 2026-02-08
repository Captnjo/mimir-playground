#!/usr/bin/env python3
"""
Working Bambu Printer MQTT Bridge
Uses proper SSL certificates like Home Assistant
"""

import json
import ssl
import os
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt

# Configuration
PRINTER_IP = "192.168.1.140"
PRINTER_SERIAL = "03919c460100975"
PRINTER_ACCESS_CODE = "33125022"
PRINTER_PORT = 8883
TOPIC_REPORT = f"device/{PRINTER_SERIAL}/report"
TOPIC_REQUEST = f"device/{PRINTER_SERIAL}/request"
STATUS_FILE = "/tmp/printer_status.json"

# Find certificate
def find_cert():
    paths = [
        "/tmp/bambu.cert",
        "/root/bambu_certs/bambu.cert",
        "/home/jo/bambu_certs/bambu.cert",
        "/home/jo/homeassistant/config/custom_components/bambu_lab/pybambu/bambu.cert"
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("bambu.cert not found")

CERT_FILE = find_cert()
print(f"Using certificate: {CERT_FILE}")

class PrinterBridge:
    def __init__(self):
        self.client = mqtt.Client(
            client_id=f"mimir_bridge_{int(time.time())}",
            protocol=mqtt.MQTTv311
        )
        self.status = {}
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[{datetime.now()}] Connected to printer!")
            self.connected = True
            result, mid = client.subscribe(TOPIC_REPORT)
            print(f"[{datetime.now()}] Subscribed to {TOPIC_REPORT}")
            # Request full status
            self.request_status()
        else:
            print(f"[{datetime.now()}] Connection failed: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        print(f"[{datetime.now()}] Disconnected: {rc}")
        self.connected = False
    
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            self.status.update(data)
            # Save to file
            with open(STATUS_FILE, 'w') as f:
                json.dump(self.status, f, indent=2)
            # Print status update
            if 'print' in data:
                state = data['print'].get('gcode_state', 'unknown')
                progress = data['print'].get('mc_percent', 0)
                print(f"[{datetime.now()}] State: {state} | Progress: {progress}%")
        except Exception as e:
            pass
    
    def request_status(self):
        payload = json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}})
        self.client.publish(TOPIC_REQUEST, payload)
        print(f"[{datetime.now()}] Requested status update")
    
    def connect(self):
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        # Setup TLS with proper certificates (like HA)
        ctx = ssl.create_default_context()
        ctx.load_verify_locations(cafile=CERT_FILE)
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        ctx.check_hostname = False
        self.client.tls_set_context(ctx)
        
        # Auth
        self.client.username_pw_set("bblp", PRINTER_ACCESS_CODE)
        
        # Connect
        print(f"[{datetime.now()}] Connecting to {PRINTER_IP}:{PRINTER_PORT}...")
        self.client.connect(PRINTER_IP, PRINTER_PORT, keepalive=5)
        self.client.loop_start()
        return True
    
    def run(self):
        try:
            while True:
                if not self.connected:
                    print(f"[{datetime.now()}] Waiting for connection...")
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.client.loop_stop()
            self.client.disconnect()

def main():
    print("Bambu Printer MQTT Bridge")
    print("=" * 40)
    
    bridge = PrinterBridge()
    if not bridge.connect():
        print("Failed to connect")
        return
    
    bridge.run()

if __name__ == "__main__":
    main()
