#!/usr/bin/env python3
"""
Manual test of learning capture functionality
"""

import sys
import os

# Add the scripts directory to Python path
scripts_dir = "/home/bamer/.opencode/emergent-learning/scripts"
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

os.chdir(scripts_dir)

# Import the functions directly
from background_learning_capture import (
    capture_from_event_chronicle,
    capture_from_watcher_log,
)

print("Running manual test of learning capture...")

print("\n=== Testing Event Chronicle Capture ===")
capture_from_event_chronicle()

print("\n=== Testing Watcher Log Capture ===")
capture_from_watcher_log()

print("\nDone.")
