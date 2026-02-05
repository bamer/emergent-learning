# Uninstalling ELF (Emergent Learning Framework)

This guide helps you cleanly remove ELF without breaking your Opencode setup.

---

## Automated Uninstall Script (Recommended)

For the easiest uninstall experience, use the automated script:

### Windows (PowerShell)
```powershell
# Download and run uninstall script
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/your-repo/ELF/main/scripts/uninstall.ps1" -OutFile "$env:TEMP\uninstall-elf.ps1"
PowerShell -ExecutionPolicy Bypass -File "$env:TEMP\uninstall-elf.ps1"
```

### Mac/Linux
```bash
# Download and run uninstall script
# TODO: uninstall.sh script needs to be created
curl -fsSL https://raw.githubusercontent.com/your-repo/ELF/main/scripts/uninstall.sh | bash
```

The automated script will:
- Remove all ELF directories safely
- Clean up hooks from settings.json automatically
- Offer to backup your data before removal
- Validate that Opencode still works after uninstall

**Note:** If you prefer manual control, use the manual steps below.

---

## Manual Quick Uninstall

### Windows (PowerShell)
```powershell
# Remove ELF files (keeps your Opencode working)
Remove-Item -Recurse -Force "$env:USERPROFILE\.opencode\emergent-learning"
Remove-Item -Recurse -Force "$env:USERPROFILE\.opencode\hooks\learning-loop"

# Note: You'll need to manually edit settings.json to remove hooks
# See "Restore settings.json" below
```

### Mac/Linux
```bash
# Remove ELF files (keeps your Opencode working)
rm -rf ~/.opencode/emergent-learning
rm -rf ~/.opencode/hooks/learning-loop

# Note: You'll need to manually edit settings.json to remove hooks
# See "Restore settings.json" below
```

---

## Restore settings.json

The installer added hooks to your `~/.opencode/settings.json`. To remove them:

1. Open `~/.opencode/settings.json` in a text editor

2. Find and remove the `PreToolUse` and `PostToolUse` sections that reference `learning-loop`:

   **Remove these blocks:**
   ```json
   "PreToolUse": [
     {
       "matcher": "Task",
       "hooks": [
         {
           "type": "command",
           "command": "python \"...learning-loop/pre_tool_learning.py\""
         }
       ]
     }
   ],
   "PostToolUse": [
     {
       "matcher": "Task",
       "hooks": [
         {
           "type": "command",
           "command": "python \"...learning-loop/post_tool_learning.py\""
         }
       ]
     }
   ]
   ```

3. If you had no other hooks, you can remove the entire `"hooks"` section, or leave it as:
   ```json
   {
     "hooks": {}
   }
   ```

4. Save the file

---

## Optional: Remove AGENTS.md Changes

**WARNING:** AGENTS.md contains important instructions for how Opencode operates. Removing it will affect ALL your Opencode sessions, not just ELF.

### Before Removing AGENTS.md:

1. **Check if you had a pre-existing AGENTS.md:**
   - If you installed ELF on a fresh system, ELF created this file
   - If you had Opencode configured before ELF, you likely had your own AGENTS.md
   - **The ELF installer preserves existing AGENTS.md files** - it does NOT overwrite them

2. **Determine what's in your AGENTS.md:**
   ```bash
   # View your AGENTS.md file
   cat ~/.opencode/AGENTS.md
   
   # Check if it contains only ELF instructions
   grep -i "emergent learning" ~/.opencode/AGENTS.md
   ```

3. **Safe removal options:**

   **Option A: If ELF created it (safe to remove):**
   ```bash
   # Only remove if the file contains ONLY ELF instructions
   rm ~/.opencode/AGENTS.md
   ```

   **Option B: If you're unsure (safest):**
   ```bash
   # Backup first, then remove ELF sections manually
   cp ~/.opencode/AGENTS.md ~/.opencode/AGENTS.md.backup
   
   # Edit the file and remove only the ELF-related sections
   nano ~/.opencode/AGENTS.md  # or use your preferred editor
   ```

   **Option C: If you had pre-existing content (keep and edit):**
   ```bash
   # Just remove the ELF sections from AGENTS.md
   # Keep your original Opencode instructions
   ```

**What happens if you remove AGENTS.md:**
- Opencode will no longer follow the ELF query-before-acting protocol
- Any other custom instructions you had will also be removed
- Your Opencode sessions will use default behavior only

**Recommendation:** Unless you're certain ELF created this file and you have no other use for AGENTS.md, consider keeping it and removing only the ELF-specific sections.

---

## Keep Your Data (Optional)

If you want to keep your learned heuristics and history for later:

**What the backup includes:**
- Your learned heuristics and confidence scores
- Success/failure records
- Custom golden rules (if you modified them)
- CEO inbox items
- Agent run history

**What the backup does NOT include:**
- The ELF code itself (re-download from GitHub when reinstalling)
- Dashboard dependencies (will be reinstalled)
- Hook configurations (will be reconfigured during reinstall)

**Before uninstalling, backup:**
```bash
# Copy database (contains heuristics, failures, successes)
cp ~/.opencode/emergent-learning/memory/index.db ~/elf-backup.db

# Copy golden rules (if you customized them)
cp ~/.opencode/emergent-learning/memory/golden-rules.md ~/elf-golden-rules-backup.md

# Copy CEO inbox (pending decisions)
cp -r ~/.opencode/emergent-learning/ceo-inbox ~/elf-ceo-inbox-backup

# Optional: Copy entire memory directory for complete backup
cp -r ~/.opencode/emergent-learning/memory ~/elf-memory-backup
```

**To restore later after reinstalling:**
```bash
cp ~/elf-backup.db ~/.opencode/emergent-learning/memory/index.db
```

---

## Verify Uninstall

After removing, verify Opencode still works:

```bash
claude --version
```

And check no ELF directories remain:

```bash
ls ~/.opencode/emergent-learning    # Should say "No such file or directory"
ls ~/.opencode/hooks/learning-loop  # Should say "No such file or directory"
```

---

## Reinstalling

If you change your mind, just run the installer again:

```bash
./install.sh        # Mac/Linux
.\install.ps1       # Windows
```

Your previous database (if backed up) can be restored to preserve history.
