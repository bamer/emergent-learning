#!/usr/bin/env python3

import sys
import os

# Change directory
os.chdir('/home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator')
sys.path.insert(0, '/home/bamer/.opencode/emergent-learning/Open_ELF')
sys.path.insert(0, '/home/bamer/.opencode/emergent-learning/Open_ELF/orchestrator')

print("Testing Unified Orchestrator import...")

try:
    from unified_orchestrator import UnifiedOrchestrator
    print("✅ Import successful")
    
    orchestrator = UnifiedOrchestrator()
    print("✅ Unified Orchestrator created")
    
    print("🚀 Starting orchestrator...")
    orchestrator.start()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
