#!/usr/bin/env python3
"""
Demo: Backend Integration for Timeline Dashboard

This script demonstrates how to integrate the timeline dashboard components
with an existing FastAPI application.
"""

from fastapi import FastAPI
import sys
from pathlib import Path

# Add the timeline dashboard to Python path
sys.path.append(str(Path(__file__).parent))

# Import the timeline router
from timeline_api import router as timeline_router


def create_demo_app():
    """Create a demo FastAPI app with timeline integration"""
    app = FastAPI(
        title="ELF Dashboard Demo",
        description="Demonstration of Event Chronicle integration with dashboard",
        version="1.0.0",
    )

    # Include the timeline router
    app.include_router(timeline_router)

    @app.get("/")
    async def root():
        return {
            "message": "ELF Dashboard Demo with Timeline Integration",
            "endpoints": [
                "GET /api/v1/timeline/events - Get timeline events",
                "GET /api/v1/timeline/stats - Get timeline statistics",
                "GET /api/v1/timeline/recent - Get recent events",
                "GET /api/v1/timeline/event-types - Get available event types",
            ],
        }

    return app


# For testing the integration
if __name__ == "__main__":
    import uvicorn

    app = create_demo_app()

    print("Starting demo server...")
    print("Access the API documentation at: http://localhost:8000/docs")
    print("Try the timeline endpoints:")
    print("  http://localhost:8000/api/v1/timeline/events")
    print("  http://localhost:8000/api/v1/timeline/stats")
    print("  http://localhost:8000/api/v1/timeline/recent")
    print("  http://localhost:8000/api/v1/timeline/event-types")

    uvicorn.run(app, host="127.0.0.1", port=8000)
