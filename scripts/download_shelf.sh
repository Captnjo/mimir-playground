#!/bin/bash
# Download monitor shelf STL

mkdir -p ~/3d_models
cd ~/3d_models

echo "Downloading Adjustable Monitor Shelf..."

# Try to download from Printables
# The direct download URL format for Printables
curl -L -o monitor_shelf.stl "https://www.printables.com/model/675840-adjustable-monitor-shelf-fits-any-display-curved-b/files" 2>/dev/null || echo "Direct download failed, will need manual download"

# Check if file was downloaded
if [ -f "monitor_shelf.stl" ] && [ -s "monitor_shelf.stl" ]; then
    echo "Downloaded successfully!"
    ls -lh monitor_shelf.stl
else
    echo ""
    echo "=== Manual download required ==="
    echo "Go to: https://www.printables.com/model/675840-adjustable-monitor-shelf-fits-any-display-curved-b"
    echo "Click 'Download' and save the STL file to ~/3d_models/"
    echo ""
    echo "Alternative: Use the Printables mobile app to send directly to Bambu Studio"
fi
