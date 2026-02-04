#!/usr/bin/env python3
"""
Learning Processor Daemon - Converts raw learnings to heuristics
Continuously monitors learnings table and processes new entries
"""

import sqlite3
import time
import json
import re
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/home/bamer/.opencode/emergent-learning/memory/index.db")
LOG_FILE = Path("/home/bamer/.opencode/emergent-learning/logs/learning-processor.log")

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")

def get_db_connection():
    try:
        conn = sqlite3.connect(str(DB_PATH))
        return conn
    except Exception as e:
        log(f"DB connection failed: {e}")
        return None

def extract_heuristic_from_learning(title, summary, learning_type):
    """Extract heuristic rule from learning content"""
    # Look for pattern indicators
    indicators = ["should", "always", "never", "must", "avoid", "prefer", "recommend"]
    
    content_str = (str(title) + " " + str(summary)).lower()
    
    # Simple heuristic extraction
    for indicator in indicators:
        if indicator in content_str:
            # Extract sentence containing the indicator
            sentences = re.split(r'[.!?]+', content_str)
            for sentence in sentences:
                if indicator in sentence and len(sentence.strip()) > 10:
                    return sentence.strip().capitalize()
    
    # Fallback: use title
    return f"{title}" if title else "Pattern detected in system behavior"

def process_unprocessed_learnings():
    """Process learnings that haven't been converted to heuristics"""
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        
        # Get recent learnings that might not be in heuristics
        cursor.execute("""
            SELECT id, type, title, summary, domain, created_at 
            FROM learnings 
            WHERE created_at > datetime('now', '-1 day')
            ORDER BY created_at ASC
            LIMIT 20
        """)
        
        learnings = cursor.fetchall()
        processed_count = 0
        
        for learning in learnings:
            learning_id, learning_type, title, summary, domain, created_at = learning
            
            # Extract heuristic
            rule = extract_heuristic_from_learning(title, summary, learning_type)
            explanation = f"Auto-extracted from {learning_type} learning: {title}"
            confidence = 0.7 if learning_type == "success" else 0.5
            
            # Check if already exists
            cursor.execute("SELECT id FROM heuristics WHERE rule = ?", (rule,))
            if cursor.fetchone():
                log(f"⚠️ Skipping duplicate heuristic: {rule[:50]}...")
                continue
            
            # Insert into heuristics table
            try:
                cursor.execute("""
                    INSERT INTO heuristics 
                    (domain, rule, explanation, confidence, source_type, source_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (domain or "general", rule, explanation, confidence, learning_type, learning_id, created_at))
                
                conn.commit()
                processed_count += 1
                log(f"✅ Converted learning {learning_id} to heuristic: {rule[:50]}...")
                
            except sqlite3.IntegrityError:
                # Duplicate rule, skip
                log(f"⚠️ Skipping duplicate learning {learning_id}")
                continue
            except Exception as e:
                log(f"❌ Failed to convert learning {learning_id}: {e}")
        
        conn.close()
        return processed_count
        
    except Exception as e:
        log(f"❌ Database error: {e}")
        if conn:
            conn.close()
        return 0

def main():
    """Main daemon loop"""
    log("🚀 Learning Processor Daemon Starting")
    
    while True:
        try:
            processed = process_unprocessed_learnings()
            if processed > 0:
                log(f"📊 Processed {processed} learnings")
            else:
                log("💤 No new learnings to process")
                
            # Wait 60 seconds before next check
            time.sleep(60)
            
        except KeyboardInterrupt:
            log("👋 Shutdown requested")
            break
        except Exception as e:
            log(f"❌ Unexpected error: {e}")
            time.sleep(60)  # Wait longer on error

if __name__ == "__main__":
    main()
