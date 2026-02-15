#!/usr/bin/env python3
"""
Ralph Loop Tool for User Story Management

Implements the Ralph Loop methodology for iterative user story refinement:
1. Recognize - Identify and capture user stories
2. Analyze - Break down and analyze story components
3. Localize - Determine scope and impact
4. Handle - Implement solutions
5. Preserve - Document and preserve learnings

This tool manages the complete lifecycle of user stories in an agile development process.
"""

import json
import uuid
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class StoryStatus(Enum):
    """Status of a user story in the Ralph Loop"""

    RECOGNIZED = "recognized"  # Story identified and captured
    ANALYZED = "analyzed"  # Story broken down and analyzed
    LOCALIZED = "localized"  # Scope and impact determined
    HANDLED = "handled"  # Implementation completed
    PRESERVED = "preserved"  # Learnings documented and preserved


class StoryPriority(Enum):
    """Priority levels for user stories"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class UserStory:
    """Represents a user story in the Ralph Loop"""

    id: str
    title: str
    description: str
    status: StoryStatus
    priority: StoryPriority
    acceptance_criteria: List[str]
    estimated_effort: int  # Story points
    assigned_to: Optional[str]  # Agent or team name
    created_at: str
    updated_at: str
    tags: List[str]
    dependencies: List[str]  # IDs of dependent stories
    notes: List[str]


class RalphLoopDB:
    """Database handler for Ralph Loop stories"""

    def __init__(self, db_path: str = "ralph_loop.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create stories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                acceptance_criteria TEXT,
                estimated_effort INTEGER,
                assigned_to TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                tags TEXT,
                dependencies TEXT,
                notes TEXT
            )
        """)

        conn.commit()
        conn.close()

    def save_story(self, story: UserStory):
        """Save a user story to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO stories (
                id, title, description, status, priority, acceptance_criteria,
                estimated_effort, assigned_to, created_at, updated_at, tags,
                dependencies, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                story.id,
                story.title,
                story.description,
                story.status.value,
                story.priority.value,
                json.dumps(story.acceptance_criteria),
                story.estimated_effort,
                story.assigned_to,
                story.created_at,
                story.updated_at,
                json.dumps(story.tags),
                json.dumps(story.dependencies),
                json.dumps(story.notes),
            ),
        )

        conn.commit()
        conn.close()

    def get_story(self, story_id: str) -> Optional[UserStory]:
        """Retrieve a user story by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_story(row)

    def get_stories_by_status(self, status: StoryStatus) -> List[UserStory]:
        """Retrieve all stories with a specific status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM stories WHERE status = ?", (status.value,))
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_story(row) for row in rows]

    def get_all_stories(self) -> List[UserStory]:
        """Retrieve all stories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM stories")
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_story(row) for row in rows]

    def update_story_status(self, story_id: str, status: StoryStatus):
        """Update the status of a story"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE stories 
            SET status = ?, updated_at = ?
            WHERE id = ?
        """,
            (status.value, datetime.now().isoformat(), story_id),
        )

        conn.commit()
        conn.close()

    def _row_to_story(self, row: tuple) -> UserStory:
        """Convert database row to UserStory object"""
        return UserStory(
            id=row[0],
            title=row[1],
            description=row[2],
            status=StoryStatus(row[3]),
            priority=StoryPriority(row[4]),
            acceptance_criteria=json.loads(row[5]) if row[5] else [],
            estimated_effort=row[6] or 0,
            assigned_to=row[7],
            created_at=row[8],
            updated_at=row[9],
            tags=json.loads(row[10]) if row[10] else [],
            dependencies=json.loads(row[11]) if row[11] else [],
            notes=json.loads(row[12]) if row[12] else [],
        )


