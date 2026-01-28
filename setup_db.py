#!/usr/bin/env python3
import asyncio
import sys
import os
from pathlib import Path

# Add the query directory to path
sys.path.append("/home/bamer/.opencode/emergent-learning/query")

from models import initialize_database, create_tables


async def create_missing_tables():
    try:
        print("Creating database tables...")
        db = await initialize_database()
        await create_tables()
        print("✓ Database tables: SUCCESS")

        # Check database file size
        db_path = Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print(f"✓ Database file: {size_mb:.2f}MB")
        else:
            print("! Database file not found")

        await db.close()
        return True

    except Exception as e:
        print(f"✗ Database creation FAILED: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(create_missing_tables())
    sys.exit(0 if success else 1)
