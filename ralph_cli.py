#!/usr/bin/env python3
"""
Command-line interface for the Ralph Loop Tool
"""

import sys
import argparse
from ralph_loop_tool import RalphLoopTool, StoryStatus, StoryPriority


def main():
    parser = argparse.ArgumentParser(
        description="Ralph Loop Tool for User Story Management"
    )
    parser.add_argument("--db", default="ralph_loop.db", help="Database file path")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Recognize command
    recognize_parser = subparsers.add_parser(
        "recognize", help="Recognize a new user story"
    )
    recognize_parser.add_argument("title", help="Story title")
    recognize_parser.add_argument("description", help="Story description")
    recognize_parser.add_argument(
        "--priority",
        choices=["low", "medium", "high", "critical"],
        default="medium",
        help="Story priority",
    )
    recognize_parser.add_argument("--tags", nargs="*", help="Story tags")
    recognize_parser.add_argument("--deps", nargs="*", help="Dependencies (story IDs)")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a user story")
    analyze_parser.add_argument("story_id", help="Story ID")
    analyze_parser.add_argument("--criteria", nargs="*", help="Acceptance criteria")
    analyze_parser.add_argument(
        "--effort", type=int, help="Estimated effort in story points"
    )

    # Localize command
    localize_parser = subparsers.add_parser("localize", help="Localize a user story")
    localize_parser.add_argument("story_id", help="Story ID")
    localize_parser.add_argument("scope", help="Scope of work")
    localize_parser.add_argument("impact", help="Impact assessment")
    localize_parser.add_argument("--assign", help="Assign to agent/team")

    # Handle command
    handle_parser = subparsers.add_parser("handle", help="Handle a user story")
    handle_parser.add_argument("story_id", help="Story ID")
    handle_parser.add_argument("--notes", help="Implementation notes")

    # Preserve command
    preserve_parser = subparsers.add_parser(
        "preserve", help="Preserve learnings from a user story"
    )
    preserve_parser.add_argument("story_id", help="Story ID")
    preserve_parser.add_argument("--lessons", help="Lessons learned")
    preserve_parser.add_argument("--doc", help="Documentation reference")

    # List command
    list_parser = subparsers.add_parser("list", help="List user stories")
    list_parser.add_argument(
        "--status",
        choices=["recognized", "analyzed", "localized", "handled", "preserved"],
        help="Filter by status",
    )

    # Show command
    show_parser = subparsers.add_parser("show", help="Show details of a user story")
    show_parser.add_argument("story_id", help="Story ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize the tool
    ralph_tool = RalphLoopTool(args.db)

    try:
        if args.command == "recognize":
            priority = StoryPriority(args.priority)
            story = ralph_tool.recognize_story(
                title=args.title,
                description=args.description,
                priority=priority,
                tags=args.tags or [],
                dependencies=args.deps or [],
            )
            print(f"✅ Story recognized with ID: {story.id}")

        elif args.command == "analyze":
            story = ralph_tool.analyze_story(
                story_id=args.story_id,
                acceptance_criteria=args.criteria,
                estimated_effort=args.effort,
            )
            print(f"✅ Story analyzed")
            ralph_tool.print_story_summary(story)

        elif args.command == "localize":
            story = ralph_tool.localize_story(
                story_id=args.story_id,
                scope=args.scope,
                impact=args.impact,
                assigned_to=args.assign,
            )
            print(f"✅ Story localized")
            ralph_tool.print_story_summary(story)

        elif args.command == "handle":
            story = ralph_tool.handle_story(
                story_id=args.story_id, implementation_notes=args.notes
            )
            print(f"✅ Story handled")
            ralph_tool.print_story_summary(story)

        elif args.command == "preserve":
            story = ralph_tool.preserve_story(
                story_id=args.story_id,
                lessons_learned=args.lessons,
                documentation_ref=args.doc,
            )
            print(f"✅ Story preserved")
            ralph_tool.print_story_summary(story)

        elif args.command == "list":
            if args.status:
                status = StoryStatus(args.status)
                stories = ralph_tool.list_stories(status=status)
            else:
                stories = ralph_tool.list_stories()

            if stories:
                print(f"\n📋 Found {len(stories)} stories:")
                for story in stories:
                    print(
                        f"  • [{story.status.value[:3].upper()}] {story.title} ({story.priority.value}) - {story.id}"
                    )
            else:
                print("No stories found")

        elif args.command == "show":
            story = ralph_tool.get_story(args.story_id)
            if story:
                ralph_tool.print_story_summary(story)
            else:
                print(f"❌ Story with ID {args.story_id} not found")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
