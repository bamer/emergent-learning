#!/usr/bin/env python3
"""
Emergency syntax fixes for the query system
This will fix the most critical errors to allow the system to function
"""

import os
import re

def fix_query_syntax():
    """Fix critical syntax errors in query system files"""
    
    query_dir = "/home/bamer/.opencode/emergent-learning/query"
    
    if not os.path.exists(query_dir):
        print(f"Query directory not found: {query_dir}")
        return
    
    # Files with critical syntax errors
    critical_files = [
        "meta_observer.py",
        "fraud_detector.py", 
        "project_context.py",
        "lifecycle_manager.py",
        "cli.py",
        "rag_query.py",
        "repair_database.py",
        "threshold_tuner.py",
        "fraud_outcomes.py",
        "test_query.py",
        "migrations.py",
        "plan_postmortem.py",
        "fraud_review.py",
        "dashboard.py"
    ]
    
    fixes_applied = 0
    
    for filename in critical_files:
        filepath = os.path.join(query_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Fix cursor\1 errors (already done, but double-check)
                content = content.replace('cursor\\1', 'cursor.fetchall()')
                
                # Fix syntax comments
                content = re.sub(
                    r"cursor\.fetchall\(\)  # Ajouté LIMIT pour éviter l\\'accumulation mémoire:\s*",
                    "cursor.fetchall():  # Ajouté LIMIT pour éviter l accumulation mémoire\n",
                    content
                )
                
                # Fix escaped backslashes in comments
                content = content.replace("\\'accumulation", "accumulation")
                
                # Fix common syntax patterns
                content = re.sub(r'":\s*', '": ', content)
                content = re.sub(r'"\[\\'accumulation"', '"[accumulation"', content)
                
                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixes_applied += 1
                    print(f"Fixed: {filename}")
                else:
                    print(f"No changes needed: {filename}")
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    print(f"\nFixed syntax errors in {fixes_applied} files")
    return fixes_applied

if __name__ == "__main__":
    fix_query_syntax()