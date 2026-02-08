#!/bin/bash
# Cleanup script for Bambu Lab MQTT debugging files
# Run on Pine A64 to remove all temporary/debugging scripts

echo "Cleaning up Bambu Lab debugging files..."

rm -f \
    bambu_a1_definitive.py \
    bambu_tls_test.py \
    check_ha.sh \
    fix_ha3.sh \
    homeassistant \
    setup_working_mqtt.sh \
    bambu_a1_minimal.py \
    check_hacs2.sh \
    check_ha_status.sh \
    fix_hacs_path.sh \
    install_ha.sh \
    test_mqtt_simple.py \
    bambu_a1_mqtt_ssl.py \
    check_hacs.sh \
    EOF \
    fix_ha.sh \
    PYEOF \
    working_mqtt.py \
    bambu_a1_pine.py \
    check_ha_mqtt2.sh \
    extract_mqtt_code.sh \
    fix_mqtt_debug2.sh \
    run_mqtt_test.sh \
    bambu.cert \
    check_ha_mqtt.sh \
    fix_compose.sh \
    fix_mqtt_debug.sh \
    setup_working_mqtt2.sh

echo "Cleanup complete."
ls -la
