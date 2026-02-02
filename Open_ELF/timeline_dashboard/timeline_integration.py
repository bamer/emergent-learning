"""
Timeline Dashboard Integration Module

This module provides integration functionality for the timeline dashboard components
with the existing dashboard backend.
"""


def integrate_with_dashboard(app):
    """
    Integrate timeline dashboard components with existing FastAPI app.

    Args:
        app: FastAPI application instance
    """
    try:
        from timeline_dashboard.timeline_api import router as timeline_router

        app.include_router(timeline_router)
        print("Timeline dashboard integration mounted successfully!")
        print("Available endpoints:")
        print("  GET /api/v1/timeline/events - Get timeline events")
        print("  GET /api/v1/timeline/stats - Get timeline statistics")
        print("  GET /api/v1/timeline/recent - Get recent events")
        print("  GET /api/v1/timeline/event-types - Get available event types")
    except ImportError as e:
        print(f"Warning: Could not integrate timeline dashboard: {e}")
        print("Make sure Open_ELF is in the Python path")


if __name__ == "__main__":
    print("Timeline Dashboard Integration")
    print("===============================")
    print()
    print("To integrate with your dashboard:")
    print("1. Import the integration function in your main.py")
    print("2. Call integrate_with_dashboard(app) during startup")
    print()
    print("The integration will add these endpoints:")
    print("  GET /api/v1/timeline/events")
    print("  GET /api/v1/timeline/stats")
    print("  GET /api/v1/timeline/recent")
    print("  GET /api/v1/timeline/event-types")
