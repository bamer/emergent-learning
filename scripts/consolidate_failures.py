#!/usr/bin/env python3
"""
Pattern Recognition with Auto-Consolidation for ELF

This script analyzes duplicate failures and automatically extracts
heuristics/golden rules to prevent future occurrences.

Usage:
    python consolidate_failures.py [--dry-run] [--threshold 3]

Features:
- Detects failure patterns by title similarity
- Groups related failures by domain/context
- Auto-generates heuristics from frequent failures
- Creates golden rules for critical patterns
- Updates failure records with extracted knowledge
"""

import sqlite3
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from Open_ELF.utils.elf_logging import get_logger, log_info, log_error
    logger = get_logger("consolidate_failures")
except ImportError:
    import logging
    logger = logging.getLogger("consolidate_failures")
    logger.setLevel(logging.INFO)

# Database path
DB_PATH = Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"


class FailurePatternAnalyzer:
    """Analyzes failure patterns and extracts actionable heuristics."""
    
    def __init__(self, threshold: int = 2):
        self.threshold = threshold  # Minimum occurrences to consider a pattern
        self.patterns = []
        self.generated_heuristics = []
        
    def connect_db(self) -> sqlite3.Connection:
        """Connect to the ELF database."""
        return sqlite3.connect(str(DB_PATH))
    
    def find_duplicate_failures(self) -> List[Dict[str, Any]]:
        """Find failures that occur multiple times (potential patterns)."""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Find failures grouped by title with count
        cursor.execute("""
            SELECT 
                id,
                title,
                domain,
                type,
                context,
                description,
                outcome,
                COUNT(*) as occurrence_count,
                MIN(created_at) as first_seen,
                MAX(created_at) as last_seen
            FROM learnings 
            WHERE type = 'failure'
            GROUP BY title 
            HAVING occurrence_count >= ?
            ORDER BY occurrence_count DESC, last_seen DESC
        """, (self.threshold,))
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append({
                'id': row[0],
                'title': row[1],
                'domain': row[2],
                'type': row[3],
                'context': row[4],
                'description': row[5],
                'outcome': row[6],
                'occurrence_count': row[7],
                'first_seen': row[8],
                'last_seen': row[9],
            })
        
        conn.close()
        return patterns
    
    def extract_pattern_type(self, title: str) -> str:
        """Extract the type of failure from title."""
        # Common failure patterns
        patterns = {
            'check': r'check\s+(\w+)',
            'verify': r'verify\s+(\w+)',
            'auto-captured': r'auto-captured:\s*(.+)',
            'test': r'test\s+(\w+)',
            'meta-learning': r'meta-learning',
            'system': r'system\s+(\w+)',
        }
        
        title_lower = title.lower()
        for pattern_name, pattern_regex in patterns.items():
            if re.search(pattern_regex, title_lower):
                return pattern_name
        
        return 'general'
    
    def generate_heuristic_from_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a heuristic rule from a failure pattern."""
        title = pattern['title']
        domain = pattern['domain']
        count = pattern['occurrence_count']
        
        # Extract pattern type
        pattern_type = self.extract_pattern_type(title)
        
        # Generate rule based on pattern
        if 'auto-captured' in title.lower():
            # Auto-captured failures → preventive checks
            match = re.search(r'check\s+(.+)', title.lower())
            if match:
                check_target = match.group(1)
                rule = f"Always verify {check_target} before system operations"
                explanation = f"This failure occurred {count} times. Manual checking of {check_target} is error-prone. Implement automated verification."
            else:
                rule = f"Review and validate: {title.replace('Auto-captured: ', '')}"
                explanation = f"Recurring failure detected {count} times. Consider automating this check or adding validation steps."
        
        elif 'meta-learning' in title.lower():
            rule = "Validate meta-learning prerequisites before execution"
            explanation = f"Meta-learning failures occurred {count} times. Ensure data quality and sufficient training samples."
        
        elif 'test' in title.lower():
            rule = "Run comprehensive tests before committing changes"
            explanation = f"Test failures occurred {count} times. Implement pre-commit hooks and automated testing."
        
        else:
            # Generic rule
            rule = f"Prevent: {title[:80]}"
            explanation = f"This failure pattern occurred {count} times between {pattern['first_seen']} and {pattern['last_seen']}. Review root cause."
        
        return {
            'domain': domain or 'general',
            'rule': rule,
            'explanation': explanation,
            'source_type': 'failure',
            'confidence': min(0.5 + (count * 0.1), 0.95),  # Higher confidence with more occurrences
            'pattern_title': title,
            'occurrence_count': count,
            'is_golden': count >= 5,  # Golden rule if 5+ occurrences
        }
    
    def heuristic_exists(self, rule: str, domain: str) -> bool:
        """Check if a similar heuristic already exists."""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM heuristics 
            WHERE domain = ? AND (rule = ? OR rule LIKE ?)
        """, (domain, rule, f"%{rule[:50]}%"))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def insert_heuristic(self, heuristic: Dict[str, Any]) -> bool:
        """Insert a new heuristic into the database."""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO heuristics 
                (domain, rule, explanation, source_type, confidence, is_golden, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                heuristic['domain'],
                heuristic['rule'],
                heuristic['explanation'],
                heuristic['source_type'],
                heuristic['confidence'],
                heuristic['is_golden']
            ))
            
            conn.commit()
            heuristic_id = cursor.lastrowid
            conn.close()
            
            logger.info(f"✅ Created heuristic ID {heuristic_id}: {heuristic['rule'][:60]}...")
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"⚠️ Heuristic already exists: {heuristic['rule'][:60]}...")
            conn.close()
            return False
        except Exception as e:
            logger.error(f"❌ Failed to insert heuristic: {e}")
            conn.close()
            return False
    
    def update_failure_with_heuristic(self, failure_id: int, heuristic_id: int):
        """Link a failure to its extracted heuristic."""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE learnings 
                SET context = COALESCE(context, '') || ' | Extracted to heuristic ID: ' || ?
                WHERE id = ?
            """, (heuristic_id, failure_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to update failure {failure_id}: {e}")
            conn.close()
    
    def analyze_and_consolidate(self, dry_run: bool = False) -> Dict[str, Any]:
        """Main method: analyze patterns and consolidate into heuristics."""
        logger.info(f"🔍 Analyzing failure patterns (threshold: {self.threshold})...")
        
        # Find duplicate failures
        patterns = self.find_duplicate_failures()
        
        if not patterns:
            logger.info("✅ No duplicate failure patterns found above threshold")
            return {
                'patterns_found': 0,
                'heuristics_created': 0,
                'status': 'no_patterns'
            }
        
        logger.info(f"📊 Found {len(patterns)} failure patterns")
        
        stats = {
            'patterns_found': len(patterns),
            'heuristics_created': 0,
            'heuristics_skipped': 0,
            'patterns': []
        }
        
        # Process each pattern
        for pattern in patterns:
            logger.info(f"  📌 Pattern: '{pattern['title']}' ({pattern['occurrence_count']} occurrences)")
            
            # Generate heuristic
            heuristic = self.generate_heuristic_from_pattern(pattern)
            
            # Check if similar heuristic exists
            if self.heuristic_exists(heuristic['rule'], heuristic['domain']):
                logger.info(f"    ⏭️ Similar heuristic already exists, skipping")
                stats['heuristics_skipped'] += 1
                continue
            
            if dry_run:
                logger.info(f"    📝 Would create heuristic (dry-run): {heuristic['rule'][:60]}...")
                stats['heuristics_created'] += 1
            else:
                # Insert heuristic
                if self.insert_heuristic(heuristic):
                    stats['heuristics_created'] += 1
                    
                    # Update failure record
                    # Note: We'd need to get the heuristic_id here to link it
            
            stats['patterns'].append({
                'title': pattern['title'],
                'count': pattern['occurrence_count'],
                'rule': heuristic['rule'],
                'golden': heuristic['is_golden']
            })
        
        return stats
    
    def generate_report(self, stats: Dict[str, Any]) -> str:
        """Generate a human-readable report."""
        report = []
        report.append("=" * 70)
        report.append("FAILURE PATTERN CONSOLIDATION REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Threshold: {self.threshold} occurrences")
        report.append("")
        report.append(f"📊 Patterns Found: {stats['patterns_found']}")
        report.append(f"✅ Heuristics Created: {stats['heuristics_created']}")
        report.append(f"⏭️ Heuristics Skipped (duplicates): {stats['heuristics_skipped']}")
        report.append("")
        
        if stats['patterns']:
            report.append("📋 CONSOLIDATED PATTERNS:")
            report.append("-" * 70)
            
            for i, pattern in enumerate(stats['patterns'], 1):
                report.append(f"\n{i}. Pattern: {pattern['title']}")
                report.append(f"   Occurrences: {pattern['count']}")
                report.append(f"   Rule: {pattern['rule']}")
                if pattern['golden']:
                    report.append(f"   🏆 Promoted to GOLDEN RULE")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Consolidate duplicate failures into heuristics'
    )
    parser.add_argument(
        '--threshold', '-t',
        type=int,
        default=2,
        help='Minimum occurrences to consider a pattern (default: 2)'
    )
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--report', '-r',
        action='store_true',
        help='Generate detailed report'
    )
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = FailurePatternAnalyzer(threshold=args.threshold)
    
    # Run analysis
    stats = analyzer.analyze_and_consolidate(dry_run=args.dry_run)
    
    # Generate report
    if args.report or stats['heuristics_created'] > 0:
        report = analyzer.generate_report(stats)
        print("\n" + report)
    
    # Summary
    print(f"\n✅ Analysis complete: {stats['heuristics_created']} heuristics created")
    
    return 0 if stats['heuristics_created'] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
