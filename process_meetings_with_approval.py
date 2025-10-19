#!/usr/bin/env python3
"""
process_meetings_with_approval.py - Meeting Processing with Claude Code Approval

This script processes meetings and outputs data for Claude Code to show the user
for approval before creating tasks.

Workflow:
1. Find unread meeting notes emails
2. Fetch content and parse action items
3. Output JSON for Claude Code to:
   - Show user the meetings found
   - Detect destinations (with confidence scores)
   - Show user all tasks that will be created
   - Get approval before creating anything
"""

import sys
import json
sys.path.insert(0, '.')

from taskUpSolo import (
    find_gemini_meeting_notes,
    get_meeting_notes_content,
    parse_action_items,
    extract_document_id
)


def main():
    """Main workflow that prepares meeting data for approval."""

    # Step 1: Find unread emails
    print("\n" + "="*60, file=sys.stderr)
    print("FINDING UNREAD MEETING NOTES", file=sys.stderr)
    print("="*60, file=sys.stderr)

    emails = find_gemini_meeting_notes()

    if not emails:
        # No meetings to process
        print(json.dumps({
            "status": "no_meetings",
            "message": "No unread meeting notes found.",
            "count": 0
        }))
        return

    print(f"\nFound {len(emails)} unread meeting(s)", file=sys.stderr)

    # Step 2: Process each meeting (but don't create tasks yet)
    meetings_data = []

    for idx, email in enumerate(emails):
        meeting_title = email['subject'].replace('Notes: ', '').strip('"')

        # Remove "Fwd: " prefix if present
        if meeting_title.startswith('Fwd: '):
            meeting_title = meeting_title[5:]

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"PROCESSING: {meeting_title}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        if not email.get('meeting_notes_link'):
            print(f"⚠️  No meeting notes link found, skipping", file=sys.stderr)
            continue

        # Get document ID for reference
        doc_id = extract_document_id(email['meeting_notes_link'])

        # Get meeting content
        content = get_meeting_notes_content(email['meeting_notes_link'])

        if not content:
            print(f"⚠️  Could not fetch meeting content, skipping", file=sys.stderr)
            continue

        print(f"✓ Fetched content ({len(content)} chars)", file=sys.stderr)

        # Parse action items
        action_items = parse_action_items(content, meeting_title, debug=False)
        print(f"✓ Found {len(action_items)} action item(s)", file=sys.stderr)

        # Convert action items for JSON serialization (remove date_obj which isn't serializable)
        serializable_items = []
        for item in action_items:
            serializable_item = item.copy()
            # Remove date_obj if present (keep date_string and due_date_ms)
            if 'due_date' in serializable_item and serializable_item['due_date']:
                if isinstance(serializable_item['due_date'], dict) and 'date_obj' in serializable_item['due_date']:
                    serializable_item['due_date'] = {
                        'date_string': serializable_item['due_date'].get('date_string'),
                        'due_date_ms': serializable_item['due_date'].get('due_date_ms')
                    }
            serializable_items.append(serializable_item)

        # Prepare meeting data for Claude Code approval
        meetings_data.append({
            'email_id': email['email_id'],
            'meeting_title': meeting_title,
            'meeting_content': content,
            'action_items': serializable_items,
            'date': email.get('date'),
            'doc_id': doc_id,
            'doc_url': email.get('meeting_notes_link'),
            'needs_destination_detection': True
        })

    if not meetings_data:
        print(json.dumps({
            "status": "no_valid_meetings",
            "message": "No meetings with valid content found.",
            "count": 0
        }))
        return

    # Output JSON for Claude Code to handle approval
    output = {
        "status": "awaiting_approval",
        "count": len(meetings_data),
        "meetings": meetings_data,
        "workflow": {
            "step_1": "Show user meetings found with action item counts",
            "step_2": "For each meeting, detect destination using workspace hierarchy + AI",
            "step_3": "Show user all tasks with destinations and confidence scores",
            "step_4": "Get user approval (all/select/none)",
            "step_5": "Create approved tasks using MCP",
            "step_6": "Mark emails as read",
            "step_7": "Copy docs to shared drive",
            "step_8": "Create notification for Drew"
        }
    }

    # Output to stdout for Claude Code
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
