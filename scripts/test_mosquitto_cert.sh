#!/bin/bash
# Test MQTT with mosquitto_sub using proper certificates

CERT_DIR="/tmp/bambu_certs"
mkdir -p $CERT_DIR

echo "Downloading Bambu certificates..."
curl -sL "https://raw.githubusercontent.com/greghesp/ha-bambulab/main/custom_components/bambu_lab/pybambu/bambu.cert" -o $CERT_DIR/bambu.crt
curl -sL "https://raw.githubusercontent.com/greghesp/ha-bambulab/main/custom_components/bambu_lab/pybambu/bambu_p2s_250626.cert" -o $CERT_DIR/bambu_p2s.crt 2>/dev/null || true
curl -sL "https://raw.githubusercontent.com/greghesp/ha-bambulab/main/custom_components/bambu_lab/pybambu/bambu_h2c_251122.cert" -o $CERT_DIR/bambu_h2c.crt 2>/dev/null || true

echo ""
echo "Testing with certificate..."
mosquitto_sub -h 192.168.1.140 -p 8883 -u bblp -P 33125022 -t "device/03919c460100975/#" --tls-version tlsv1.2 --cafile $CERT_DIR/bambu.crt -d -k 5
