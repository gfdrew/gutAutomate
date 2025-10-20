#!/usr/bin/env python3
"""
Test script to show how gutAutomate.py prepares tasks for MCP integration.
This demonstrates the JSON structure that Claude Code would receive.
"""

import json
import sys

# Sample prepared tasks from gutAutomate (this would come from the script)
sample_prepared_tasks = {
    "list_id": "901112154120",  # Holiday CTV 2025
    "meeting_title": "BevMo Recurring StandUp",
    "count": 5,
    "prepared_tasks": [
        {
            "name": "Provide realistic budget for shoot",
            "markdown_description": """**Action Item:** Provide realistic budget for shoot

**Context from Meeting:**
Discussion about budget requirements for the upcoming shoot. Team needs accurate cost estimates to move forward with planning.

**Source:** BevMo Recurring StandUp""",
            "tags": ["bevmo", "meeting-action-item"],
            "assignees": ["rose@gutfeeling.agency"],
            "priority": None
        },
        {
            "name": "Confirm graphic outro card details",
            "markdown_description": """**Action Item:** Confirm graphic outro card details

**Context from Meeting:**
Need to finalize the design and content for the outro card that will appear at the end of the video.

**Source:** BevMo Recurring StandUp""",
            "tags": ["bevmo", "meeting-action-item"],
            "assignees": ["rose@gutfeeling.agency"],
            "priority": None
        },
        {
            "name": "Confirm discussion points and send invite",
            "markdown_description": """**Action Item:** Confirm discussion points and send invite

**Context from Meeting:**
Prepare agenda for client meeting and send calendar invite to all stakeholders.

**Source:** BevMo Recurring StandUp""",
            "tags": ["bevmo", "meeting-action-item"],
            "assignees": ["rose@gutfeeling.agency"],
            "priority": None
        },
        {
            "name": "Include Total Wine references in concept",
            "markdown_description": """**Action Item:** Include Total Wine references in concept

**Context from Meeting:**
Make sure creative concept includes appropriate references to Total Wine brand elements and style guide.

**Source:** BevMo Recurring StandUp""",
            "tags": ["bevmo", "meeting-action-item"],
            "assignees": ["art@gutfeeling.agency"],
            "priority": None
        },
        {
            "name": "Go over shot list tonight",
            "markdown_description": """**Action Item:** Go over shot list tonight

**Context from Meeting:**
Review and finalize the complete shot list before production begins. Time-sensitive.

**Source:** BevMo Recurring StandUp""",
            "tags": ["bevmo", "meeting-action-item"],
            "assignees": ["art@gutfeeling.agency"],
            "priority": "urgent"
        }
    ]
}

print("=" * 80)
print("SAMPLE: gutAutomate.py OUTPUT FOR CLAUDE CODE MCP INTEGRATION")
print("=" * 80)
print(f"\nMeeting: {sample_prepared_tasks['meeting_title']}")
print(f"Tasks Prepared: {sample_prepared_tasks['count']}")
print(f"Destination List ID: {sample_prepared_tasks['list_id']}")
print("\n" + "=" * 80)
print("JSON STRUCTURE FOR MCP TOOLS")
print("=" * 80)
print(json.dumps(sample_prepared_tasks, indent=2))
print("\n" + "=" * 80)
print("NEXT STEPS (handled by Claude Code)")
print("=" * 80)
print("""
Claude Code would now call:
  mcp__clickup__clickup_create_bulk_tasks(
    list_id='901112154120',
    tasks=[...prepared_tasks...]
  )

All task context, assignees, tags, and priorities are preserved!
""")