class RalphLoopTool:
    """Main Ralph Loop Tool for user story management"""

    def __init__(self, db_path: str = "ralph_loop.db"):
        self.db = RalphLoopDB(db_path)
        self.current_story: Optional[UserStory] = None

    def recognize_story(
        self,
        title: str,
        description: str,
        priority: StoryPriority = StoryPriority.MEDIUM,
        tags: List[str] = None,
        dependencies: List[str] = None,
    ) -> UserStory:
        """
        Phase 1: Recognize - Identify and capture a new user story

        Args:
            title: Brief title of the story
            description: Detailed description of the story
            priority: Priority level of the story
            tags: Tags for categorization
            dependencies: IDs of dependent stories

        Returns:
            Created UserStory object
        """
        story_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        story = UserStory(
            id=story_id,
            title=title,
            description=description,
            status=StoryStatus.RECOGNIZED,
            priority=priority,
            acceptance_criteria=[],
            estimated_effort=0,
            assigned_to=None,
            created_at=now,
            updated_at=now,
            tags=tags or [],
            dependencies=dependencies or [],
            notes=[f"Story recognized at {now}"],
        )

        self.db.save_story(story)
        self.current_story = story

        print(f"✅ Story '{title}' recognized with ID: {story_id}")
        return story

    def analyze_story(
        self,
        story_id: str,
        acceptance_criteria: List[str] = None,
        estimated_effort: int = None,
    ) -> UserStory:
        """
        Phase 2: Analyze - Break down and analyze story components

        Args:
            story_id: ID of the story to analyze
            acceptance_criteria: List of acceptance criteria
            estimated_effort: Estimated effort in story points

        Returns:
            Updated UserStory object
        """
        story = self.db.get_story(story_id)
        if not story:
            raise ValueError(f"Story with ID {story_id} not found")

        if story.status != StoryStatus.RECOGNIZED:
            raise ValueError(
                f"Story must be in RECOGNIZED status to analyze. Current status: {story.status.value}"
            )

        if acceptance_criteria:
            story.acceptance_criteria = acceptance_criteria

        if estimated_effort is not None:
            story.estimated_effort = estimated_effort

        story.status = StoryStatus.ANALYZED
        story.updated_at = datetime.now().isoformat()
        story.notes.append(f"Story analyzed at {story.updated_at}")

        self.db.save_story(story)
        self.current_story = story

        print(f"✅ Story '{story.title}' analyzed")
        return story

    def localize_story(
        self, story_id: str, scope: str, impact: str, assigned_to: str = None
    ) -> UserStory:
        """
        Phase 3: Localize - Determine scope and impact of the story

        Args:
            story_id: ID of the story to localize
            scope: Description of the scope of work
            impact: Description of the impact
            assigned_to: Agent or team assigned to handle the story

        Returns:
            Updated UserStory object
        """
        story = self.db.get_story(story_id)
        if not story:
            raise ValueError(f"Story with ID {story_id} not found")

        if story.status != StoryStatus.ANALYZED:
            raise ValueError(
                f"Story must be in ANALYZED status to localize. Current status: {story.status.value}"
            )

        story.status = StoryStatus.LOCALIZED
        story.assigned_to = assigned_to
        story.updated_at = datetime.now().isoformat()
        story.notes.append(f"Story localized at {story.updated_at}")
        story.notes.append(f"Scope: {scope}")
        story.notes.append(f"Impact: {impact}")

        self.db.save_story(story)
        self.current_story = story

        print(
            f"✅ Story '{story.title}' localized and assigned to {assigned_to or 'unassigned'}"
        )
        return story

    def handle_story(
        self, story_id: str, implementation_notes: str = None
    ) -> UserStory:
        """
        Phase 4: Handle - Implement the solution for the story

        Args:
            story_id: ID of the story to handle
            implementation_notes: Notes about the implementation

        Returns:
            Updated UserStory object
        """
        story = self.db.get_story(story_id)
        if not story:
            raise ValueError(f"Story with ID {story_id} not found")

        if story.status != StoryStatus.LOCALIZED:
            raise ValueError(
                f"Story must be in LOCALIZED status to handle. Current status: {story.status.value}"
            )

        story.status = StoryStatus.HANDLED
        story.updated_at = datetime.now().isoformat()

        if implementation_notes:
            story.notes.append(f"Implementation: {implementation_notes}")

        story.notes.append(f"Story handled at {story.updated_at}")

        self.db.save_story(story)
        self.current_story = story

        print(f"✅ Story '{story.title}' handled")
        return story

    def preserve_story(
        self, story_id: str, lessons_learned: str = None, documentation_ref: str = None
    ) -> UserStory:
        """
        Phase 5: Preserve - Document and preserve learnings from the story

        Args:
            story_id: ID of the story to preserve
            lessons_learned: Key lessons learned from implementing the story
            documentation_ref: Reference to documentation

        Returns:
            Updated UserStory object
        """
        story = self.db.get_story(story_id)
        if not story:
            raise ValueError(f"Story with ID {story_id} not found")

        if story.status != StoryStatus.HANDLED:
            raise ValueError(
                f"Story must be in HANDLED status to preserve. Current status: {story.status.value}"
            )

        story.status = StoryStatus.PRESERVED
        story.updated_at = datetime.now().isoformat()

        if lessons_learned:
            story.notes.append(f"Lessons learned: {lessons_learned}")

        if documentation_ref:
            story.notes.append(f"Documentation: {documentation_ref}")

        story.notes.append(f"Story preserved at {story.updated_at}")

        self.db.save_story(story)
        self.current_story = story

        print(f"✅ Story '{story.title}' preserved with learnings documented")
        return story

    def get_story(self, story_id: str) -> Optional[UserStory]:
        """Get a story by ID"""
        return self.db.get_story(story_id)

    def list_stories(self, status: StoryStatus = None) -> List[UserStory]:
        """List stories, optionally filtered by status"""
        if status:
            return self.db.get_stories_by_status(status)
        else:
            return self.db.get_all_stories()

    def get_current_story(self) -> Optional[UserStory]:
        """Get the current story being worked on"""
        return self.current_story

    def print_story_summary(self, story: UserStory):
        """Print a formatted summary of a story"""
        print(f"\n📝 Story: {story.title}")
        print(f"   ID: {story.id}")
        print(f"   Status: {story.status.value.upper()}")
        print(f"   Priority: {story.priority.value.upper()}")
        print(f"   Assigned to: {story.assigned_to or 'Unassigned'}")
        print(f"   Effort: {story.estimated_effort} points")
        print(f"   Created: {story.created_at}")
        print(f"   Updated: {story.updated_at}")

        if story.description:
            print(
                f"   Description: {story.description[:100]}{'...' if len(story.description) > 100 else ''}"
            )

        if story.acceptance_criteria:
            print("   Acceptance Criteria:")
            for i, criterion in enumerate(story.acceptance_criteria, 1):
                print(f"     {i}. {criterion}")

        if story.tags:
            print(f"   Tags: {', '.join(story.tags)}")

        if story.dependencies:
            print(f"   Dependencies: {', '.join(story.dependencies)}")

        if story.notes:
            print("   Notes:")
            for note in story.notes[-3:]:  # Show last 3 notes
                print(f"     - {note}")


