#!/usr/bin/env python3
"""
Interactive script to build processing history for gutAutomate.

This script:
1. Fetches ALL meeting notes emails from Gmail (not just unread)
2. Shows you each one and asks if it was already processed
3. Builds data/processed_meetings.json based on your answers
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gut_automate.core import get_meeting_notes_emails, extract_document_id

def build_processing_history():
    """Interactive script to build processing history."""
    print("=" * 70)
    print("gutAutomate - Processing History Builder")
    print("=" * 70)
    print()
    print("This script will help you build the processing history by showing")
    print("you all meeting notes emails and letting you mark which were processed.")
    print()

    # Fetch ALL emails (including read ones)
    print("Fetching all meeting notes emails from Gmail...")
    print("(This includes both read and unread emails)")
    print()

    # Get emails - need to modify the query to include read emails
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    import pickle

    # Gmail API setup
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    creds = None

    token_path = os.path.expanduser('~/.credentials/gmail_token.pickle')
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("Error: No valid Gmail credentials found.")
            print("Please run the main gutAutomate script first to authenticate.")
            return

    service = build('gmail', 'v1', credentials=creds)

    # Search for all meeting notes emails (read and unread) from last 30 days
    query = 'from:gemini-app-noreply@google.com subject:("Notes:") newer_than:30d'

    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=100
    ).execute()

    messages = results.get('messages', [])

    if not messages:
        print("No meeting notes emails found in the last 30 days.")
        return

    print(f"Found {len(messages)} meeting notes emails\n")
    print("=" * 70)
    print()

    # Get full details for each email
    emails = []
    for msg in messages:
        full_msg = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        headers = {h['name']: h['value'] for h in full_msg['payload']['headers']}
        subject = headers.get('Subject', '')
        date = headers.get('Date', '')

        # Extract meeting notes link
        meeting_notes_link = None
        if 'parts' in full_msg['payload']:
            for part in full_msg['payload']['parts']:
                if part['mimeType'] == 'text/html':
                    import base64
                    html_content = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    import re
                    link_match = re.search(r'https://docs\.google\.com/document/d/([a-zA-Z0-9_-]+)', html_content)
                    if link_match:
                        meeting_notes_link = link_match.group(0)
                        break

        emails.append({
            'email_id': msg['id'],
            'subject': subject,
            'date': date,
            'meeting_notes_link': meeting_notes_link
        })

    # Sort by date (newest first)
    emails.sort(key=lambda x: x['date'], reverse=True)

    # Interactive review
    processed_meetings = []

    for i, email in enumerate(emails, 1):
        meeting_title = email['subject'].replace('Notes: ', '').strip('"')
        doc_id = extract_document_id(email['meeting_notes_link']) if email['meeting_notes_link'] else None

        print(f"\n{'=' * 70}")
        print(f"Email {i} of {len(emails)}")
        print(f"{'=' * 70}")
        print(f"Meeting: {meeting_title}")
        print(f"Date: {email['date']}")
        print(f"Email ID: {email['email_id']}")
        if doc_id:
            print(f"Doc ID: {doc_id}")
        print()

        # Ask if already processed
        while True:
            response = input("Was this meeting already processed? (y/n/skip): ").lower().strip()
            if response in ['y', 'yes']:
                # Ask how many tasks
                task_count = input("  How many tasks were created? (enter number or 'unknown'): ").strip()
                if task_count.isdigit():
                    task_count = int(task_count)
                else:
                    task_count = 0

                processed_meetings.append({
                    'doc_id': doc_id or '',
                    'meeting_title': meeting_title,
                    'email_id': email['email_id'],
                    'processed_date': 'backfilled',
                    'tasks_created': [{'task_id': '', 'task_name': f'Task {j+1}', 'list_id': ''} for j in range(task_count)]
                })
                print(f"  ✓ Marked as processed ({task_count} tasks)")
                break
            elif response in ['n', 'no']:
                print(f"  ⏭️  Marked as NOT processed")
                break
            elif response == 'skip':
                print(f"  ⏭️  Skipped")
                break
            else:
                print("  Please enter 'y', 'n', or 'skip'")

    # Save to file
    if processed_meetings:
        print(f"\n{'=' * 70}")
        print(f"Building processing history...")
        print(f"{'=' * 70}\n")

        history_data = {
            'version': '1.0',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'meetings': processed_meetings
        }

        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)

        # Save to file
        with open('data/processed_meetings.json', 'w') as f:
            json.dump(history_data, f, indent=2)

        print(f"✓ Created processing history with {len(processed_meetings)} meetings")
        print(f"✓ Saved to: data/processed_meetings.json")
        print()
        print("You can now run gutAutomate and it will skip these meetings!")
    else:
        print("\nNo meetings marked as processed. Processing history not created.")

if __name__ == '__main__':
    try:
        build_processing_history()
    except KeyboardInterrupt:
        print("\n\n✗ Cancelled by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
