#!/usr/bin/env python3
"""Test script to verify monitoring endpoints are registered"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from routers.monitoring import router
from fastapi import FastAPI

# Create test app
app = FastAPI()
app.include_router(router, prefix="/api/v1")

# Print all routes
for route in app.routes:
    if hasattr(route, "path"):
        print(f"Route: {route.methods} {route.path}")
