# disk_cleanup.sh - Automated disk cleanup script
#!/bin/bash

# This script cleans up temporary and log files to free disk space
# Usage: disk_cleanup.sh --force [include paths]

set -e

# Function to delete files safely
safe_delete() {
    local path="$1"
    if [ ! -d "$path" ]; then
        echo "[WARN] $path is not a directory, skipping"
        return
    fi
    
    # Delete temporary files
    find "$path" -type f -name "*.tmp" -delete
    find "$path" -type f -name "*.log" -delete
    find "$path" -type f -name "*.cache" -delete
    find "$path" -type f -name "*.db" -delete
    
    # Clean up Docker-related files if present
    if [ -d "/var/lib/docker" ]; then
        docker system prune -f -u
    fi
    
    echo "✓ Cleaned: $path"
}

# Parse arguments
force=true
include_paths="/tmp /var/log /home/bamer/.opencode/emergent-learning"

if [ "$1" != "--force" ]; then
    echo "Usage: $0 --force [include paths]"
    echo "  include paths: /tmp, /var/log, /home/bamer/.opencode/emergent-learning"
    exit 1
fi

# Set include paths if not provided
: ${!include_paths}

# Execute cleanup
for path in "$include_paths"; do
    if [ -d "$path" ]; then
        safe_delete "$path"
    fi
done

echo "Disk cleanup completed. Current usage: $(df -h / | awk '{print $2}')%"