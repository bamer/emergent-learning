# Focused Self-Test Script

## Purpose

This script provides a lightweight self-test for the Emergent Learning Framework (ELF) that verifies core functionality without the extensive scanning performed by the full self-test script.

## Features

The focused self-test verifies:

1. **Directory Structure** - Checks that all required ELF directories exist
2. **Database Integrity** - Verifies the SQLite database file and required tables
3. **Script Functionality** - Ensures core ELF scripts exist and are executable
4. **Query System** - Tests the query system functionality
5. **Golden Rules Integrity** - Checks for golden rules existence
6. **Bootstrap Recovery** - Verifies bootstrap recovery capability

## Usage

```bash
./focused-self-test.sh
```

## Benefits

- Faster execution than full self-test
- No verbose circular dependency scanning
- Focuses on core functionality only
- Automatically records failures to the building
- Provides clear pass/fail/warning status

## Output

The script provides a summary of:
- Tests passed
- Tests failed
- Warnings
- Overall status

If all core tests pass, the script exits with code 0.
If any tests fail, the script exits with code 1.