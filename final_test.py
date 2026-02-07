#!/usr/bin/env python3
"""
Final test of learning capture functionality
"""

import sys
import os

# Add the scripts directory to Python path
scripts_dir = "/home/bamer/.opencode/emergent-learning/scripts"
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

os.chdir(scripts_dir)

# Import the functions directly
import background_learning_capture as bg_capture

print("Running final test of learning capture functionality...")

print("\n=== Testing Event Chronicle Capture ===")
bg_capture.capture_from_event_chronicle()

print("\n=== Testing Watcher Log Capture ===")
bg_capture.capture_from_watcher_log()

print("\nDone.")
