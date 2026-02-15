#!/bin/bash
# Fix script - Move proposals from wrong directory to correct one

WRONG_DIR="/home/bamer/.opocode/emergent-learning/proposals/pending"
CORRECT_DIR="/home/bamer/.opencode/emergent-learning/proposals/pending"

echo "Moving proposals from .opocode to .opencode..."

if [ -d "$WRONG_DIR" ]; then
    # Move all proposal files
    mv "$WRONG_DIR"/*.md "$CORRECT_DIR/" 2>/dev/null
    
    # Count moved files
    MOVED=$(ls "$CORRECT_DIR"/proposal_*.md 2>/dev/null | wc -l)
    
    echo "✓ Moved $MOVED proposal files"
    echo ""
    echo "Files now in: $CORRECT_DIR"
    
    # List moved files
    ls -1 "$CORRECT_DIR"/proposal_*.md 2>/dev/null | head -10
    
    # Now it's safe to remove the wrong directory
    echo ""
    read -p "Remove .opocode directory? [y/N]: " response
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        rm -rf /home/bamer/.opocode
        echo "✓ Removed /home/bamer/.opocode"
    fi
else
    echo "Directory not found: $WRONG_DIR"
fi
