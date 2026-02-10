#!/usr/bin/env python3
"""
Rebuild a corrupted SQLite database by dumping and restoring.

This fixes issues like "Rowid out of order" btree corruption.
Usage:
    python rebuild_corrupted_db.py
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

def get_db_path():
    """Get the database path."""
    return Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"

def rebuild_database():
    """Rebuild the database to fix corruption."""
    db_path = get_db_path()
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return False
    
    print(f"Database path: {db_path}")
    print(f"Database size: {db_path.stat().st_size / (1024*1024):.2f} MB")
    
    # Create backup
    backup_path = db_path.with_suffix(f".db.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    print(f"\n1. Creating backup at: {backup_path}")
    shutil.copy2(db_path, backup_path)
    print("   ✓ Backup created")
    
    # Connect to corrupted database
    print("\n2. Connecting to corrupted database...")
    conn_src = sqlite3.connect(str(db_path))
    conn_src.row_factory = sqlite3.Row
    
    # Get list of tables
    cursor = conn_src.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"   Found {len(tables)} tables")
    
    # Create new database
    new_db_path = db_path.with_suffix('.db.new')
    print(f"\n3. Creating new database at: {new_db_path}")
    
    if new_db_path.exists():
        new_db_path.unlink()
    
    conn_dst = sqlite3.connect(str(new_db_path))
    conn_dst.row_factory = sqlite3.Row
    cursor_dst = conn_dst.cursor()
    
    # Copy schema and data
    total_rows = 0
    failed_tables = []
    
    for i, table in enumerate(tables, 1):
        try:
            # Get schema
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
            schema = cursor.fetchone()[0]
            
            # Create table in new database
            cursor_dst.execute(schema)
            
            # Copy data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if rows:
                # Get column names
                columns = [description[0] for description in cursor.description]
                placeholders = ','.join(['?' for _ in columns])
                
                # Insert data
                cursor_dst.executemany(
                    f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                    rows
                )
                total_rows += len(rows)
            
            print(f"   {i}/{len(tables)} ✓ {table} ({len(rows)} rows)")
            
        except Exception as e:
            print(f"   {i}/{len(tables)} ✗ {table} - ERROR: {e}")
            failed_tables.append((table, str(e)))
    
    # Copy indexes
    print("\n4. Copying indexes...")
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
    indexes = cursor.fetchall()
    
    for idx, (sql,) in enumerate(indexes, 1):
        try:
            cursor_dst.execute(sql)
            print(f"   {idx}/{len(indexes)} ✓ Index created")
        except Exception as e:
            print(f"   {idx}/{len(indexes)} ✗ Index failed: {e}")
    
    # Commit and close
    conn_dst.commit()
    conn_dst.close()
    conn_src.close()
    
    print(f"\n5. Data migration complete: {total_rows} rows copied")
    
    if failed_tables:
        print(f"\n   ⚠️  {len(failed_tables)} tables failed:")
        for table, error in failed_tables:
            print(f"      - {table}: {error}")
    
    # Verify new database integrity
    print("\n6. Verifying new database integrity...")
    conn_verify = sqlite3.connect(str(new_db_path))
    cursor_verify = conn_verify.cursor()
    cursor_verify.execute("PRAGMA integrity_check")
    results = cursor_verify.fetchall()
    conn_verify.close()
    
    is_valid = all(row[0] == "ok" for row in results)
    
    if is_valid:
        print("   ✓ New database integrity OK")
        
        # Replace old database with new one
        print(f"\n7. Replacing old database...")
        db_path.rename(db_path.with_suffix('.db.corrupted'))
        new_db_path.rename(db_path)
        print("   ✓ Database replaced successfully")
        print(f"\n   Old corrupted database saved as: {db_path.with_suffix('.db.corrupted')}")
        print(f"   Backup saved as: {backup_path}")
        
        return True
    else:
        print("   ✗ New database still has integrity issues!")
        print(f"   Errors: {results}")
        new_db_path.unlink()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("SQLite Database Rebuild Tool")
    print("=" * 60)
    
    success = rebuild_database()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Database rebuild completed successfully!")
    else:
        print("✗ Database rebuild failed!")
    print("=" * 60)
