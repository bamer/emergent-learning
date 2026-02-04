#!/usr/bin/env python3
"""Restore knowledge from markdown files to databases"""

import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path('/home/bamer/.opencode/emergent-learning')
MEMORY_DIR = BASE_DIR / 'memory'

def restore_heuristics():
    """Restore heuristics from markdown files"""
    print("📚 Restoring heuristics...")
    conn = sqlite3.connect(MEMORY_DIR / 'building.db')
    cursor = conn.cursor()
    
    heuristics_dir = MEMORY_DIR / 'heuristics'
    restored_count = 0
    
    for md_file in sorted(heuristics_dir.glob('*.md')):
        domain = md_file.stem
        
        with open(md_file, 'r') as f:
            content = f.read()
        
        # Extract content - split by double newlines for multiple entries
        entries = content.split('\n\n')
        
        for entry in entries:
            entry = entry.strip()
            if entry and len(entry) > 10:
                # Clean markdown formatting
                lines = entry.split('\n')
                rule_content = ' '.join([
                    l.lstrip('#').lstrip('-').lstrip('*').lstrip('>').strip() 
                    for l in lines if l.strip()
                ])
                
                if rule_content and len(rule_content) > 5:
                    try:
                        cursor.execute('''
                            INSERT INTO heuristics (rule, domain, source, confidence, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (rule_content, domain, str(md_file), 0.5, datetime.now()))
                        restored_count += 1
                    except sqlite3.IntegrityError:
                        # Already exists
                        pass
    
    conn.commit()
    conn.close()
    return restored_count

def restore_failures():
    """Restore failures from markdown files"""
    print("📋 Restoring failures...")
    conn = sqlite3.connect(MEMORY_DIR / 'building.db')
    cursor = conn.cursor()
    
    failures_dir = MEMORY_DIR / 'failures'
    restored_count = 0
    
    for md_file in sorted(failures_dir.glob('*.md')):
        with open(md_file, 'r') as f:
            content = f.read()
        
        # Extract title from filename
        name = md_file.stem
        
        # Extract severity from filename if present
        severity = 'medium'
        if 'critical' in name.lower():
            severity = 'critical'
        elif 'low' in name.lower():
            severity = 'low'
        
        cursor.execute('''
            INSERT INTO failures (title, description, domain, severity, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, content, 'general', severity, datetime.now()))
        restored_count += 1
    
    conn.commit()
    conn.close()
    return restored_count

def restore_successes():
    """Restore successes from markdown files"""
    print("🏆 Restoring successes...")
    conn = sqlite3.connect(MEMORY_DIR / 'building.db')
    cursor = conn.cursor()
    
    successes_dir = MEMORY_DIR / 'successes'
    restored_count = 0
    
    for md_file in sorted(successes_dir.glob('*.md')):
        with open(md_file, 'r') as f:
            content = f.read()
        
        # Extract name from filename
        name = md_file.stem
        
        cursor.execute('''
            INSERT INTO successes (title, description, created_at)
            VALUES (?, ?, ?)
        ''', (name, content, datetime.now()))
        restored_count += 1
    
    conn.commit()
    conn.close()
    return restored_count

def restore_golden_rules():
    """Restore golden rules from markdown"""
    print("⭐ Restoring golden rules...")
    conn = sqlite3.connect(MEMORY_DIR / 'building.db')
    cursor = conn.cursor()
    
    golden_rules_file = MEMORY_DIR / 'golden-rules.md'
    restored_count = 0
    
    if golden_rules_file.exists():
        with open(golden_rules_file, 'r') as f:
            content = f.read()
        
        # Parse markdown for rules (assume H2 headers are rules)
        lines = content.split('\n')
        current_rule = ""
        in_rule = False
        
        for line in lines:
            if line.startswith('##'):
                if current_rule:
                    # Save previous rule
                    cursor.execute('''
                        INSERT INTO golden_rules (rule, domain, confidence, source)
                        VALUES (?, ?, ?, ?)
                    ''', (current_rule.strip(), 'general', 1.0, str(golden_rules_file)))
                    restored_count += 1
                current_rule = line.lstrip('#').strip()
                in_rule = True
            elif in_rule and line.strip() and not line.startswith('#'):
                current_rule += "\n" + line
        
        # Don't forget last rule
        if current_rule:
            cursor.execute('''
                INSERT INTO golden_rules (rule, domain, confidence, source)
                VALUES (?, ?, ?, ?)
            ''', (current_rule.strip(), 'general', 1.0, str(golden_rules_file)))
            restored_count += 1
    
    conn.commit()
    conn.close()
    return restored_count

print()
print("=" * 60)
print("🔄 RESTORING KNOWLEDGE FROM MARKDOWN FILES")
print("=" * 60)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# Run all restorations
h_count = restore_heuristics()
print(f"  ✅ Restored {h_count} heuristics")

f_count = restore_failures()
print(f"  ✅ Restored {f_count} failures")

s_count = restore_successes()
print(f"  ✅ Restored {s_count} successes")

g_count = restore_golden_rules()
print(f"  ✅ Restored {g_count} golden rules")

# Verify
print()
print("📊 Verification:")
conn = sqlite3.connect(MEMORY_DIR / 'building.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM heuristics")
print(f"  • Heuristics in DB: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM failures")
print(f"  • Failures in DB: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM successes")
print(f"  • Successes in DB: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM golden_rules")
print(f"  • Golden Rules in DB: {cursor.fetchone()[0]}")

conn.close()

print()
print("=" * 60)
print("✅ KNOWLEDGE RESTORATION COMPLETE")
print("=" * 60)
