#!/usr/bin/env python3
"""
Debug script to test timeline integration with the actual dashboard backend
"""

import sys
import os
from pathlib import Path

# Add the dashboard backend to Python path
dashboard_path = Path(__file__).parent.parent.parent / "dashboard-app" / "backend"
sys.path.insert(0, str(dashboard_path))

# Add Open_ELF to Python path
open_elf_path = Path(__file__).parent.parent
sys.path.insert(0, str(open_elf_path))

print(f"Dashboard path: {dashboard_path}")
print(f"Open_ELF path: {open_elf_path}")
print(f"Current sys.path: {sys.path[:5]}...")  # Show first 5 paths

try:
    # Try importing the main module
    import main

    print("✅ Successfully imported main module")

    # Try importing the integration function
    from timeline_dashboard.timeline_integration import integrate_with_dashboard

    print("✅ Successfully imported integrate_with_dashboard")

    # Create a mock app to test integration
    from fastapi import FastAPI

    app = FastAPI()

    # Test the integration
    integrate_with_dashboard(app)
    print("✅ Integration function executed successfully")

    # Check routes
    timeline_routes = [route for route in app.routes if "timeline" in str(route.path)]
    print(f"✅ Added {len(timeline_routes)} timeline routes")
    for route in timeline_routes:
        print(f"  {list(route.methods)[0]} {route.path}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
