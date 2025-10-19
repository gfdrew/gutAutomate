#!/usr/bin/env python3
"""
duplicate_detection.py - Duplicate Task Detection and Update Logic

This module provides functions to:
1. Track processed meetings to avoid re-processing
2. Detect duplicate tasks in ClickUp using fuzzy matching
3. Compare tasks and detect what changed (due date, assignee, etc.)
4. Update existing tasks with new information
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_MEETINGS_FILE = os.path.join(PROJECT_ROOT, 'data', 'processed_meetings.json')


def load_processed_meetings() -> Dict:
    """
    Load the history of processed meetings.

    Returns:
        Dictionary containing processed meeting history
    """
    if not os.path.exists(PROCESSED_MEETINGS_FILE):
        return {
            "version": "1.0",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "meetings": []
        }

    try:
        with open(PROCESSED_MEETINGS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Error loading processed meetings: {e}")
        return {"version": "1.0", "meetings": []}


def save_processed_meetings(data: Dict):
    """
    Save processed meetings history to file.

    Args:
        data: Dictionary containing meeting history
    """
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(PROCESSED_MEETINGS_FILE), exist_ok=True)

        data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(PROCESSED_MEETINGS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️  Error saving processed meetings: {e}")


def check_meeting_processed(doc_id: str = None, meeting_title: str = None, email_id: str = None) -> Optional[Dict]:
    """
    Check if a meeting has already been processed.

    Can check by doc_id, email_id, or both.

    Args:
        doc_id: Google Doc ID of the meeting notes (optional)
        meeting_title: Title of the meeting (optional)
        email_id: Gmail email ID (optional)

    Returns:
        Meeting data if previously processed, None otherwise
    """
    data = load_processed_meetings()

    for meeting in data.get('meetings', []):
        # Check by doc_id if provided
        if doc_id and meeting.get('doc_id') == doc_id:
            return meeting

        # Check by email_id if provided
        if email_id and meeting.get('email_id') == email_id:
            return meeting

    return None


def record_processed_meeting(doc_id: str, meeting_title: str, email_id: str,
                            tasks_created: List[Dict]):
    """
    Record that a meeting has been processed.

    Args:
        doc_id: Google Doc ID of the meeting notes
        meeting_title: Title of the meeting
        email_id: Gmail email ID
        tasks_created: List of tasks that were created
    """
    data = load_processed_meetings()

    meeting_record = {
        "doc_id": doc_id,
        "meeting_title": meeting_title,
        "email_id": email_id,
        "processed_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tasks_created": tasks_created
    }

    data['meetings'].append(meeting_record)
    save_processed_meetings(data)


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity between two strings using SequenceMatcher.

    Args:
        str1: First string
        str2: Second string

    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Normalize strings
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()

    return SequenceMatcher(None, s1, s2).ratio()


def find_similar_tasks(new_task: Dict, existing_tasks: List[Dict],
                      threshold: float = 0.85) -> List[Tuple[Dict, float]]:
    """
    Find similar tasks in the existing task list using fuzzy matching.

    Args:
        new_task: The new task to check
        existing_tasks: List of existing tasks in ClickUp
        threshold: Similarity threshold (0.0 to 1.0)

    Returns:
        List of tuples (task, similarity_score) sorted by similarity (highest first)
    """
    matches = []
    new_task_name = new_task.get('name', '')

    for existing_task in existing_tasks:
        existing_name = existing_task.get('name', '')

        # Calculate similarity
        similarity = calculate_similarity(new_task_name, existing_name)

        if similarity >= threshold:
            matches.append((existing_task, similarity))

    # Sort by similarity (highest first)
    matches.sort(key=lambda x: x[1], reverse=True)

    return matches


def compare_tasks(new_task: Dict, existing_task: Dict) -> Dict:
    """
    Compare new task with existing task to find what changed.

    Args:
        new_task: The new task data
        existing_task: The existing task from ClickUp

    Returns:
        Dictionary of changes with keys like 'due_date_changed', 'assignee_changed', etc.
    """
    changes = {
        'has_changes': False,
        'due_date_changed': False,
        'assignee_changed': False,
        'description_different': False,
        'new_due_date': None,
        'old_due_date': None,
        'new_assignee': None,
        'old_assignee': None,
        'new_description': None,
        'old_description': None
    }

    # Check due date
    new_due = new_task.get('due_date')
    old_due = existing_task.get('due_date')

    if new_due and new_due != old_due:
        changes['due_date_changed'] = True
        changes['has_changes'] = True
        changes['new_due_date'] = new_due
        changes['old_due_date'] = old_due

    # Check assignee
    new_assignees = new_task.get('assignees', [])
    old_assignees = existing_task.get('assignees', [])

    # Extract IDs for comparison
    new_assignee_ids = [a.get('id') if isinstance(a, dict) else a for a in new_assignees]
    old_assignee_ids = [a.get('id') if isinstance(a, dict) else a for a in old_assignees]

    if set(new_assignee_ids) != set(old_assignee_ids):
        changes['assignee_changed'] = True
        changes['has_changes'] = True
        changes['new_assignee'] = new_assignees
        changes['old_assignee'] = old_assignees

    # Check description
    new_desc = new_task.get('description', '').strip()
    old_desc = existing_task.get('description', '').strip()

    if new_desc and new_desc != old_desc:
        # Check if new description adds information
        similarity = calculate_similarity(new_desc, old_desc)
        if similarity < 0.95:  # Not exactly the same
            changes['description_different'] = True
            changes['has_changes'] = True
            changes['new_description'] = new_desc
            changes['old_description'] = old_desc

    return changes


def format_changes_summary(changes: Dict) -> str:
    """
    Format changes into a human-readable summary.

    Args:
        changes: Dictionary from compare_tasks()

    Returns:
        Formatted string describing changes
    """
    if not changes.get('has_changes'):
        return "No changes detected"

    summary = []

    if changes.get('due_date_changed'):
        old_date = changes.get('old_due_date', 'None')
        new_date = changes.get('new_due_date', 'None')
        summary.append(f"Due date: {old_date} → {new_date}")

    if changes.get('assignee_changed'):
        summary.append("Assignee changed")

    if changes.get('description_different'):
        summary.append("Description has new information")

    return " | ".join(summary)


def create_update_comment(meeting_title: str, changes: Dict) -> str:
    """
    Create a comment to add to the task explaining the update.

    Args:
        meeting_title: Title of the meeting where update came from
        changes: Dictionary from compare_tasks()

    Returns:
        Comment text
    """
    comment_parts = [
        f"Updated from meeting: **{meeting_title}**",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ]

    if changes.get('due_date_changed'):
        old_date = changes.get('old_due_date', 'None')
        new_date = changes.get('new_due_date')
        comment_parts.append(f"Due date changed: {old_date} → {new_date}")

    if changes.get('assignee_changed'):
        comment_parts.append("Assignee updated")

    if changes.get('description_different'):
        comment_parts.append("New information added to description")

    return "\n".join(comment_parts)


def merge_descriptions(old_desc: str, new_desc: str) -> str:
    """
    Merge old and new descriptions intelligently.

    Args:
        old_desc: Existing task description
        new_desc: New description from meeting notes

    Returns:
        Merged description
    """
    if not old_desc:
        return new_desc

    if not new_desc:
        return old_desc

    # If they're very similar, just keep the old one
    if calculate_similarity(old_desc, new_desc) > 0.95:
        return old_desc

    # Otherwise, append with separator
    separator = "\n\n---\nUpdated from new meeting notes:\n"
    return old_desc + separator + new_desc


def get_task_url(task_id: str, team_id: str = None) -> str:
    """
    Generate ClickUp task URL.

    Args:
        task_id: ClickUp task ID
        team_id: Team/workspace ID (optional)

    Returns:
        URL to the task
    """
    if team_id:
        return f"https://app.clickup.com/t/{team_id}/{task_id}"
    return f"https://app.clickup.com/t/{task_id}"
