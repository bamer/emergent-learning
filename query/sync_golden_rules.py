#!/usr/bin/env python3
"""
sync_golden_rules.py - Auto-sync golden rules from markdown to database

This runs automatically on system startup and periodically ensures golden rules
from memory/golden-rules.md are synchronized into the database.

One-time migration + continuous sync = rules always available in all contexts.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
import re

def get_elf_home() -> Path:
    """Resolve ELF home directory."""
    try:
        from elf_paths import get_base_path
        return get_base_path()
    except:
        return Path.home() / ".opencode" / "emergent-learning"

def parse_golden_rules(markdown_path: Path) -> list:
    """
    Parse golden rules from markdown file.
    
    Returns list of dicts with: name, rule_text, why, promoted, validations
    """
    rules = []
    
    if not markdown_path.exists():
        return rules
    
    content = markdown_path.read_text(encoding='utf-8')
    
    # Split by rule header: ## N. Title
    rule_blocks = re.split(r'^## \d+\.\s+', content, flags=re.MULTILINE)
    
    for block in rule_blocks[1:]:  # Skip first split (header)
        lines = block.strip().split('\n')
        if not lines:
            continue
        
        # First line is the rule title
        title = lines[0].strip()
        
        # Extract rule text (quoted section)
        rule_text = None
        why_text = None
        promoted = None
        validations = None
        
        for i, line in enumerate(lines[1:], 1):
            if line.startswith('> '):
                rule_text = line[2:].strip()
            elif line.startswith('**Why:**'):
                why_text = line.replace('**Why:**', '').strip()
            elif line.startswith('**Promoted:**'):
                promoted = line.replace('**Promoted:**', '').strip()
            elif line.startswith('**Validations:**'):
                validations = line.replace('**Validations:**', '').strip()
        
        if rule_text:
            rules.append({
                'name': title,
                'rule': rule_text,
                'explanation': why_text or '',
                'promoted': promoted or 'initial',
                'validations': validations or '0',
                'category': 'golden'
            })
    
    return rules

def sync_rules_to_database(rules: list, db_path: Path) -> dict:
    """
    Sync parsed rules to database golden_rules table.
    
    Returns: {'synced': N, 'updated': N, 'errors': []}
    """
    results = {'synced': 0, 'updated': 0, 'errors': []}
    
    if not db_path.exists():
        results['errors'].append(f"Database not found: {db_path}")
        return results
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS golden_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule TEXT NOT NULL UNIQUE,
                category TEXT,
                confidence REAL DEFAULT 0.9,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                use_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                source TEXT,
                explanation TEXT
            )
        """)
        
        for rule_data in rules:
            try:
                # Try to insert new rule
                cursor.execute("""
                    INSERT OR IGNORE INTO golden_rules 
                    (rule, category, confidence, source, explanation, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    rule_data['rule'],
                    rule_data['category'],
                    0.9,  # Golden rules have high confidence
                    f"golden-rules.md - {rule_data['promoted']}",
                    rule_data['explanation'],
                    1
                ))
                
                if cursor.rowcount > 0:
                    results['synced'] += 1
                else:
                    # Rule exists, maybe update explanation
                    cursor.execute("""
                        UPDATE golden_rules 
                        SET explanation = ?, is_active = 1
                        WHERE rule = ?
                    """, (rule_data['explanation'], rule_data['rule']))
                    if cursor.rowcount > 0:
                        results['updated'] += 1
                
            except sqlite3.IntegrityError:
                # Rule already exists
                results['updated'] += 1
            except Exception as e:
                results['errors'].append(f"Error syncing rule '{rule_data['name']}': {e}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        results['errors'].append(f"Database error: {e}")
    
    return results

def ensure_rules_in_context():
    """
    Ensure golden rules are loaded whenever context is needed.
    
    This is called automatically by query system initialization.
    """
    elf_home = get_elf_home()
    markdown_path = elf_home / "memory" / "golden-rules.md"
    db_path = elf_home / "memory" / "index.db"
    
    rules = parse_golden_rules(markdown_path)
    if rules:
        results = sync_rules_to_database(rules, db_path)
        return results
    
    return {'synced': 0, 'updated': 0, 'errors': ['No rules found']}

def main():
    """Main sync operation."""
    elf_home = get_elf_home()
    markdown_path = elf_home / "memory" / "golden-rules.md"
    db_path = elf_home / "memory" / "index.db"
    
    print("🔄 Syncing golden rules from markdown to database...")
    print()
    
    # Parse markdown
    rules = parse_golden_rules(markdown_path)
    
    if not rules:
        print("❌ No golden rules found in markdown")
        return 1
    
    print(f"📖 Found {len(rules)} golden rules in markdown")
    
    # Sync to database
    results = sync_rules_to_database(rules, db_path)
    
    print()
    print(f"✅ Synced: {results['synced']}")
    print(f"🔄 Updated: {results['updated']}")
    
    if results['errors']:
        print()
        print("⚠️  Errors:")
        for error in results['errors']:
            print(f"  - {error}")
        return 1
    
    print()
    print("✨ Golden rules synchronized!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
