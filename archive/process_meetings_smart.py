#!/usr/bin/env python3
"""
process_meetings_smart.py - Smart Meeting Processing for Claude Code

This script processes meetings and outputs JSON for Claude Code to handle:
1. Fetches unread meeting emails
2. Gets meeting content
3. Parses action items
4. Outputs meeting data for Claude Code to:
   - Fetch workspace hierarchy via MCP
   - Run smart destination detection
   - Use AI analysis if needed
   - Create tasks in correct location
"""

import sys
import json
sys.path.insert(0, '.')

from taskUpSolo import (
    find_gemini_meeting_notes,
    get_meeting_notes_content,
    parse_action_items,
    mark_emails_as_read,
    copy_doc_to_shared_drive,
    extract_document_id
)


def main():
    """Main workflow that prepares meeting data for Claude Code."""

    # Step 1: Find unread emails
    print("=" * 60, file=sys.stderr)
    print("STEP 1: Finding unread meeting notes emails", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    emails = find_gemini_meeting_notes()

    if not emails:
        print(json.dumps({
            "status": "no_meetings",
            "count": 0,
            "meetings": []
        }))
        return

    print(f"\nFound {len(emails)} meeting(s)", file=sys.stderr)

    # Step 2: Process each meeting
    meetings_data = []

    for idx, email in enumerate(emails):
        meeting_title = email['subject'].replace('Notes: ', '').strip('"')

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"STEP 2.{idx+1}: Processing '{meeting_title}'", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        if not email.get('meeting_notes_link'):
            print(f"⚠️  No meeting notes link found, skipping", file=sys.stderr)
            continue

        # Copy document to shared drive
        doc_id = extract_document_id(email['meeting_notes_link'])
        if doc_id:
            copy_result = copy_doc_to_shared_drive(doc_id, meeting_title)
            if copy_result.get('success'):
                print(f"✓ Copied to shared drive: {copy_result['url']}", file=sys.stderr)

        # Get meeting content
        content = get_meeting_notes_content(email['meeting_notes_link'])

        if not content:
            print(f"⚠️  Could not fetch meeting content, skipping", file=sys.stderr)
            continue

        print(f"✓ Fetched content ({len(content)} chars)", file=sys.stderr)

        # Parse action items
        action_items = parse_action_items(content, meeting_title, debug=False)
        print(f"✓ Found {len(action_items)} action item(s)", file=sys.stderr)

        # Prepare meeting data for Claude Code
        meetings_data.append({
            'email_id': email['email_id'],
            'meeting_title': meeting_title,
            'meeting_content': content,
            'action_items': action_items,
            'date': email.get('date'),
            # Claude Code will determine destination using:
            # 1. Workspace hierarchy (fetched via MCP)
            # 2. Smart fuzzy matching
            # 3. AI analysis fallback
            'needs_destination': True
        })

    # Mark emails as read
    if meetings_data:
        email_ids = [m['email_id'] for m in meetings_data]
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Marking {len(email_ids)} email(s) as read", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        mark_emails_as_read(email_ids)

    # Output JSON for Claude Code
    output = {
        "status": "success",
        "count": len(meetings_data),
        "meetings": meetings_data,
        "instructions_for_claude": {
            "step_1": "Fetch workspace hierarchy using mcp__clickup__clickup_get_workspace_hierarchy",
            "step_2": "For each meeting, run smart destination detection with fuzzy matching",
            "step_3": "If confidence < 0.5, use AI to analyze meeting content and find best project",
            "step_4": "Create tasks using mcp__clickup__clickup_create_bulk_tasks with detected destination",
            "step_5": "Create notification task for Drew in Automation Summaries list"
        }
    }

    # Output to stdout for Claude Code to parse
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
