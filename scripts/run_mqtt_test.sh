#!/bin/bash
# Download and run MQTT test

cd /tmp
curl -O https://raw.githubusercontent.com/Captnjo/mimir-playground/main/scripts/test_mqtt_simple.py
python3 test_mqtt_simple.py
