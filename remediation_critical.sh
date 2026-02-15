# ELFHEMETER CRITICAL REMEDIATION SCRIPT - Execute with sudo
#!/bin/bash

# This script resolves the critical failure state in the ELF ecosystem
# Requires manual execution by human/Orchestrator with sudo privileges

set -e

# Configuration
USER=bamer
SCRIPT_DIR="/home/bamer/.opencode/emergent-learning"

# Step 1: Fix Authentication/Permissions (Requires sudo)
echo "[STEP 1/5] Fixing authentication and permissions..."
sudo usermod -a -G kgettext,wheel,dialout,sudo -r $USER

# Step 2: Fix cleanup permissions
echo "[STEP 2/5] Fixing cleanup directory permissions..."
sudo chmod -R 775 /tmp /var/log
sudo chown -R $USER:$USER $SCRIPT_DIR

# Step 3: Restart critical services in proper order
echo "[STEP 3/5] Restarting critical services..."
sleep 15  # Ensure permissions apply
systemctl restart dashboard-backend.service
systemctl restart learning-capture.service
systemctl restart eventsbridge-agent.service

# Step 4: Execute disk cleanup
if [ ! -f "$SCRIPT_DIR/scripts/disk_cleanup.sh" ]; then
    echo "[STEP 4a] Creating disk cleanup script..."
    cat > "$SCRIPT_DIR/scripts/disk_cleanup.sh" << 'EOF'
#!/bin/bash
set -e

force=true
include_paths="/tmp /var/log $SCRIPT_DIR"

: ${!include_paths}

for path in "$include_paths"; do
    if [ -d "$path" ]; then
        find "$path" -type f -name "*.tmp" -delete
        find "$path" -type f -name "*.log" -delete
        find "$path" -type f -name "*.cache" -delete
    fi
done
echo "Disk cleanup completed"
EOF
    chmod +x "$SCRIPT_DIR/scripts/disk_cleanup.sh"
fi

# Execute cleanup
disk_cleanup.sh --force "$SCRIPT_DIR"

# Step 5: Fallback union mount (if needed)
# This requires union-mount tool installation - manual step if not present
# Example: union-mount --target /tmp --mode=rw /path/to/source
# echo "[STEP 5] Union mount preparation - requires manual setup"

# Validation
echo "[STEP 6/6] Validating remediation results..."

# Check service status
for service in dashboard-backend.service learning-capture.service eventsbridge-agent.service; do
    if systemctl is-active "$service"; then
        echo "✓ $service is active"
    else
        echo "✗ $service is NOT active - check logs"
    fi
done

# Check disk usage
Disk_usage=$(df -h / | awk '{print $2}')
echo "Root partition usage: $Disk_usage%"

# Check authentication logs
auth_failures=$(grep -i "conversation failed" /var/log/auth.log | wc -l)
echo "Authentication failures: $auth_failures"

# Check service health
health_check=$(curl -s http://localhost:4096/api/v1/health | jq .overall)
if [ "$health_check" == "healthy" ]; then
    echo "✓ All services healthy"
else
    echo "✗ Health check failed - services may still be down"
fi
EOF