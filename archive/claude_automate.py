#!/usr/bin/env python3
"""
claude_automate.py - Wrapper for running gutAutomate with Claude Code approval

This script is meant to be called BY Claude Code, not run directly.
It outputs JSON so Claude Code can parse it and use AskUserQuestion for approval.
"""

import sys
import json
sys.path.insert(0, '.')

from gutAutomate import (
    find_gemini_meeting_notes,
    get_meeting_notes_content,
    parse_action_items,
    smart_destination_detection,
    mark_emails_as_read,
    copy_doc_to_shared_drive,
    extract_document_id,
    create_clickup_tasks_via_mcp
)

def main():
    """
    Main workflow for Claude Code integration.
    Outputs JSON at each step for Claude Code to parse.
    """

    # Step 1: Find unread emails
    print(json.dumps({
        "step": "find_emails",
        "status": "starting"
    }))

    emails = find_gemini_meeting_notes()

    if not emails:
        print(json.dumps({
            "step": "find_emails",
            "status": "completed",
            "count": 0,
            "emails": []
        }))
        return

    # Format emails for Claude Code
    formatted_emails = []
    for i, email in enumerate(emails):
        meeting_title = email['subject'].replace('Notes: ', '').strip('"')
        formatted_emails.append({
            "index": i,
            "number": i + 1,
            "title": meeting_title,
            "date": email['date'],
            "email_id": email['email_id'],
            "meeting_notes_link": email.get('meeting_notes_link')
        })

    print(json.dumps({
        "step": "find_emails",
        "status": "completed",
        "count": len(emails),
        "emails": formatted_emails
    }))

    # Step 2: Wait for Claude Code to get user approval
    # (Claude Code will use AskUserQuestion and then call this script again with selected indices)

if __name__ == '__main__':
    main()
