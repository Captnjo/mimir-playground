#!/usr/bin/env python3
"""
Bambu Printer MQTT Bridge for Pine A64
Relays MQTT between printer and Tailscale network
"""

import json
import ssl
import sys
import time
import threading
from datetime import datetime

import paho.mqtt.client as mqtt

# Configuration
PRINTER_IP = "192.168.1.140"
PRINTER_SERIAL = "03919c460100975"
PRINTER_ACCESS_CODE = "33125022"  # From LAN Only Mode
PRINTER_PORT = 8883

# Topics
TOPIC_REPORT = f"device/{PRINTER_SERIAL}/report"
TOPIC_REQUEST = f"device/{PRINTER_SERIAL}/request"

# Status file for VPS to read
STATUS_FILE = "/tmp/printer_status.json"


class PrinterBridge:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.status = {}
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[{datetime.now()}] Connected to printer")
            self.connected = True
            result, mid = client.subscribe(TOPIC_REPORT)
            print(f"[{datetime.now()}] Subscribe result: {result}")
        else:
            print(f"[{datetime.now()}] Connection failed: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        print(f"[{datetime.now()}] Disconnected from printer")
        self.connected = False
    
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            self.status.update(data)
            
            # Save status to file for other processes to read
            with open(STATUS_FILE, 'w') as f:
                json.dump(self.status, f, indent=2)
                
        except json.JSONDecodeError:
            pass
    
    def connect(self):
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        # TLS setup (Bambu uses self-signed certs)
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.client.tls_insecure_set(True)
        
        # Auth (bblp as username, access code as password for local LAN mode)
        self.client.username_pw_set("bblp", PRINTER_ACCESS_CODE)
        
        try:
            self.client.connect(PRINTER_IP, PRINTER_PORT, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"[{datetime.now()}] Failed to connect: {e}")
            return False
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
    
    def get_status(self):
        """Get current printer status."""
        print_data = self.status.get("print", {})
        return {
            "connected": self.connected,
            "timestamp": datetime.now().isoformat(),
            "state": print_data.get("gcode_state", "unknown"),
            "progress": print_data.get("mc_percent", 0),
            "time_remaining": print_data.get("mc_remaining_time", 0),
            "layer": print_data.get("layer_num", 0),
            "total_layers": print_data.get("total_layer_num", 0),
            "bed_temp": print_data.get("bed_temper", 0),
            "nozzle_temp": print_data.get("nozzle_temper", 0),
            "filename": print_data.get("gcode_file", "unknown"),
        }
    
    def send_command(self, command):
        """Send a command to the printer."""
        if not self.connected:
            return False
        payload = json.dumps({"print": command})
        self.client.publish(TOPIC_REQUEST, payload)
        return True


def main():
    print("Bambu Printer MQTT Bridge")
    print("=" * 40)
    
    bridge = PrinterBridge()
    
    if not bridge.connect():
        print("Failed to connect to printer. Retrying in 10 seconds...")
        time.sleep(10)
        if not bridge.connect():
            print("Failed to connect. Exiting.")
            sys.exit(1)
    
    print("Bridge running. Press Ctrl+C to stop.")
    print(f"Status file: {STATUS_FILE}")
    
    try:
        while True:
            # Print status every 30 seconds
            status = bridge.get_status()
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                  f"State: {status['state']} | "
                  f"Progress: {status['progress']}% | "
                  f"Connected: {status['connected']}", end='', flush=True)
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        bridge.disconnect()


if __name__ == "__main__":
    main()
