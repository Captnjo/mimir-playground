#!/usr/bin/env python3
"""
TLS Version Test for Bambu Lab A1

Tests different TLS configurations to identify what works with the A1.
This helps diagnose connection issues.
"""

import json
import ssl
import sys
import time
import paho.mqtt.client as mqtt

# Configuration
PRINTER_IP = "192.168.1.140"
PRINTER_PORT = 8883
PRINTER_SERIAL = "03919c460100975"
ACCESS_CODE = "33125022"
CERT_FILE = "/root/.openclaw/workspace/bambu_certs/bambu.cert"

TOPIC_REPORT = f"device/{PRINTER_SERIAL}/report"


def test_connection(name, tls_version=None, use_ssl_context=False):
    """Test a specific TLS configuration"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    
    results = {
        'connected': False,
        'disconnected': False,
        'disconnect_rc': None,
        'messages': 0
    }
    
    client = mqtt.Client()
    
    def on_connect(c, u, f, rc):
        if rc == 0:
            results['connected'] = True
            print(f"  [OK] Connected!")
            c.subscribe(TOPIC_REPORT)
        else:
            print(f"  [FAIL] Connection failed: {rc}")
    
    def on_disconnect(c, u, rc):
        results['disconnected'] = True
        results['disconnect_rc'] = rc
        if rc != 0:
            print(f"  [FAIL] Disconnected: {rc}")
    
    def on_message(c, u, m):
        results['messages'] += 1
        if results['messages'] == 1:
            print(f"  [OK] First message received!")
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.username_pw_set("bblp", ACCESS_CODE)
    
    try:
        if use_ssl_context:
            # Test with SSLContext
            context = ssl.create_default_context()
            if tls_version:
                context.minimum_version = tls_version
                context.maximum_version = tls_version
            context.load_verify_locations(cafile=CERT_FILE)
            context.check_hostname = False
            context.verify_flags &= ~ssl.VERIFY_X509_STRICT
            client.tls_set_context(context)
            print(f"  Using SSLContext")
        else:
            # Test with tls_set
            if tls_version:
                client.tls_set(
                    ca_certs=CERT_FILE,
                    tls_version=tls_version
                )
                print(f"  Using tls_set with {tls_version}")
            else:
                client.tls_set(ca_certs=CERT_FILE)
                print(f"  Using tls_set (default)")
            client.tls_insecure_set(True)
        
        print(f"  Connecting to {PRINTER_IP}:{PRINTER_PORT}...")
        client.connect(PRINTER_IP, PRINTER_PORT, keepalive=5)
        client.loop_start()
        
        # Wait for connection and messages
        time.sleep(5)
        
        client.loop_stop()
        client.disconnect()
        
        # Evaluate results
        print(f"\n  Results:")
        print(f"    Connected: {results['connected']}")
        print(f"    Disconnected: {results['disconnected']} (rc={results['disconnect_rc']})")
        print(f"    Messages: {results['messages']}")
        
        if results['connected'] and not results['disconnected'] and results['messages'] > 0:
            print(f"  Status: ✓ SUCCESS")
            return True
        elif results['disconnected'] and results['disconnect_rc'] == 7:
            print(f"  Status: ✗ FAILED - Disconnect code 7 (TLS/subscription issue)")
            return False
        else:
            print(f"  Status: ✗ FAILED")
            return False
            
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


def main():
    print("=" * 60)
    print("Bambu Lab A1 - TLS Version Diagnostic")
    print("=" * 60)
    print()
    print(f"Printer: {PRINTER_IP}:{PRINTER_PORT}")
    print(f"Serial: {PRINTER_SERIAL}")
    print()
    
    results = []
    
    # Test 1: Default TLS (may use TLS 1.3)
    try:
        results.append(("Default TLS", test_connection(
            "Default TLS (tls_set default)",
            tls_version=None
        )))
    except Exception as e:
        print(f"Test error: {e}")
        results.append(("Default TLS", False))
    
    time.sleep(1)
    
    # Test 2: TLS 1.2 (working version)
    try:
        results.append(("TLS 1.2", test_connection(
            "TLS 1.2 (ssl.PROTOCOL_TLSv1_2)",
            tls_version=ssl.PROTOCOL_TLSv1_2
        )))
    except Exception as e:
        print(f"Test error: {e}")
        results.append(("TLS 1.2", False))
    
    time.sleep(1)
    
    # Test 3: TLS 1.3 (if supported)
    try:
        results.append(("TLS 1.3", test_connection(
            "TLS 1.3 (ssl.TLSVersion.TLSv1_3)",
            use_ssl_context=True,
            tls_version=ssl.TLSVersion.TLSv1_3
        )))
    except Exception as e:
        print(f"\n  [SKIP] TLS 1.3 not supported by this Python version")
        results.append(("TLS 1.3", False))
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for name, success in results:
        status = "✓ WORKS" if success else "✗ FAILS"
        print(f"  {status}: {name}")
    
    print()
    print("RECOMMENDATION:")
    if any(r[1] for r in results):
        working = [r[0] for r in results if r[1]]
        print(f"  Use: {working[0]}")
    else:
        print("  All tests failed. Check:")
        print("    - Printer IP address")
        print("    - Access code")
        print("    - Network connectivity")
        print("    - Certificate file exists")


if __name__ == "__main__":
    main()
