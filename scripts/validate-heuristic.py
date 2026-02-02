#!/usr/bin/env python3
"""
Validate or violate a heuristic in the Emergent Learning Framework
Updates confidence scores based on validation/violation tracking.

Usage:
  python validate-heuristic.py --id <heuristic_id> --action validate
  python validate-heuristic.py --id <heuristic_id> --action violate
  python validate-heuristic.py --domain <domain> --rule <rule> --action validate

The confidence system:
  - Each validation increases confidence by 0.05 (max 1.0)
  - Each violation decreases confidence by 0.1 (min 0.0)
  - After 10+ validations and confidence > 0.9, heuristic becomes eligible for golden status
"""

import sqlite3
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# Database path
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "memory" / "index.db"

# Confidence adjustment values
VALIDATION_BOOST = 0.05
VIOLATION_PENALTY = 0.10
MAX_CONFIDENCE = 1.0
MIN_CONFIDENCE = 0.0
GOLDEN_THRESHOLD = 0.9
GOLDEN_VALIDATIONS_REQUIRED = 10


def get_db_connection():
    """Get database connection with WAL mode and timeout."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def find_heuristic_by_id(cursor, heuristic_id):
    """Find heuristic by ID."""
    cursor.execute(
        "SELECT id, domain, rule, confidence, times_validated, times_violated, is_golden FROM heuristics WHERE id = ?",
        (heuristic_id,),
    )
    return cursor.fetchone()


def find_heuristic_by_rule(cursor, domain, rule):
    """Find heuristic by domain and rule."""
    cursor.execute(
        "SELECT id, domain, rule, confidence, times_validated, times_violated, is_golden FROM heuristics WHERE domain = ? AND rule LIKE ?",
        (domain, f"%{rule}%"),
    )
    return cursor.fetchone()


def update_heuristic_validation(cursor, heuristic_id, action):
    """Update heuristic validation counters and confidence."""
    # Get current values
    cursor.execute(
        "SELECT confidence, times_validated, times_violated, is_golden FROM heuristics WHERE id = ?",
        (heuristic_id,),
    )
    row = cursor.fetchone()

    if not row:
        return None

    confidence, validated, violated, is_golden = row

    # Calculate new values
    if action == "validate":
        new_validated = validated + 1
        new_violated = violated
        new_confidence = min(confidence + VALIDATION_BOOST, MAX_CONFIDENCE)
    else:  # violate
        new_validated = validated
        new_violated = violated + 1
        new_confidence = max(confidence - VIOLATION_PENALTY, MIN_CONFIDENCE)

    # Check if eligible for golden status
    new_is_golden = is_golden
    if (
        not is_golden
        and new_validated >= GOLDEN_VALIDATIONS_REQUIRED
        and new_confidence >= GOLDEN_THRESHOLD
    ):
        new_is_golden = 1

    # Update database
    now = datetime.now().isoformat()
    cursor.execute(
        """UPDATE heuristics 
           SET confidence = ?, times_validated = ?, times_violated = ?, is_golden = ?, updated_at = ?
           WHERE id = ?""",
        (new_confidence, new_validated, new_violated, new_is_golden, now, heuristic_id),
    )

    return {
        "id": heuristic_id,
        "previous_confidence": confidence,
        "new_confidence": new_confidence,
        "times_validated": new_validated,
        "times_violated": new_violated,
        "is_golden": bool(new_is_golden),
        "promoted_to_golden": new_is_golden and not is_golden,
    }


def list_heuristics(cursor, domain=None):
    """List all heuristics or filter by domain."""
    if domain:
        cursor.execute(
            "SELECT id, domain, rule, confidence, times_validated, times_violated, is_golden FROM heuristics WHERE domain = ? ORDER BY confidence DESC",
            (domain,),
        )
    else:
        cursor.execute(
            "SELECT id, domain, rule, confidence, times_validated, times_violated, is_golden FROM heuristics ORDER BY confidence DESC"
        )
    return cursor\1  # Ajouté LIMIT pour éviter l\'accumulation mémoire


def main():
    parser = argparse.ArgumentParser(
        description="Validate or violate a heuristic in the ELF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --id 42 --action validate
  %(prog)s --id 42 --action violate
  %(prog)s --domain debugging --rule "Always check logs" --action validate
  %(prog)s --list
  %(prog)s --list --domain architecture
        """,
    )

    parser.add_argument("--id", type=int, help="Heuristic ID")
    parser.add_argument("--domain", help="Heuristic domain")
    parser.add_argument("--rule", help="Heuristic rule (partial match)")
    parser.add_argument(
        "--action", choices=["validate", "violate"], help="Action to take"
    )
    parser.add_argument("--list", action="store_true", help="List all heuristics")

    args = parser.parse_args()

    # Check database exists
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if args.list:
            # List mode
            heuristics = list_heuristics(cursor, args.domain)

            if not heuristics:
                print(
                    f"No heuristics found"
                    + (f" in domain '{args.domain}'" if args.domain else "")
                )
                return

            print(
                f"\n{'ID':<5} {'Domain':<20} {'Conf':<6} {'Val':<4} {'Vio':<4} {'Golden':<7} Rule"
            )
            print("-" * 100)

            for row in heuristics:
                hid, domain, rule, conf, val, vio, golden = row
                rule_short = rule[:50] + "..." if len(rule) > 50 else rule
                golden_str = "⭐ YES" if golden else "no"
                print(
                    f"{hid:<5} {domain:<20} {conf:<6.2f} {val:<4} {vio:<4} {golden_str:<7} {rule_short}"
                )

            print(f"\nTotal: {len(heuristics)} heuristics")
            print(f"\nLegend: Conf=Confidence, Val=Validations, Vio=Violations")
            print(
                f"Golden threshold: {GOLDEN_VALIDATIONS_REQUIRED} validations + {GOLDEN_THRESHOLD} confidence"
            )

        elif args.action:
            # Validation/Violation mode
            heuristic = None

            if args.id:
                heuristic = find_heuristic_by_id(cursor, args.id)
            elif args.domain and args.rule:
                heuristic = find_heuristic_by_rule(cursor, args.domain, args.rule)
            else:
                print(
                    "❌ Error: Must provide --id OR both --domain and --rule",
                    file=sys.stderr,
                )
                sys.exit(1)

            if not heuristic:
                print(f"❌ Heuristic not found", file=sys.stderr)
                sys.exit(1)

            hid, domain, rule, conf, val, vio, golden = heuristic

            print(f"\n{'⭐' if golden else ' '} Heuristic #{hid}: {rule}")
            print(f"   Domain: {domain}")
            print(
                f"   Current: {conf:.2f} confidence, {val} validations, {vio} violations"
            )
            print(f"   Action: {args.action.upper()}")
            print()

            # Update
            result = update_heuristic_validation(cursor, hid, args.action)
            conn.commit()

            if result:
                print(f"✅ Updated successfully!")
                print(
                    f"   New confidence: {result['previous_confidence']:.2f} → {result['new_confidence']:.2f}"
                )
                print(
                    f"   Validations: {result['times_validated']}, Violations: {result['times_violated']}"
                )

                if result["promoted_to_golden"]:
                    print(f"\n🎉 PROMOTED TO GOLDEN RULE!")
                    print(
                        f"   This heuristic now has golden status (confidence >= {GOLDEN_THRESHOLD}, validations >= {GOLDEN_VALIDATIONS_REQUIRED})"
                    )
            else:
                print("❌ Update failed", file=sys.stderr)
                sys.exit(1)
        else:
            parser.print_help()

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
