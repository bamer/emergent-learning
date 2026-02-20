#!/bin/bash
# Wrapper script to run opencode_sdk_client.mjs from project root
# This ensures correct module resolution

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"  # emergent-learning root

# Change to project root for module resolution
cd "$PROJECT_ROOT"

# Run the SDK client with stdin passed through
exec bun "$SCRIPT_DIR/opencode_sdk_client.mjs" "$@"
