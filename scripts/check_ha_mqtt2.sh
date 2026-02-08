#!/bin/bash
# Check HA Bambulab MQTT connection details

echo "=== Checking Bambulab integration location ==="
ls -la /home/jo/homeassistant/config/custom_components/ 2>/dev/null | grep bambu || echo "Not in jo's home"
ls -la ~/homeassistant/config/custom_components/ 2>/dev/null | grep bambu || echo "Not in current home"

echo ""
echo "=== Looking for MQTT connection code ==="
find /home/jo/homeassistant/config/custom_components -name "*.py" -path "*bambu*" 2>/dev/null | head -5 || echo "Not found"

echo ""
echo "=== HA config entries ==="
cat /home/jo/homeassistant/config/.storage/core.config_entries 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(json.dumps(e,indent=2)) for e in d.get('data',{}).get('entries',[]) if 'bambu' in str(e).lower()]" 2>/dev/null || echo "Could not parse config"
