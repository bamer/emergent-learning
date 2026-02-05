#!/usr/bin/env python3
"""
swarm_cli.py - Command-line interface for swarm tasks

Usage:
  python3 swarm_cli.py --task "Refactor API" --agents architect researcher skeptic
  python3 swarm_cli.py --task "Find bugs" --subtasks "Test edge cases" "Test invalid input" "Test performance"
"""

import sys
from pathlib import Path
from swarm_controller import SwarmController

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Swarm Agent Task Executor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute task with auto-generated subtasks
  python3 swarm_cli.py --task "Refactor authentication system"
  
  # Execute task with specific subtasks
  python3 swarm_cli.py --task "Find security vulnerabilities" \\
    --subtasks "Test SQL injection" "Test XSS" "Test CSRF"
  
  # Execute with specific agents
  python3 swarm_cli.py --task "Design API" --agents architect creative researcher
        """
    )
    
    parser.add_argument('--task', required=True, help='Main task description')
    parser.add_argument('--subtasks', nargs='+', help='Optional subtasks')
    parser.add_argument('--agents', nargs='+', default=['architect', 'researcher', 'skeptic', 'creative'],
                        help='Agents to use (default: all)')
    parser.add_argument('--output', help='Save results to JSON file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Execute swarm
    print("\n" + "="*70)
    print("  🐝 SWARM AGENT EXECUTION")
    print("="*70 + "\n")
    
    controller = SwarmController()
    result = controller.execute_swarm(args.task, args.subtasks)
    
    # Save results if requested
    if args.output:
        import json
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2))
        print(f"\n✅ Results saved to: {args.output}")
    
    # Print summary
    print("\n" + "="*70)
    print("  📊 SUMMARY")
    print("="*70)
    print(f"\nStatus: {result['status']}")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Total learnings captured: {len(result['all_learnings'])}")
    
    if result['all_learnings']:
        print("\nTop Learnings:")
        for i, learning in enumerate(result['all_learnings'][:5], 1):
            print(f"  {i}. {learning[:70]}...")
    
    print("\nAgent Results:")
    for agent_result in result['agent_results']:
        status_emoji = "✅" if agent_result['status'] == 'completed' else "❌"
        print(f"  {status_emoji} {agent_result['agent']}: {agent_result['status']} " 
              f"({len(agent_result['learnings'])} learnings)")
    
    print("\n" + "="*70 + "\n")
    
    return 0 if result['status'] == 'success' else 1

if __name__ == '__main__':
    sys.exit(main())
