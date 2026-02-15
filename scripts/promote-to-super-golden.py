#!/usr/bin/env python3
"""
Promote a heuristic to Super Golden Rule (Universal Scope)

Usage:
    python promote-to-super-golden.py <heuristic_id>   # Promote to universal
    python promote-to-super-golden.py <heuristic_id> --domain <domain>  # Promote to domain
    python promote-to-super-golden.py --list                       # List available heuristics
"""

import sqlite3
import sys
from pathlib import Path

# Use index.db (used by checkin)
DB_PATH = Path.home() / ".opencode" / "emergent-learning" / "memory" / "index.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def list_heuristics():
    """List heuristics ready for promotion."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, rule, domain, confidence, times_validated, scope
        FROM heuristics 
        WHERE confidence >= 0.5 AND (scope != 'universal' OR scope IS NULL)
        ORDER BY confidence DESC, times_validated DESC
        LIMIT 20
    """)

    print("\n=== Heuristics Ready for Promotion ===\n")
    for h in cursor.fetchall():
        conf = h["confidence"] or 0.0
        print(f"[{h['id']}] 🟡 {h['rule'][:65]}...")
        print(
            f"    Domain: {h['domain'] or 'general'}, Conf: {conf:.2f}, Validations: {h['times_validated']}"
        )
        print()

    conn.close()


def promote(heuristic_id: int, scope: str = "universal"):
    """Promote a heuristic to golden rule."""
    conn = get_db()
    cursor = conn.cursor()

    # Get the heuristic
    cursor.execute("SELECT * FROM heuristics WHERE id = ?", (heuristic_id,))
    h = cursor.fetchone()

    if not h:
        print(f"❌ Error: Heuristic {heuristic_id} not found")
        return False

    # Check if already a universal golden rule
    if h["scope"] == "universal":
        print(f"ℹ️  Heuristic {heuristic_id} is already a universal golden rule")
        return False

    # Insert into golden_rules with scope
    explanation = h["explanation"] if h["explanation"] else ""
    cursor.execute(
        """
        INSERT INTO golden_rules (rule, category, confidence, source, scope, explanation)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            h["rule"],
            h["domain"] or "general",
            h["confidence"] or 0.5,
            f"promoted_from_heuristic_{heuristic_id}",
            scope,
            explanation,
        ),
    )

    # Update heuristic scope
    cursor.execute(
        "UPDATE heuristics SET scope = ? WHERE id = ?", (scope, heuristic_id)
    )

    conn.commit()

    print(f"\n✅ SUCCESS: Heuristic {heuristic_id} promoted to SUPER GOLDEN RULE!")
    print(f"   Rule: {h['rule'][:70]}...")
    print(f"   Scope: {scope}")
    print(f"   Domain: {h['domain'] or 'general'}")

    conn.close()
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n=== Golden Rules (Universal) ===")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as c FROM golden_rules WHERE scope = 'universal'"
        )
        print(f"Total: {cursor.fetchone()['c']} universal golden rules\n")
        conn.close()
        return

    arg = sys.argv[1]

    if arg == "--list":
        list_heuristics()
    elif arg == "--help":
        print(__doc__)
    elif arg.isdigit():
        scope = "universal"
        # Check for --domain flag
        if "--domain" in sys.argv:
            idx = sys.argv.index("--domain")
            if idx + 1 < len(sys.argv):
                scope = sys.argv[idx + 1]
        promote(int(arg), scope)
    else:
        print(f"Unknown option: {arg}")
        print(__doc__)


if __name__ == "__main__":
    main()
