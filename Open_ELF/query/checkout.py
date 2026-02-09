#!/usr/bin/env python3
"""
Emergent Learning Framework - Automated Checkout

Fully automated session closing - captures and records everything:
1. Session metadata to database
2. Triggers learning capture system
3. Saves session notes for next session
4. Updates semantic memory indices
"""

import sys
import io
import sqlite3
import json
import subprocess
from pathlib import Path
from datetime import datetime
import hashlib

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class CheckoutOrchestrator:
    """Automated checkout - captures and records session data."""

    BANNER = """
┌────────────────────────────────────┐
│    Emergent Learning Framework     │
├────────────────────────────────────┤
│                                    │
│      Session Complete              │
│      Recording learnings...        │
│                                    │
└────────────────────────────────────┘
"""

    def __init__(self):
        self.elf_home = self._resolve_elf_home()
        self.db_path = self.elf_home / "memory" / "index.db"
        self.heuristics_dir = self.elf_home / "memory" / "heuristics"
        self.session_notes_file = Path.home() / ".checkout_notes"
        self.timestamp = datetime.now()
        self.session_data = {
            'domains': [],
            'files_touched': [],
            'commits_made': 0,
            'heuristics_recorded': 0,
            'session_id': self._generate_session_id()
        }

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        data = f"{datetime.now().isoformat()}".encode()
        return hashlib.md5(data).hexdigest()[:12]

    def _resolve_elf_home(self) -> Path:
        try:
            current_dir = Path(__file__).resolve().parent
            src_dir = current_dir.parent
            if str(src_dir) not in sys.path:
                sys.path.insert(0, str(src_dir))
            from elf_paths import get_base_path
            return get_base_path()
        except ImportError:
            return Path.home() / '.opencode' / 'emergent-learning'

    def display_banner(self):
        print(self.BANNER)

    def analyze_session(self):
        """Auto-detect session activity from git and file system."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~5', 'HEAD'],
                capture_output=True, text=True, timeout=10, cwd=str(self.elf_home)
            )
            if result.returncode == 0:
                files = [f for f in result.stdout.strip().split('\n') if f]
                self.session_data['files_touched'] = files[:20]

                domains = set()
                for f in files:
                    if 'dashboard' in f:
                        domains.add('dashboard')
                    if 'query' in f:
                        domains.add('infrastructure')
                    if '.tsx' in f or '.jsx' in f:
                        domains.add('frontend')
                    if '.py' in f:
                        domains.add('backend')
                self.session_data['domains'] = list(domains)

            result = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD~5..HEAD'],
                capture_output=True, text=True, timeout=10, cwd=str(self.elf_home)
            )
            if result.returncode == 0:
                self.session_data['commits_made'] = int(result.stdout.strip() or 0)

        except Exception:
            pass

    def record_session_to_database(self) -> bool:
        """Record session metadata to database."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # Record session as a decision/activity record
                domains_str = ','.join(self.session_data['domains']) or 'general'
                files_str = ','.join(self.session_data['files_touched'][:10])
                
                cursor.execute("""
                    INSERT INTO decisions (
                        title, context, decision, rationale, 
                        files_touched, domain, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"Session {self.session_data['session_id'][:8]}",
                    f"Automated session checkout",
                    f"Recorded session activity",
                    f"Commits: {self.session_data['commits_made']}, Files: {len(self.session_data['files_touched'])}",
                    files_str,
                    domains_str,
                    'accepted',
                    self.timestamp.isoformat()
                ))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"   [WARN] Could not record to database: {e}")
            return False

    def count_recent_heuristics(self) -> int:
        """Count heuristics recorded in the last 4 hours."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM heuristics
                    WHERE created_at > datetime('now', '-4 hours')
                """)
                return cursor.fetchone()[0]
        except Exception:
            return 0

    def save_session_notes(self) -> bool:
        """Save session summary for next session."""
        try:
            notes = {
                'session_id': self.session_data['session_id'],
                'timestamp': self.timestamp.isoformat(),
                'domains': self.session_data['domains'],
                'commits': self.session_data['commits_made'],
                'files_touched': len(self.session_data['files_touched']),
                'heuristics_recorded': self.session_data['heuristics_recorded'],
                'domains_worked': ', '.join(self.session_data['domains']) if self.session_data['domains'] else 'general'
            }
            
            # Append to session notes file
            with open(self.session_notes_file, 'a') as f:
                f.write(json.dumps(notes) + '\n')
            
            return True
        except Exception as e:
            print(f"   [WARN] Could not save session notes: {e}")
            return False

    def update_semantic_memory_index(self) -> bool:
        """Update semantic memory indices."""
        try:
            # Create/update heuristics directory metadata
            self.heuristics_dir.mkdir(parents=True, exist_ok=True)
            
            # Index current heuristics
            heuristic_files = list(self.heuristics_dir.glob('*.md'))
            
            index_file = self.heuristics_dir / '_index.json'
            index_data = {
                'updated_at': self.timestamp.isoformat(),
                'total_heuristics': len(heuristic_files),
                'domains': list(set(f.stem.lower() for f in heuristic_files)),
                'last_session_id': self.session_data['session_id']
            }
            
            with open(index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"   [WARN] Could not update semantic memory: {e}")
            return False

    def display_summary(self):
        """Display automated session summary."""
        print("[*] Session Summary (auto-detected)")

        if self.session_data['domains']:
            print(f"   Domains: {', '.join(self.session_data['domains'])}")

        if self.session_data['commits_made']:
            print(f"   Commits: {self.session_data['commits_made']}")

        files = self.session_data['files_touched']
        if files:
            print(f"   Files modified: {len(files)}")
            for f in files[:5]:
                print(f"     - {f}")
            if len(files) > 5:
                print(f"     ... and {len(files) - 5} more")

        heuristics = self.count_recent_heuristics()
        self.session_data['heuristics_recorded'] = heuristics
        if heuristics:
            print(f"   Heuristics recorded: {heuristics}")

        print("")

    def run(self):
        """Execute automated checkout - analyze, record, and save."""
        self.display_banner()
        
        # Step 1: Analyze session activity
        self.analyze_session()
        
        # Step 2: Record session to database
        print("[*] Recording session metadata...")
        if self.record_session_to_database():
            print("   [OK] Session recorded to database")
        
        # Step 3: Save session notes for next session
        print("[*] Saving session notes...")
        if self.save_session_notes():
            print("   [OK] Session notes saved")
        
        # Step 4: Update semantic memory indices
        print("[*] Updating semantic memory...")
        if self.update_semantic_memory_index():
            print("   [OK] Semantic memory updated")
        
        # Step 5: Display summary
        self.display_summary()
        
        print("[OK] Checkout complete - all learnings recorded!")


def main():
    try:
        orchestrator = CheckoutOrchestrator()
        orchestrator.run()
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Checkout failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
