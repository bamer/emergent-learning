#!/bin/bash
# Self-Test Script for Emergent Learning Framework (Fixed Version)
# Purpose: Meta-learning - can the system detect its own bugs?

# Change to the emergent-learning directory to ensure proper path resolution
cd "$(dirname "${BASH_SOURCE[0]}")/.." || { echo "Error: Cannot change to ELF directory"; exit 1; }

# Now run the original self-test script
exec ./scripts/self-test.sh