def main():
    """Main function to demonstrate the Ralph Loop Tool"""
    print("🚀 Ralph Loop Tool for User Story Management")
    print("=" * 50)

    # Initialize the tool
    ralph_tool = RalphLoopTool()

    # Demonstrate the Ralph Loop with an example story

    # Phase 1: Recognize
    print("\n📋 PHASE 1: RECOGNIZE")
    story = ralph_tool.recognize_story(
        title="Add User Authentication",
        description="As a user, I want to be able to register and login to the application so that I can access personalized features.",
        priority=StoryPriority.HIGH,
        tags=["security", "authentication", "users"],
        dependencies=[],
    )
    ralph_tool.print_story_summary(story)

    # Phase 2: Analyze
    print("\n🔍 PHASE 2: ANALYZE")
    story = ralph_tool.analyze_story(
        story_id=story.id,
        acceptance_criteria=[
            "User can register with email and password",
            "User can login with registered credentials",
            "Password is securely hashed",
            "Email validation is performed",
            "Appropriate error messages are shown for invalid inputs",
        ],
        estimated_effort=5,
    )
    ralph_tool.print_story_summary(story)

    # Phase 3: Localize
    print("\n📍 PHASE 3: LOCALIZE")
    story = ralph_tool.localize_story(
        story_id=story.id,
        scope="Implement authentication endpoints, user database schema, and frontend forms",
        impact="Enables all future personalized features; requires database migration",
        assigned_to="auth-team",
    )
    ralph_tool.print_story_summary(story)

    # Phase 4: Handle
    print("\n🔧 PHASE 4: HANDLE")
    story = ralph_tool.handle_story(
        story_id=story.id,
        implementation_notes="Implemented JWT-based authentication with bcrypt password hashing. Added user registration and login endpoints. Created database migration script.",
    )
    ralph_tool.print_story_summary(story)

    # Phase 5: Preserve
    print("\n📚 PHASE 5: PRESERVE")
    story = ralph_tool.preserve_story(
        story_id=story.id,
        lessons_learned="JWT tokens should have reasonable expiration times. Bcrypt work factor needs to be tuned for production. Rate limiting is essential for auth endpoints.",
        documentation_ref="docs/authentication.md",
    )
    ralph_tool.print_story_summary(story)

    # List all stories
    print("\n📋 ALL STORIES:")
    all_stories = ralph_tool.list_stories()
    for story in all_stories:
        print(
            f"  • [{story.status.value[:3].upper()}] {story.title} ({story.priority.value})"
        )

    print("\n🎉 Ralph Loop demonstration completed!")


if __name__ == "__main__":
    main()
