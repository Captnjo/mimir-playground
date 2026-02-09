#!/bin/bash
# OpenClaw Migration Script: root -> jo user
# Run this as root, then switch to jo for final steps

set -e  # Exit on any error

echo "=== OpenClaw Migration: root -> jo ==="
echo ""

# Step 1: Stop services
echo "[1/8] Stopping services..."
systemctl stop mimir-dashboard.service 2>/dev/null || true
pkill -f "openclaw-gateway" 2>/dev/null || true
pkill -f "dashboard_server.py" 2>/dev/null || true
sleep 2

# Step 2: Create jo's .openclaw directory
echo "[2/8] Creating /home/jo/.openclaw..."
mkdir -p /home/jo/.openclaw

# Step 3: Copy workspace (preserve permissions, but we'll fix them after)
echo "[3/8] Copying workspace to /home/jo/.openclaw/..."
cp -a /root/.openclaw/workspace /home/jo/.openclaw/

# Step 4: Fix ownership
echo "[4/8] Setting ownership to jo:jo..."
chown -R jo:jo /home/jo/.openclaw

# Step 5: Update systemd service
echo "[5/8] Updating systemd service..."
cat > /etc/systemd/system/mimir-dashboard.service << 'EOF'
[Unit]
Description=Mimir Dashboard Web Server
After=network.target

[Service]
Type=simple
User=jo
WorkingDirectory=/home/jo/.openclaw/workspace
ExecStart=/usr/bin/python3 /home/jo/.openclaw/workspace/scripts/dashboard_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

# Step 6: Create backup of root's version
echo "[6/8] Backing up root's version..."
mv /root/.openclaw /root/.openclaw.backup.$(date +%Y%m%d)

# Step 7: Create symlink for compatibility (optional)
echo "[7/8] Creating symlink..."
ln -s /home/jo/.openclaw /root/.openclaw

# Step 8: Start dashboard as jo
echo "[8/8] Starting dashboard service..."
systemctl start mimir-dashboard.service
systemctl enable mimir-dashboard.service

echo ""
echo "=== Migration Complete ==="
echo ""
echo "Next steps (run as user 'jo'):"
echo ""
echo "1. Switch to jo user:"
echo "   sudo su - jo"
echo ""
echo "2. Start OpenClaw gateway:"
echo "   cd ~/.openclaw/workspace"
echo "   openclaw gateway start"
echo ""
echo "3. Verify dashboard:"
echo "   curl http://localhost:8080"
echo ""
echo "4. Check services:"
echo "   sudo systemctl status mimir-dashboard.service"
echo ""
echo "Rollback (if needed):"
echo "   sudo rm -rf /home/jo/.openclaw"
echo "   sudo mv /root/.openclaw.backup.YYYYMMDD /root/.openclaw"
echo "   sudo rm /root/.openclaw  # remove symlink"
echo ""
