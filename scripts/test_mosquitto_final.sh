#!/bin/bash
# Test MQTT with mosquitto_sub - disable hostname verification

CERT_DIR="/tmp/bambu_certs"

if [ ! -f "$CERT_DIR/bambu.crt" ]; then
    echo "Downloading Bambu certificates..."
    mkdir -p $CERT_DIR
    curl -sL "https://raw.githubusercontent.com/greghesp/ha-bambulab/main/custom_components/bambu_lab/pybambu/bambu.cert" -o $CERT_DIR/bambu.crt
fi

echo "Testing with certificate (insecure mode)..."
echo "This should work if the A1 accepts our connection:"
echo ""

# Use --insecure to skip hostname verification but still use the CA cert
mosquitto_sub -h 192.168.1.140 -p 8883 -u bblp -P 33125022 \
    -t "device/03919c460100975/#" \
    --tls-version tlsv1.2 \
    --cafile $CERT_DIR/bambu.crt \
    --insecure \
    -d -k 5
