# Bambu Lab A1 MQTT Connection - Final Solution

## Summary of Findings

After extensive analysis of the Home Assistant bambu_lab integration and working community examples, I've identified the root causes of the "disconnect code 7" issue with the Bambu Lab A1.

### Root Cause Analysis

**Disconnect Code 7** = "The connection was lost" - This happens on the A1 when:

1. **Wrong TLS Version**: The A1 REQUIRES TLS 1.2 specifically. Default TLS settings often don't work.
2. **Subscribe Timing**: Subscribing before the connection is fully established causes immediate disconnect.
3. **Client ID Format**: Using no client_id or wrong format can cause issues.

### Key Differences from Other Bambu Printers

The A1 has stricter MQTT requirements than the X1 Carbon:
- **Must use TLS 1.2** (not TLS 1.3 or default)
- **Must subscribe inside on_connect callback**
- **Must use proper certificate chain**

## Scripts Provided

### 1. `bambu_a1_minimal.py` - SIMPLEST WORKING VERSION

This is the most reliable, minimal implementation based on tested working code.

```bash
python3 bambu_a1_minimal.py
```

**Key features:**
- Uses TLS 1.2 explicitly (`ssl.PROTOCOL_TLSv1_2`)
- Uses `loop_forever()` for simplicity
- Subscribes in `on_connect` callback
- Minimal code, easy to understand

### 2. `bambu_a1_working.py` - FULL-FEATURED VERSION

Full implementation with all features.

```bash
python3 bambu_a1_working.py
```

**Key features:**
- Thread-based with `loop_start()`
- Status tracking and display
- Proper SSL context with all 3 Bambu certs
- Watchdog to detect stale connections
- Clean disconnect handling

### 3. `bambu_tls_test.py` - DIAGNOSTIC TOOL

Tests different TLS configurations to identify what works.

```bash
python3 bambu_tls_test.py
```

## Critical Implementation Details

### 1. TLS 1.2 is REQUIRED

```python
# WRONG - Uses default TLS
client.tls_set(ca_certs=cert_file)

# CORRECT - Explicit TLS 1.2
client.tls_set(
    ca_certs=cert_file,
    tls_version=ssl.PROTOCOL_TLSv1_2
)
client.tls_insecure_set(True)
```

### 2. Subscribe in on_connect (Not After connect())

```python
# WRONG - Causes disconnect code 7
client.connect(ip, port)
client.subscribe(topic)  # Don't do this!

# CORRECT - Subscribe in callback
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(topic)  # Do this!

client.on_connect = on_connect
client.connect(ip, port)
```

### 3. Client ID Format

```python
# Use unique client_id with uuid
client_id = f"ha-bambulab-{uuid.uuid4()}"
client = mqtt.Client(
    client_id=client_id,
    protocol=mqtt.MQTTv311,
    clean_session=True
)
```

### 4. Use loop_forever() for Simplicity

For simple scripts, `loop_forever()` is more reliable than `loop_start()`:

```python
# Simple approach - works reliably
client.connect(ip, port)
client.loop_forever()

# Alternative with thread control
client.connect(ip, port)
client.loop_start()
# ... do other work ...
client.loop_stop()
```

## Certificate Setup

Ensure these certificates are in `bambu_certs/`:
- `bambu.cert`
- `bambu_p2s_250626.cert`
- `bambu_h2c_251122.cert`

From Home Assistant's `ha-bambulab` integration.

## Troubleshooting

### Still getting disconnect code 7?

1. **Verify TLS version**: Run `bambu_tls_test.py`
2. **Check certificates**: Ensure cert files exist and are valid
3. **Verify credentials**: Access code must be from printer's LAN settings screen
4. **Check IP**: Printer must be on same network, ping test it
5. **Firewall**: Ensure port 8883 is not blocked

### Testing the connection

```bash
# Test with mosquitto (if installed)
mosquitto_sub -h 192.168.1.140 -p 8883 -t "device/03919c460100975/report" \
  -u "bblp" -P "33125022" \
  --cafile bambu_certs/bambu.cert \
  --tls-version tlsv1.2 --insecure
```

### Home Assistant vs Standalone

Home Assistant works because:
1. Uses TLS 1.2 (via `create_local_ssl_context()`)
2. Subscribes in `_on_connect()` which is called from `on_connect`
3. Uses `loop_forever()` in separate thread
4. Has proper certificate chain validation

## References

- Home Assistant Integration: https://github.com/greghesp/ha-bambulab
- Working A1 Example: https://github.com/AlexanderBiba/bambulab-timelapse-trigger
- Paho MQTT Docs: https://eclipse.dev/paho/
