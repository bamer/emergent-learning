#!/usr/bin/env python3
"""
Integration test for Timeline Dashboard with FastAPI
"""

import sys
from pathlib import Path

# Add Open_ELF to Python path
open_elf_path = Path(__file__).parent.parent
sys.path.insert(0, str(open_elf_path))

from fastapi import FastAPI
import uvicorn


def create_test_app():
    """Create a test FastAPI app with timeline integration"""
    app = FastAPI(title="Timeline Dashboard Integration Test")

    # Import and integrate timeline dashboard
    try:
        from timeline_dashboard.demo_integration import integrate_with_dashboard

        integrate_with_dashboard(app)
        print("✅ Timeline dashboard integrated successfully!")
    except ImportError as e:
        print(f"❌ Failed to integrate timeline dashboard: {e}")
        return None

    @app.get("/")
    async def root():
        return {"message": "Timeline Dashboard Integration Test"}

    return app


if __name__ == "__main__":
    app = create_test_app()
    if app:
        print("\n🚀 Starting test server...")
        print("🔧 Available endpoints:")
        for route in app.routes:
            if hasattr(route, "methods"):
                print(f"   {list(route.methods)[0]} {route.path}")

        print("\n📋 Test the endpoints:")
        print("   http://localhost:8000/api/v1/timeline/events")
        print("   http://localhost:8000/api/v1/timeline/stats")
        print("   http://localhost:8000/api/v1/timeline/recent")
        print("   http://localhost:8000/api/v1/timeline/event-types")
        print("\n💡 Press Ctrl+C to stop the server")

        uvicorn.run(app, host="127.0.0.1", port=8000)
    else:
        print("❌ Failed to create test app")
        sys.exit(1)
