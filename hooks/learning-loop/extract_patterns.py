#!/usr/bin/env python3
"""
extract_patterns.py - Extract [LEARNED:] patterns from tool outputs

Processes tool execution output to identify and store learning patterns.
Integrates with the post_tool_learning.py hook system.

Patterns extracted:
- [LEARNED:] markers in output
- Success patterns from tool results
- Error patterns for improvement
- Cross-tool correlations
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from query.models import HeuristicModel, PatternModel


def extract_learned_markers(text: str) -> List[Dict[str, Any]]:
    """
    Extract [LEARNED:] markers from text.
    
    Format: [LEARNED: <pattern description>]
    
    Returns:
        List of extracted patterns with metadata
    """
    patterns = []
    
    # Match [LEARNED: ...] markers
    regex = r'\[LEARNED:\s*([^\]]+)\]'
    matches = re.finditer(regex, text, re.IGNORECASE)
    
    for match in matches:
        pattern_text = match.group(1).strip()
        patterns.append({
            'text': pattern_text,
            'type': 'learned_marker',
            'confidence': 0.8,  # Explicit markers are high confidence
            'extracted_at': datetime.now().isoformat(),
            'source': 'learned_marker'
        })
    
    return patterns


def extract_success_patterns(tool_output: str, tool_name: str) -> List[Dict[str, Any]]:
    """
    Extract success patterns from tool execution.
    
    Identifies patterns that indicate successful tool execution:
    - Tool completed successfully
    - Output format is correct
    - Expected data was generated
    """
    patterns = []
    
    success_indicators = [
        (r'success', 'Tool reported success'),
        (r'complete', 'Operation completed'),
        (r'✅|✓', 'Success marker found'),
        (r'done|finished', 'Process finished'),
    ]
    
    for indicator, description in success_indicators:
        if re.search(indicator, tool_output, re.IGNORECASE):
            patterns.append({
                'text': f'{tool_name}: {description}',
                'type': 'success_pattern',
                'confidence': 0.6,
                'extracted_at': datetime.now().isoformat(),
                'source': f'tool:{tool_name}'
            })
    
    return patterns


def extract_error_patterns(tool_output: str, tool_name: str) -> List[Dict[str, Any]]:
    """
    Extract error patterns to learn what goes wrong.
    
    Identifies patterns that indicate issues:
    - Error messages
    - Warnings
    - Failed assertions
    """
    patterns = []
    
    error_indicators = [
        (r'error|ERROR|Error', 'Error detected', -0.3),
        (r'warning|WARNING|Warning', 'Warning encountered', -0.2),
        (r'failed|FAILED|Failed', 'Operation failed', -0.4),
        (r'exception|Exception', 'Exception occurred', -0.5),
        (r'timeout|Timeout', 'Operation timed out', -0.6),
    ]
    
    for indicator, description, confidence_delta in error_indicators:
        if re.search(indicator, tool_output, re.IGNORECASE):
            patterns.append({
                'text': f'{tool_name}: {description}',
                'type': 'error_pattern',
                'confidence': max(0.1, 0.5 + confidence_delta),
                'extracted_at': datetime.now().isoformat(),
                'source': f'tool:{tool_name}'
            })
    
    return patterns


def extract_output_patterns(tool_output: str, tool_name: str) -> List[Dict[str, Any]]:
    """
    Extract patterns from tool output structure.
    
    Identifies:
    - JSON outputs
    - Structured data
    - Command patterns
    - File operations
    """
    patterns = []
    
    # Check for JSON output
    try:
        json.loads(tool_output)
        patterns.append({
            'text': f'{tool_name}: JSON output',
            'type': 'output_pattern',
            'confidence': 0.7,
            'extracted_at': datetime.now().isoformat(),
            'source': f'tool:{tool_name}'
        })
    except:
        pass
    
    # Check for table/structured output
    if re.search(r'\|.*\|.*\|', tool_output):  # Markdown table
        patterns.append({
            'text': f'{tool_name}: Tabular output',
            'type': 'output_pattern',
            'confidence': 0.6,
            'extracted_at': datetime.now().isoformat(),
            'source': f'tool:{tool_name}'
        })
    
    # Check for code blocks
    if re.search(r'```[\w]*\n', tool_output):
        patterns.append({
            'text': f'{tool_name}: Code generation',
            'type': 'output_pattern',
            'confidence': 0.7,
            'extracted_at': datetime.now().isoformat(),
            'source': f'tool:{tool_name}'
        })
    
    return patterns


def extract_all_patterns(tool_name: str, tool_input: str, tool_output: str) -> List[Dict[str, Any]]:
    """
    Extract all patterns from tool execution context.
    
    Args:
        tool_name: Name of the executed tool
        tool_input: Input provided to tool
        tool_output: Output produced by tool
        
    Returns:
        List of extracted patterns
    """
    all_patterns = []
    
    # Extract different pattern types
    all_patterns.extend(extract_learned_markers(tool_output))
    all_patterns.extend(extract_success_patterns(tool_output, tool_name))
    all_patterns.extend(extract_error_patterns(tool_output, tool_name))
    all_patterns.extend(extract_output_patterns(tool_output, tool_name))
    all_patterns.extend(extract_learned_markers(tool_input))  # Input markers too
    
    return all_patterns


def store_patterns(patterns: List[Dict[str, Any]]) -> bool:
    """
    Store extracted patterns in the database.
    
    Args:
        patterns: List of patterns to store
        
    Returns:
        Success status
    """
    if not patterns:
        return True
    
    try:
        for pattern in patterns:
            heuristic = HeuristicModel(
                pattern=pattern['text'],
                domain=pattern.get('source', 'unknown'),
                confidence=pattern.get('confidence', 0.5),
                tags=['extracted', pattern['type']],
                explanation=f"Auto-extracted from tool execution at {pattern['extracted_at']}"
            )
            heuristic.save()
        
        return True
    except Exception as e:
        print(f"Error storing patterns: {e}", file=sys.stderr)
        return False


def main():
    """
    Main entry point for pattern extraction.
    
    Reads tool execution context from stdin or arguments.
    """
    
    # Parse input
    tool_name = "unknown"
    tool_input = ""
    tool_output = ""
    
    if len(sys.argv) > 1:
        try:
            # Input is JSON passed as argument
            context = json.loads(sys.argv[1])
            tool_name = context.get('tool_name', 'unknown')
            tool_input = context.get('tool_input', '')
            tool_output = context.get('tool_output', '')
        except json.JSONDecodeError:
            print(f"Error parsing input: {sys.argv[1]}", file=sys.stderr)
            return 1
    else:
        # Read from stdin
        try:
            context = json.load(sys.stdin)
            tool_name = context.get('tool_name', 'unknown')
            tool_input = context.get('tool_input', '')
            tool_output = context.get('tool_output', '')
        except:
            print("No tool context provided", file=sys.stderr)
            return 1
    
    # Extract patterns
    patterns = extract_all_patterns(tool_name, tool_input, tool_output)
    
    if patterns:
        # Store patterns
        if store_patterns(patterns):
            print(f"Extracted and stored {len(patterns)} patterns from {tool_name}")
            return 0
        else:
            print(f"Failed to store {len(patterns)} patterns", file=sys.stderr)
            return 1
    else:
        print(f"No patterns extracted from {tool_name}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
