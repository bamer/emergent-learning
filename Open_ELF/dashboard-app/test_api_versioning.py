#!/usr/bin/env python3
"""
Simple test script to verify API versioning works correctly.
"""

import requests
import json
from typing import Dict, Any


def test_api_versioning():
    base_url = "http://localhost:8888"

    # Test both old and new endpoints
    test_cases = [
        ("/api/stats", "old endpoint"),
        ("/api/v1/stats", "new versioned endpoint"),
        ("/api/heuristics", "old heuristics endpoint"),
        ("/api/v1/heuristics", "new versioned heuristics endpoint"),
    ]

    print("Testing API Versioning")
    print("=" * 50)

    for endpoint, description in test_cases:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            status = "✅ PASS" if response.status_code == 200 else "❌ FAIL"
            print(f"{status} {description:30} -> {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ FAIL {description:30} -> Connection Error: {str(e)[:50]}")

    print("\nExpected behavior:")
    print("- Old endpoints (/api/*) should return 404 (backward compatibility broken)")
    print("- New endpoints (/api/v1/*) should return 200 (working)")


if __name__ == "__main__":
    test_api_versioning()
