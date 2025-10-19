#!/usr/bin/env python3
"""
gutAutomate - Google Drive and Gmail Automation

Usage:
    python3 gutAutomate.py           # Standalone mode (prepares tasks only)
    python3 gutAutomate.py claude    # Claude mode (creates tasks via MCP)
"""

import os
import os.path
import re
import base64
import sys
import argparse
import json
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv(os.path.join(SCRIPT_DIR, '.env'))

# Check if we're in batch mode (non-interactive)
BATCH_MODE = os.getenv('BATCH_MODE', 'false').lower() == 'true'

def get_user_input(prompt, default='y'):
    """
    Get user input or return default if in batch mode.

    Args:
        prompt: The prompt to display to the user
        default: The default value to return in batch mode

    Returns:
        User input string or default value
    """
    if BATCH_MODE:
        print(f"{prompt} [BATCH MODE: auto-selecting '{default}']")
        return default
    return input(prompt).strip()


def prompt_duplicate_action(new_task, existing_task, similarity, changes):
    """
    Prompt user for action when duplicate task is found.

    Args:
        new_task: The new task dict
        existing_task: The existing task from ClickUp
        similarity: Similarity score (0.0 to 1.0)
        changes: Dict from compare_tasks()

    Returns:
        str: 'skip', 'update', or 'create'
    """
    from gut_automate.duplicate_detection import format_changes_summary, get_task_url

    print("\n" + "="*70)
    print("⚠️  POTENTIAL DUPLICATE DETECTED")
    print("="*70)

    print(f"\n📋 Existing Task ({int(similarity*100)}% match):")
    print(f"   Name: {existing_task.get('name', 'Unknown')}")
    print(f"   ID: {existing_task.get('id')}")
    print(f"   URL: {get_task_url(existing_task.get('id'))}")
    print(f"   Status: {existing_task.get('status', {}).get('status', 'Unknown')}")

    assignees = existing_task.get('assignees', [])
    if assignees:
        assignee_names = [a.get('username', 'Unknown') for a in assignees]
        print(f"   Assignees: {', '.join(assignee_names)}")

    due_date = existing_task.get('due_date')
    if due_date:
        print(f"   Due Date: {due_date}")

    print(f"\n🆕 New Task:")
    print(f"   Name: {new_task.get('name', 'Unknown')}")

    new_assignees = new_task.get('assignees', [])
    if new_assignees:
        print(f"   Assignees: {', '.join(new_assignees)}")

    new_due = new_task.get('due_date')
    if new_due:
        print(f"   Due Date: {new_due}")

    # Show changes if any
    if changes.get('has_changes'):
        print(f"\n📝 Detected Changes:")
        print(f"   {format_changes_summary(changes)}")

    print("\n" + "="*70)
    print("What would you like to do?")
    print("  1) Skip - Don't create (task already exists)")
    print("  2) Update - Update existing task with new information")
    print("  3) Create - Create new task anyway (ignore duplicate)")
    print("="*70)

    if BATCH_MODE:
        print("[BATCH MODE: auto-selecting 'skip']")
        return 'skip'

    choice = input("\nYour choice (1/2/3): ").strip()

    if choice == '1':
        return 'skip'
    elif choice == '2':
        return 'update'
    elif choice == '3':
        return 'create'
    else:
        print("Invalid choice. Defaulting to 'skip'.")
        return 'skip'


# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/drive',  # Full Drive access for copying files
    'https://www.googleapis.com/auth/gmail.modify',  # Read and modify Gmail
    'https://www.googleapis.com/auth/documents.readonly'  # Read Google Docs
]

def test_gdrive_connection():
    """Test Google Drive API connection and list some files."""
    creds = None

    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Build the Drive service
        service = build('drive', 'v3', credentials=creds)

        print(" Successfully connected to Google Drive!")
        print("\nTesting API by listing first 3 files (sorted by modified time):")
        print("-" * 50)

        # Call the Drive v3 API to list files, sorted by most recently modified
        results = service.files().list(
            pageSize=3,
            orderBy='modifiedTime desc',
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)"
        ).execute()

        items = results.get('files', [])

        if not items:
            print('No files found in your Google Drive.')
        else:
            print(f'Found {len(items)} files:')
            for item in items:
                print(f"  - {item['name']}")
                print(f"    Type: {item['mimeType']}")
                print(f"    Last Modified: {item['modifiedTime']}")
                print()

        print("\n Google Drive connection test successful!")
        return True

    except HttpError as error:
        print(f' An error occurred: {error}')
        return False

def get_credentials():
    """Get or create credentials for Google APIs."""
    creds = None

    # Use absolute paths relative to the script location
    token_path = os.path.join(SCRIPT_DIR, 'token.json')
    client_secrets_path = os.path.join(SCRIPT_DIR, 'client_secrets.json')

    # The file token.json stores the user's access and refresh tokens
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds


def find_gemini_meeting_notes():
    """
    Step 1: Find and process unread emails from Gemini with 'Notes' in subject.

    Returns:
        list: List of dictionaries containing:
            - email_id: Gmail message ID
            - subject: Email subject line
            - date: Email date
            - meeting_notes_link: Link to open meeting notes
    """
    try:
        creds = get_credentials()
        service = build('gmail', 'v1', credentials=creds)

        print("\nStep 1: Searching for unread Gemini meeting notes emails...")
        print("=" * 60)

        # Search query: unread emails from Gemini with 'Notes' in subject
        query = 'from:gemini is:unread subject:Notes'

        results = service.users().messages().list(
            userId='me',
            q=query
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            print("No unread emails found from Gemini with 'Notes' in subject.")
            return []

        print(f"Found {len(messages)} matching email(s)\n")

        processed_emails = []

        for msg in messages:
            # Get the full message details
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            # Extract headers
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'No Date')

            # Extract body and find meeting notes link
            meeting_notes_link = None

            # Get the email body
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/html' or part['mimeType'] == 'text/plain':
                        body_data = part['body'].get('data', '')
                        if body_data:
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            # Look for Google Docs links (meeting notes)
                            docs_pattern = r'https://docs\.google\.com/document/d/[a-zA-Z0-9_-]+(?:/[^\s<>"\']*)?'
                            match = re.search(docs_pattern, body)
                            if match:
                                meeting_notes_link = match.group(0)
                                break
            else:
                # No parts, body is directly in payload
                body_data = message['payload']['body'].get('data', '')
                if body_data:
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                    docs_pattern = r'https://docs\.google\.com/document/d/[a-zA-Z0-9_-]+(?:/[^\s<>"\']*)?'
                    match = re.search(docs_pattern, body)
                    if match:
                        meeting_notes_link = match.group(0)

            email_info = {
                'email_id': msg['id'],
                'subject': subject,
                'date': date,
                'meeting_notes_link': meeting_notes_link
            }

            processed_emails.append(email_info)

            # Print the extracted info
            print(f"Email ID: {msg['id']}")
            print(f"Subject: {subject}")
            print(f"Date: {date}")
            print(f"Meeting Notes Link: {meeting_notes_link or 'NOT FOUND'}")
            print("-" * 60)

        print(f"\nSuccessfully processed {len(processed_emails)} email(s)")
        return processed_emails

    except HttpError as error:
        print(f'An error occurred: {error}')
        return []


def copy_doc_to_shared_drive(doc_id, doc_title):
    """
    Copy a Google Doc to the Collective Meeting Notes shared drive.

    Args:
        doc_id: Google Doc ID to copy
        doc_title: Title for the copied document

    Returns:
        dict: Copy result with success status and file info
    """
    try:
        creds = get_credentials()
        drive_service = build('drive', 'v3', credentials=creds)

        # First, find the "Collective Meeting Notes" shared drive folder
        # Search for shared drives
        shared_drives = drive_service.drives().list().execute()

        target_folder_id = None
        for drive in shared_drives.get('drives', []):
            if 'Collective Meeting Notes' in drive['name']:
                target_folder_id = drive['id']
                print(f"Found shared drive: {drive['name']} (ID: {target_folder_id})")
                break

        if not target_folder_id:
            print("⚠️  Could not find 'Collective Meeting Notes' shared drive")
            return {'success': False, 'error': 'Shared drive not found'}

        # Copy the document to the shared drive
        print(f"\nCopying document: {doc_title}")
        print(f"Destination: Collective Meeting Notes")

        copied_file = drive_service.files().copy(
            fileId=doc_id,
            body={
                'name': doc_title,
                'parents': [target_folder_id]
            },
            supportsAllDrives=True
        ).execute()

        copied_file_id = copied_file.get('id')
        copied_file_url = f"https://docs.google.com/document/d/{copied_file_id}/edit"

        print(f"✓ Document copied successfully!")
        print(f"  File ID: {copied_file_id}")
        print(f"  URL: {copied_file_url}")

        return {
            'success': True,
            'file_id': copied_file_id,
            'url': copied_file_url,
            'title': doc_title
        }

    except HttpError as error:
        print(f'Error copying document: {error}')
        return {'success': False, 'error': str(error)}


def mark_emails_as_read(email_ids):
    """
    Mark specified emails as read by removing the UNREAD label.

    Args:
        email_ids: List of Gmail message IDs to mark as read

    Returns:
        int: Number of emails successfully marked as read
    """
    if not email_ids:
        return 0

    try:
        creds = get_credentials()
        service = build('gmail', 'v1', credentials=creds)

        successful_count = 0
        for email_id in email_ids:
            try:
                # Remove the UNREAD label
                service.users().messages().modify(
                    userId='me',
                    id=email_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
                successful_count += 1
            except HttpError as error:
                print(f'Error marking email {email_id} as read: {error}')

        print(f"✓ Marked {successful_count} email(s) as read")
        return successful_count

    except HttpError as error:
        print(f'An error occurred: {error}')
        return 0


def extract_document_id(url):
    """Extract document ID from Google Docs URL."""
    match = re.search(r'/document/d/([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None


def get_meeting_notes_content(doc_url):
    """
    Step 2: Fetch the content of a Google Doc meeting notes.

    Args:
        doc_url: URL of the Google Doc

    Returns:
        str: The text content of the document
    """
    try:
        creds = get_credentials()
        service = build('docs', 'v1', credentials=creds)

        # Extract document ID from URL
        doc_id = extract_document_id(doc_url)
        if not doc_id:
            print(f"Could not extract document ID from URL: {doc_url}")
            return None

        print(f"\nStep 2: Fetching meeting notes content...")
        print("=" * 60)
        print(f"Document ID: {doc_id}\n")

        # Retrieve the document
        document = service.documents().get(documentId=doc_id).execute()

        # Extract text content
        content = []
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for text_run in paragraph.get('elements', []):
                    if 'textRun' in text_run:
                        content.append(text_run['textRun']['content'])

        full_text = ''.join(content)

        # Clean up Google Docs special characters and formatting artifacts
        # These can cause issues with parsing and display
        special_chars = [
            '\u2610',  # ☐ Empty checkbox
            '\u2611',  # ☑ Checked checkbox
            '\u2612',  # ☒ Checked checkbox with X
            '\ufffc',  # Object replacement character
            '\u200b',  # Zero-width space
            '\u200c',  # Zero-width non-joiner
            '\u200d',  # Zero-width joiner
            '\ufeff',  # Zero-width no-break space (BOM)
            '\u00a0',  # Non-breaking space
        ]

        for char in special_chars:
            full_text = full_text.replace(char, '')

        print(f"Successfully retrieved document content ({len(full_text)} characters)")
        return full_text

    except HttpError as error:
        print(f'An error occurred: {error}')
        return None


def show_meeting_notes_content(notes_content):
    """Display the raw meeting notes content for review."""
    print("\n[DEBUG] Meeting Notes Content:")
    print("=" * 60)
    print(notes_content)
    print("=" * 60)


def extract_details_section(notes_content):
    """Extract the Details section from meeting notes."""
    details_match = re.search(
        r'Details[\s:]*\n(.*?)(?:Suggested next steps|Action items|Next steps|$)',
        notes_content,
        re.IGNORECASE | re.DOTALL
    )
    return details_match.group(1).strip() if details_match else ""


def extract_meeting_date(meeting_title):
    """
    Extract the date from the meeting title.

    Args:
        meeting_title: Title like "BevMo Recurring StandUp Oct 17, 2025"

    Returns:
        datetime: The meeting date, or current date if not found
    """
    from datetime import datetime
    import re

    # Look for date patterns like "Oct 17, 2025" or "October 17, 2025"
    date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})'
    match = re.search(date_pattern, meeting_title, re.IGNORECASE)

    if match:
        month_abbr = match.group(1)
        day = int(match.group(2))
        year = int(match.group(3))

        # Convert month abbreviation to month number
        months = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        month = months.get(month_abbr.lower()[:3])

        if month:
            try:
                return datetime(year, month, day)
            except:
                pass

    # Fallback to current date
    return datetime.now()


def extract_due_date(task_text, context="", meeting_date=None):
    """
    Extract or infer due date from task text and context.

    Args:
        task_text: The action item text
        context: Additional context from meeting
        meeting_date: The date of the meeting (datetime object)

    Returns:
        dict: Contains 'date_string' (human readable) and 'due_date_ms' (timestamp in ms)
              Defaults to meeting_date if no date can be inferred from text
    """
    from datetime import datetime, timedelta
    import calendar

    combined_text = f"{task_text} {context}".lower()

    # Use meeting date as reference point, or current date if not provided
    if meeting_date:
        reference_date = meeting_date
    else:
        reference_date = datetime.now()

    # Patterns for date extraction (using reference_date instead of today)
    patterns = {
        # Explicit dates
        r'by the end of (?:the )?day|end of day|eod': lambda: reference_date.replace(hour=23, minute=59),
        r'today': lambda: reference_date.replace(hour=23, minute=59),
        r'tonight': lambda: reference_date.replace(hour=23, minute=59),
        r'tomorrow': lambda: reference_date + timedelta(days=1),

        # Day of week references
        r'(?:by |for |on )?monday': lambda: reference_date + timedelta(days=(7 - reference_date.weekday()) % 7 or 7) if reference_date.weekday() != 0 else reference_date + timedelta(days=7),
        r'(?:by |for |on )?tuesday': lambda: reference_date + timedelta(days=(1 - reference_date.weekday()) % 7 or 7),
        r'(?:by |for |on )?wednesday': lambda: reference_date + timedelta(days=(2 - reference_date.weekday()) % 7 or 7),
        r'(?:by |for |on )?thursday': lambda: reference_date + timedelta(days=(3 - reference_date.weekday()) % 7 or 7),
        r'(?:by |for |on )?friday': lambda: reference_date + timedelta(days=(4 - reference_date.weekday()) % 7 or 7),

        # Relative time
        r'in advance': lambda: reference_date + timedelta(days=1),  # Tomorrow if "in advance"
        r'this week': lambda: reference_date + timedelta(days=(4 - reference_date.weekday()) % 7),  # End of week
        r'next week': lambda: reference_date + timedelta(days=7),
    }

    for pattern, date_func in patterns.items():
        if re.search(pattern, combined_text):
            due_date = date_func()
            # Convert to milliseconds timestamp (ClickUp format)
            due_date_ms = int(due_date.timestamp() * 1000)

            # Create human readable date string
            date_string = due_date.strftime("%B %d, %Y")

            return {
                'date_string': date_string,
                'due_date_ms': due_date_ms,
                'date_obj': due_date
            }

    # No date pattern found - default to meeting date (or reference date)
    due_date = reference_date
    due_date_ms = int(due_date.timestamp() * 1000)
    date_string = due_date.strftime("%B %d, %Y")

    return {
        'date_string': date_string,
        'due_date_ms': due_date_ms,
        'date_obj': due_date
    }


def find_relevant_context(task_text, details_section, assignee=None):
    """
    Find relevant context from the Details section for a given task.
    Includes timestamps from transcript if found.

    Args:
        task_text: The action item text
        details_section: The full Details section content
        assignee: The person assigned to the task

    Returns:
        str: Relevant context paragraph(s) with timestamps or empty string
    """
    if not details_section:
        return ""

    # Extract key terms from the task
    key_terms = []

    # Add assignee name as a key term
    if assignee:
        key_terms.append(assignee.lower())

    # Extract important keywords from task (nouns, verbs)
    task_lower = task_text.lower()
    keywords = [
        'budget', 'shot list', 'production brief', 'graphic', 'outro card',
        'meeting', 'assets', 'deliverables', 'brand', 'references',
        'total wine', 'bevmo', 'client', 'agency', 'location', 'tonight',
        'monday', 'today', 'tomorrow', 'week', 'deadline', 'due'
    ]

    for keyword in keywords:
        if keyword in task_lower:
            key_terms.append(keyword)

    # Split details into paragraphs
    paragraphs = re.split(r'\n(?=[A-Z][a-z]+ [A-Z][a-z]+)', details_section)

    # Score each paragraph based on matching key terms
    scored_paragraphs = []
    for para in paragraphs:
        if len(para.strip()) < 50:  # Skip very short paragraphs
            continue

        para_lower = para.lower()
        score = sum(1 for term in key_terms if term in para_lower)

        if score > 0:
            # Keep timestamps in the paragraph (format: 00:00:00 or (00:00:00))
            # These are already in the text, so no need to extract separately
            scored_paragraphs.append((score, para.strip()))

    # Sort by score and take top matches
    scored_paragraphs.sort(reverse=True, key=lambda x: x[0])

    # Return top 1-2 most relevant paragraphs
    # Timestamps are preserved in the original paragraph text
    relevant_context = []
    for score, para in scored_paragraphs[:2]:
        if score >= 1:  # At least one matching term
            # Clean up the paragraph but keep timestamps
            cleaned_para = para.replace('\n', ' ')  # Join multiline paragraphs
            relevant_context.append(cleaned_para)

    return "\n\n".join(relevant_context)


def load_assignee_mapping():
    """
    Load assignee name-to-email mapping from environment variable.

    Returns:
        dict: Mapping of names (lowercase) to emails
    """
    assignee_map = {}
    map_str = os.getenv('ASSIGNEE_MAP', '')

    if map_str:
        # Parse comma-separated name=email pairs
        for pair in map_str.split(','):
            pair = pair.strip()
            if '=' in pair:
                name, email = pair.split('=', 1)
                # Store lowercase name for case-insensitive matching
                assignee_map[name.strip().lower()] = email.strip()

    return assignee_map


def get_ignored_assignees():
    """
    Get list of names to ignore when assigning tasks.

    Returns:
        list: List of names (lowercase) to never assign tasks to
    """
    ignore_str = os.getenv('IGNORE_ASSIGNEES', '')
    if ignore_str:
        return [name.strip().lower() for name in ignore_str.split(',')]
    return []


def resolve_assignee_email(name):
    """
    Resolve a person's name to their ClickUp email address.

    Args:
        name: Person's name as mentioned in meeting notes

    Returns:
        str: Email address or original name if not found
    """
    if not name:
        return None

    # Load the mapping
    assignee_map = load_assignee_mapping()

    # Try exact match (case-insensitive)
    name_lower = name.lower()
    if name_lower in assignee_map:
        return assignee_map[name_lower]

    # Try partial match (e.g., "Drew" matches "Drew Smith")
    for map_name, email in assignee_map.items():
        if name_lower in map_name or map_name in name_lower:
            return email

    # If no match found, return None (person not in assignee map)
    # Task will be assigned to DEFAULT_ASSIGNEE instead
    return None


def shorten_task_name(task_text, assignee=None):
    """
    Shorten task name by removing redundant information and verbose phrasing.

    Format pattern:
    - Remove "Person will" prefix (assignee already shown in ClickUp)
    - Start with action verb (Update, Ask, Create, Coordinate, Research, Test, Design, Shoot, etc.)
    - Keep key details (what/why)
    - Remove unnecessary filler words

    Args:
        task_text: Original task text from meeting notes
        assignee: Person assigned (used to remove their name from task)

    Returns:
        str: Shortened task name
    """
    import re

    # Original text for reference
    original = task_text.strip()
    shortened = original

    # Remove assignee name + "will" pattern at start
    # Example: "Matt Rose will update..." → "update..."
    if assignee:
        assignee_pattern = rf'^{re.escape(assignee)}\s+will\s+'
        shortened = re.sub(assignee_pattern, '', shortened, flags=re.IGNORECASE)

    # Remove generic "will" patterns at start
    # Example: "will update..." → "update..."
    shortened = re.sub(r'^(?:will|should|needs? to)\s+', '', shortened, flags=re.IGNORECASE)

    # Remove "Coordinate with [Name] to" and keep the action
    # Example: "Coordinate with Aidan Wilde to create..." → "Create..."
    shortened = re.sub(r'^coordinate with [^t]+to\s+', '', shortened, flags=re.IGNORECASE)

    # Remove verbose phrases and filler words
    replacements = {
        r'\s+separately\s+': ' ',
        r'\s+for anything that was missed during the call\s*': '',
        r'\s+and circulate it for review\s*': ' and circulate',
        r'to see if they are open to': 'about',
        r'45-second or 1-minute': '45-60 sec',
        r'will aim to': '',
        r'the exact\s+': '',
        r'\s+being used': '',
        r'\s+to make sure it is good': '',
        r'\s+and drop the screenshots of the AI test with the transition into Slack': '',
        r'\s+to help with pacing': ' for pacing',
        r'\s+for the script': '',
        r'recreating each scene with a DIY version\s+': '',
    }

    for pattern, replacement in replacements.items():
        shortened = re.sub(pattern, replacement, shortened, flags=re.IGNORECASE)

    # Capitalize first letter
    if shortened:
        shortened = shortened[0].upper() + shortened[1:]

    # Trim and clean up extra spaces
    shortened = ' '.join(shortened.split())

    # If shortened version is too short or same as original, return original
    if len(shortened) < 10:
        return original

    return shortened


def parse_action_items(notes_content, meeting_title="", debug=False):
    """
    Step 3: Parse meeting notes and extract action items.

    Args:
        notes_content: Text content of meeting notes
        debug: If True, show the raw content

    Returns:
        list: List of dictionaries containing action items with:
            - task: The action item text
            - assignee: Person assigned (if mentioned)
            - priority: Estimated priority
            - context: Relevant context from Details section
    """
    print("\nStep 3: Parsing action items from meeting notes...")
    print("=" * 60)

    if debug:
        show_meeting_notes_content(notes_content)

    action_items = []

    # Extract the meeting date from title for due date calculations
    meeting_date = extract_meeting_date(meeting_title) if meeting_title else None
    if meeting_date:
        print(f"Meeting date detected: {meeting_date.strftime('%B %d, %Y')}")

    # Extract the Details section for context matching
    details_section = extract_details_section(notes_content)
    if details_section:
        print(f"Found 'Details' section ({len(details_section)} characters)")

    # First, try to find "Suggested next steps" or "Action items" section
    next_steps_match = re.search(
        r'(?:Suggested next steps|Action items|Next steps|Follow[- ]up|To[- ]?do)[\s:]*\n((?:.*\n)*?)(?:\n\n|$)',
        notes_content,
        re.IGNORECASE
    )

    if next_steps_match:
        next_steps_section = next_steps_match.group(1)
        print(f"Found 'Next Steps' section ({len(next_steps_section)} characters)")

        # Parse each line in the next steps section
        lines = next_steps_section.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or len(line) < 15:  # Skip empty or very short lines
                continue

            # Skip Gemini footer lines
            if any(phrase in line.lower() for phrase in ['you should review', 'please provide feedback', 'get tips and learn']):
                continue

            # Extract all names mentioned in the action item
            # Look for:
            # 1. Full names: "FirstName LastName" (e.g., "Drew Gilbert", "Art Okoro")
            # 2. Single names: "Drew", "Art", "Matt", "Kato", "Paula" (case-insensitive)
            full_names = re.findall(r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b', line)
            single_names = re.findall(r'\b(drew|art|matt|kato|paula)\b', line, re.IGNORECASE)

            # Combine both lists (full names first, then single names)
            all_names = full_names + single_names

            # Get list of names to ignore from environment
            ignored_names = get_ignored_assignees()

            # Filter out ignored names (e.g., Ryan Joseph)
            non_ignored_names = [name for name in all_names if name.lower() not in ignored_names]

            # Determine the assignee: prioritize people in ASSIGNEE_MAP
            assignee = None
            if non_ignored_names:
                # Try to find someone in the ASSIGNEE_MAP first
                for name in non_ignored_names:
                    if resolve_assignee_email(name):
                        # This person is in the map, assign to them
                        assignee = name
                        break

                # If no one in the map was found, use first non-ignored person
                # (they'll be marked as "Mentioned Assignee" later)
                if not assignee:
                    assignee = non_ignored_names[0]

            # Clean up task text: remove checkboxes, bullet points, etc.
            task_text = line
            # Remove checkbox symbols (☐ ☑ ✓ ✗ ☒ □ ■)
            task_text = re.sub(r'^[☐☑✓✗☒□■]\s*', '', task_text)
            # Remove bullet points (-, •, *, etc.)
            task_text = re.sub(r'^[-•*]\s+', '', task_text)
            # Remove numbered list markers (1., 2., etc.)
            task_text = re.sub(r'^\d+\.\s+', '', task_text)
            task_text = task_text.strip()

            # Shorten task name for cleaner ClickUp task titles
            task_name = shorten_task_name(task_text, assignee)

            # Estimate priority based on keywords
            priority = None
            if any(word in task_text.lower() for word in ['urgent', 'asap', 'immediately', 'critical', 'today', 'tonight']):
                priority = 'urgent'
            elif any(word in task_text.lower() for word in ['important', 'priority', 'high']):
                priority = 'high'

            # Find relevant context from Details section
            context = find_relevant_context(task_text, details_section, assignee)

            # Extract due date from task text and context (using meeting date as reference)
            due_date_info = extract_due_date(task_text, context, meeting_date)

            action_items.append({
                'task': task_name,  # Use shortened name
                'original_task': task_text,  # Keep original for description
                'assignee': assignee,
                'priority': priority,
                'context': context,
                'due_date': due_date_info
            })

    # If no next steps section found, try general patterns
    if not action_items:
        print("No 'Next Steps' section found, trying general patterns...")
        patterns = [
            r'(?:^|\n)\s*[-•*]\s*(?:ACTION|TODO|TASK):\s*(.+?)(?:\n|$)',
            r'(?:^|\n)\s*[-•*]\s*(.+?)\s+(?:will|should|needs? to)\s+(.+?)(?:\n|$)',
            r'(?:^|\n)\s*\d+\.\s*(.+?)(?:\n|$)',  # Numbered lists
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, notes_content, re.IGNORECASE)
            for match in matches:
                task_text = match.group(1).strip()

                # Clean up task text: remove checkboxes, bullet points, etc.
                task_text = re.sub(r'^[☐☑✓✗☒□■]\s*', '', task_text)
                task_text = re.sub(r'^[-•*]\s+', '', task_text)
                task_text = re.sub(r'^\d+\.\s+', '', task_text)
                task_text = task_text.strip()

                # Skip very short items or headers
                if len(task_text) > 10 and not task_text.endswith(':'):
                    # Extract all names mentioned
                    full_names = re.findall(r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b', task_text)
                    single_names = re.findall(r'\b(drew|art|matt|kato|paula)\b', task_text, re.IGNORECASE)
                    all_names = full_names + single_names

                    # Filter out ignored names
                    ignored_names = get_ignored_assignees()
                    non_ignored_names = [name for name in all_names if name.lower() not in ignored_names]

                    # Prioritize people in ASSIGNEE_MAP
                    assignee = None
                    if non_ignored_names:
                        for name in non_ignored_names:
                            if resolve_assignee_email(name):
                                assignee = name
                                break
                        if not assignee:
                            assignee = non_ignored_names[0]

                    # Estimate priority based on keywords
                    priority = None
                    if any(word in task_text.lower() for word in ['urgent', 'asap', 'immediately', 'critical']):
                        priority = 'urgent'
                    elif any(word in task_text.lower() for word in ['important', 'priority', 'high']):
                        priority = 'high'

                    # Find relevant context from Details section
                    context = find_relevant_context(task_text, details_section, assignee)

                    # Extract due date from task text and context (using meeting date as reference)
                    due_date_info = extract_due_date(task_text, context, meeting_date)

                    action_items.append({
                        'task': task_text,
                        'assignee': assignee,
                        'priority': priority,
                        'context': context,
                        'due_date': due_date_info
                    })

    # Remove duplicates
    seen = set()
    unique_items = []
    for item in action_items:
        if item['task'] not in seen:
            seen.add(item['task'])
            unique_items.append(item)

    print(f"Found {len(unique_items)} potential action item(s)\n")
    return unique_items


def smart_destination_detection(meeting_title):
    """
    Automatically detect the appropriate ClickUp destination based on meeting title.

    Args:
        meeting_title: Title of the meeting

    Returns:
        dict: Suggested destination with space, folder, list info
    """
    meeting_lower = meeting_title.lower()

    # Define keyword mappings to ClickUp lists
    keyword_mappings = {
        'bevmo': {
            'space_name': 'Clients',
            'folder_name': 'BevMo',
            'list_name': 'Holiday CTV 2025',
            'list_id': '901112154120'
        },
        'holiday ctv': {
            'space_name': 'Clients',
            'folder_name': 'BevMo',
            'list_name': 'Holiday CTV 2025',
            'list_id': '901112154120'
        },
        'gopuff': {
            'space_name': 'Clients',
            'folder_name': 'Gopuff',
            'list_name': 'NYE',
            'list_id': '901106184953'
        },
        'nye': {
            'space_name': 'Clients',
            'folder_name': 'Gopuff',
            'list_name': 'NYE',
            'list_id': '901106184953'
        },
        # Add more mappings as needed
    }

    # Check for keyword matches
    for keyword, destination in keyword_mappings.items():
        if keyword in meeting_lower:
            return destination

    # Default fallback - Operations list
    return {
        'space_name': 'Clients',
        'folder_name': 'Gut Feeling',
        'list_name': 'Operations',
        'list_id': '901104934665'
    }


def get_clickup_destination():
    """
    Prompt user to select or confirm the ClickUp list for task creation.

    Returns:
        dict: Contains 'space_name', 'list_name', 'list_id'
    """
    print("\n" + "=" * 60)
    print("SELECT CLICKUP DESTINATION")
    print("=" * 60)
    print("\nWhere should these tasks be created?\n")

    # Default option based on existing BevMo structure
    print("Suggested destination (based on existing BevMo tasks):")
    print("  Space: Clients")
    print("  Folder: BevMo")
    print("  List: Holiday CTV 2025")
    print("  List ID: 901112154120\n")

    response = get_user_input("Use this destination? (y/n): ", 'y').lower()

    if response == 'y':
        return {
            'space_name': 'Clients',
            'folder_name': 'BevMo',
            'list_name': 'Holiday CTV 2025',
            'list_id': '901112154120'
        }
    else:
        print("\nEnter custom destination:")
        list_id = get_user_input("List ID (or press Enter to search by name): ", '')

        if not list_id:
            list_name = get_user_input("List name to search for: ", '')
            return {
                'space_name': None,
                'folder_name': None,
                'list_name': list_name,
                'list_id': None  # Will need to look up
            }
        else:
            return {
                'space_name': None,
                'folder_name': None,
                'list_name': None,
                'list_id': list_id
            }


def preview_all_meetings_for_approval(meetings_data):
    """
    Show all meetings with their action items and destinations, let user approve/reject each.

    Args:
        meetings_data: List of dicts with meeting_title, action_items, destination

    Returns:
        list: List of approved meeting indices
    """
    print("\n" + "=" * 60)
    print("MULTIPLE MEETINGS FOUND - APPROVAL REQUIRED")
    print("=" * 60)
    print(f"\nFound {len(meetings_data)} meeting(s) to process:\n")

    # Show summary of each meeting
    for i, meeting in enumerate(meetings_data, 1):
        print(f"Meeting {i}: {meeting['meeting_title']}")
        print(f"  Action Items: {len(meeting['action_items'])}")
        print(f"  Destination: {meeting['destination']['space_name']} → {meeting['destination']['folder_name']} → {meeting['destination']['list_name']}")
        print()

    # Ask user which meetings to process
    print("=" * 60)
    response = get_user_input("\nProcess ALL meetings? (y/n/select): ", 'y').lower()

    if response == 'y':
        return list(range(len(meetings_data)))  # All meetings
    elif response == 'n':
        return []  # No meetings
    elif response == 'select':
        # Let user select specific meetings
        print("\nEnter meeting numbers to process (comma-separated, e.g., 1,3,4):")
        selection = get_user_input("Meetings to process: ", '')
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            # Validate indices
            valid_indices = [i for i in indices if 0 <= i < len(meetings_data)]
            return valid_indices
        except:
            print("Invalid selection, processing none.")
            return []
    else:
        return []


def preview_clickup_tasks(action_items, meeting_title, destination=None, claude_mode=False):
    """
    Step 4: Preview what would be created in ClickUp (without actually creating).
    In claude_mode, auto-confirms creation.

    Args:
        action_items: List of parsed action items
        meeting_title: Title of the meeting for context
        destination: Dict with space_name, list_name, list_id
        claude_mode: If True, auto-confirm without prompting

    Returns:
        bool: True if user confirms creation (or in claude_mode), False otherwise
    """
    print("\nStep 4: Preview of ClickUp Tasks to Create")
    print("=" * 60)
    print(f"Meeting: {meeting_title}")

    if destination:
        print(f"\nDestination:")
        if destination.get('space_name'):
            print(f"  Space: {destination['space_name']}")
        if destination.get('folder_name'):
            print(f"  Folder: {destination['folder_name']}")
        if destination.get('list_name'):
            print(f"  List: {destination['list_name']}")
        if destination.get('list_id'):
            print(f"  List ID: {destination['list_id']}")
    print()

    if not action_items:
        print("No action items found to create tasks from.")
        return False

    for i, item in enumerate(action_items, 1):
        print(f"Task {i}:")
        print(f"  Name: {item['task'][:80]}{'...' if len(item['task']) > 80 else ''}")
        print(f"  Action Item: {item.get('original_task', item['task'])}")

        # Build full description with context (use original_task if available)
        original_text = item.get('original_task', item['task'])
        description_parts = [f"**Action Item:** {original_text}", ""]
        if item.get('context'):
            description_parts.append("**Context from Meeting:**")
            description_parts.append(item['context'])
            description_parts.append("")
        description_parts.append(f"**Source:** {meeting_title}")

        full_description = "\n".join(description_parts)

        print(f"\n  Full Description (for ClickUp):")
        print("  " + "-" * 58)
        for line in full_description.split('\n'):
            print(f"  {line}")
        print("  " + "-" * 58)

        # Show who will actually be assigned (resolve through ASSIGNEE_MAP)
        mentioned_assignee = item.get('assignee')
        if mentioned_assignee:
            resolved_email = resolve_assignee_email(mentioned_assignee)
            if resolved_email:
                print(f"\n  Assignee: {mentioned_assignee} ({resolved_email})")
            else:
                # Not in map, will use default
                default_email = os.getenv('DEFAULT_ASSIGNEE', 'unassigned')
                print(f"\n  Assignee: {default_email} (default, {mentioned_assignee} not in team map)")
        else:
            default_email = os.getenv('DEFAULT_ASSIGNEE', 'unassigned')
            print(f"\n  Assignee: {default_email} (default)")
        print(f"  Priority: {item.get('priority', 'normal')}")

        # Show due date if found
        if item.get('due_date'):
            due_date = item['due_date']
            print(f"  Due Date: {due_date['date_string']} (timestamp: {due_date['due_date_ms']})")
        else:
            print(f"  Due Date: (none detected)")

        print(f"  Tags: ['meeting-action-item', 'bevmo']")
        print("=" * 60)

    # Ask for confirmation or auto-confirm in Claude mode
    print("\n" + "=" * 60)
    print(f"TOTAL: {len(action_items)} tasks ready to create")
    print("=" * 60)

    # Check for TASK_CONFIRMATION environment variable
    confirmation = os.environ.get('TASK_CONFIRMATION', '').strip().lower()

    if confirmation:
        # Using environment variable
        if confirmation == 'y' or confirmation == 'yes':
            print(f"\n✓ Using TASK_CONFIRMATION={confirmation} - Creating tasks")
            return True
        else:
            print(f"\n✓ Using TASK_CONFIRMATION={confirmation} - Skipping task creation")
            return False
    else:
        # Interactive mode
        response = get_user_input("\nCreate these tasks in ClickUp? (y/n): ", 'y').lower()
        return response == 'y'


def send_drew_notification(meetings_processed):
    """
    Send Drew a detailed notification by creating a summary task in ClickUp.

    Args:
        meetings_processed: List of dicts with meeting info:
            {
                'meeting_title': str,
                'tasks_created': list of dicts with 'name', 'assignee', 'priority', 'destination'
            }

    Returns:
        dict: Notification task details for Claude Code to create
    """
    print("\nPreparing notification task for Drew...")

    from datetime import datetime
    import re

    # Calculate totals
    total_meetings = len(meetings_processed)
    total_tasks = sum(len(m['tasks_created']) for m in meetings_processed)

    # Generate title
    if total_meetings == 1:
        meeting_title = meetings_processed[0]['meeting_title']
        meeting_name_match = re.search(r'"([^"]+)"', meeting_title)
        meeting_name = meeting_name_match.group(1) if meeting_name_match else meeting_title
        title = f"Meeting Processing: {meeting_name}, {total_tasks} tasks created"
    else:
        title = f"Meeting Processing: {total_meetings} meetings, {total_tasks} tasks created"

    # Build detailed description
    description_parts = [
        "Meeting Processing Summary\n",
        f"Date: {datetime.now().strftime('%B %d, %Y')}",
        f"Meetings Processed: {total_meetings}",
        f"Total Tasks Created: {total_tasks}\n"
    ]

    # Add details for each meeting
    for i, meeting in enumerate(meetings_processed, 1):
        meeting_title = meeting['meeting_title']
        meeting_name_match = re.search(r'"([^"]+)"', meeting_title)
        meeting_name = meeting_name_match.group(1) if meeting_name_match else meeting_title

        # Extract date from meeting title
        date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+,\s+\d{4}', meeting_title)
        date_str = f" ({date_match.group(0)})" if date_match else ""

        description_parts.append(f"Meeting {i}: \"{meeting_name}\"{date_str}\n")

        tasks = meeting['tasks_created']
        description_parts.append(f"Tasks Created: {len(tasks)}")

        # Group tasks by destination (project)
        tasks_by_project = {}
        for task in tasks:
            dest_key = f"{task.get('folder_name', 'Unknown')} → {task.get('list_name', 'Unknown')}"
            if dest_key not in tasks_by_project:
                tasks_by_project[dest_key] = []
            tasks_by_project[dest_key].append(task)

        if len(tasks_by_project) > 1:
            description_parts[-1] += f" (across {len(tasks_by_project)} projects)"

        description_parts.append("")

        # List tasks grouped by project
        for dest_key, dest_tasks in tasks_by_project.items():
            description_parts.append(f"{dest_key}:\n")

            for task in dest_tasks:
                task_name = task['name']
                assignee_name = task.get('assignee_name', '')
                priority = task.get('priority', '')

                # Build task line
                task_line = f"- {task_name}"
                if assignee_name:
                    task_line += f" ({assignee_name})"
                if priority and priority != 'None':
                    priority_map = {'1': 'URGENT', '2': 'HIGH', '3': 'NORMAL', '4': 'LOW'}
                    priority_text = priority_map.get(str(priority), str(priority).upper())
                    task_line += f" - {priority_text} priority"

                description_parts.append(task_line)

            description_parts.append("")

    # Add footer
    description_parts.append("🤖 Automated by Claude Code meeting processor")

    # Create notification task
    notification_task = {
        'name': title,
        'markdown_description': '\n'.join(description_parts),
        'assignees': ['drew@gutfeeling.agency'],
        'tags': ['automation-summary', 'meeting-processed'],
        'priority': 'normal',
        'list_id': '901112235176'  # Automation Summaries list
    }

    print(f"✓ Notification task prepared for Drew")
    return notification_task


def get_clickup_api_token():
    """
    Get ClickUp API token from environment variable or prompt user.

    Returns:
        str: ClickUp API token
    """
    # Try to get from environment first
    token = os.environ.get('CLICKUP_API_TOKEN')

    if not token:
        # Try to read from .env file
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('CLICKUP_API_TOKEN='):
                        token = line.strip().split('=', 1)[1].strip('"\'')
                        break

    if not token:
        print("\n⚠️  ClickUp API token not found")
        print("\nTo create tasks, you need a ClickUp API token.")
        print("Get one from: https://app.clickup.com/settings/apps")
        print("\nYou can either:")
        print("  1. Set environment variable: export CLICKUP_API_TOKEN='your_token'")
        print("  2. Create .env file with: CLICKUP_API_TOKEN=your_token")
        print("  3. Enter it now (will be used for this session only)")
        print()
        token = get_user_input("Enter ClickUp API token (or press Enter to skip): ", '')

    return token if token else None


# Cache for email to user ID mapping (to avoid repeated API calls)
_email_to_id_cache = {}

def resolve_email_to_clickup_id(email, api_token, workspace_id='2538614'):
    """
    Convert email address to ClickUp user ID by looking up workspace members.
    Caches results to avoid repeated API calls.

    Args:
        email: Email address to resolve
        api_token: ClickUp API token
        workspace_id: ClickUp workspace/team ID

    Returns:
        int: ClickUp user ID or None if not found
    """
    # Check cache first
    if email in _email_to_id_cache:
        return _email_to_id_cache[email]

    # Fetch workspace members if not cached
    if not _email_to_id_cache:
        try:
            url = f"https://api.clickup.com/api/v2/team/{workspace_id}/user"
            headers = {'Authorization': api_token}
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            members = response.json().get('members', [])
            for member in members:
                user = member.get('user', {})
                user_email = user.get('email', '')
                user_id = user.get('id')
                if user_email and user_id:
                    _email_to_id_cache[user_email.lower()] = user_id

        except Exception as e:
            print(f"Warning: Could not fetch workspace members: {e}")
            return None

    # Look up in cache
    return _email_to_id_cache.get(email.lower())


def get_tasks_from_list(list_id, api_token):
    """
    Fetch all existing tasks from a ClickUp list.

    Args:
        list_id: ClickUp list ID
        api_token: ClickUp API token

    Returns:
        List of task dictionaries or empty list if failed
    """
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"

    headers = {
        'Authorization': api_token,
        'Content-Type': 'application/json'
    }

    params = {
        'include_closed': False,  # Don't include closed tasks
        'subtasks': False  # Don't include subtasks
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('tasks', [])
        else:
            print(f"⚠️  Failed to fetch tasks from list: {response.status_code}")
            return []
    except Exception as e:
        print(f"⚠️  Error fetching tasks: {e}")
        return []


def update_clickup_task(task_id, updates, api_token):
    """
    Update an existing ClickUp task.

    Args:
        task_id: ClickUp task ID
        updates: Dict with fields to update (name, description, due_date, assignees, etc.)
        api_token: ClickUp API token

    Returns:
        dict: API response or None if failed
    """
    url = f"https://api.clickup.com/api/v2/task/{task_id}"

    headers = {
        'Authorization': api_token,
        'Content-Type': 'application/json'
    }

    payload = {}

    # Add fields to update
    if 'name' in updates:
        payload['name'] = updates['name']

    if 'markdown_description' in updates:
        payload['markdown_description'] = updates['markdown_description']

    if 'due_date' in updates:
        payload['due_date'] = updates['due_date']

    if 'assignees' in updates:
        # Handle assignees
        assignee_ids = []
        for assignee in updates['assignees']:
            if isinstance(assignee, dict):
                assignee_ids.append(assignee.get('id'))
            else:
                # It's an email, resolve it
                user_id = resolve_email_to_clickup_id(assignee, api_token)
                if user_id:
                    assignee_ids.append(user_id)

        if assignee_ids:
            payload['assignees'] = {'add': assignee_ids}

    try:
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️  Failed to update task: {response.status_code}")
            print(f"    Response: {response.text}")
            return None
    except Exception as e:
        print(f"⚠️  Error updating task: {e}")
        return None


def add_task_comment(task_id, comment_text, api_token):
    """
    Add a comment to a ClickUp task.

    Args:
        task_id: ClickUp task ID
        comment_text: Comment text (supports markdown)
        api_token: ClickUp API token

    Returns:
        dict: API response or None if failed
    """
    url = f"https://api.clickup.com/api/v2/task/{task_id}/comment"

    headers = {
        'Authorization': api_token,
        'Content-Type': 'application/json'
    }

    payload = {
        'comment_text': comment_text
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️  Failed to add comment: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️  Error adding comment: {e}")
        return None


def create_clickup_task_via_api(task_data, api_token):
    """
    Create a single task in ClickUp using the REST API.

    Args:
        task_data: Dict with task details
        api_token: ClickUp API token

    Returns:
        dict: API response or None if failed
    """
    list_id = task_data.get('list_id')
    if not list_id:
        return None

    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"

    headers = {
        'Authorization': api_token,
        'Content-Type': 'application/json'
    }

    payload = {
        'name': task_data['name'],
        'markdown_description': task_data.get('markdown_description', ''),
        'tags': task_data.get('tags', []),
    }

    # Add optional fields
    if task_data.get('assignees'):
        # Convert email addresses to ClickUp user IDs for REST API
        assignee_ids = []
        for email in task_data['assignees']:
            user_id = resolve_email_to_clickup_id(email, api_token)
            if user_id:
                assignee_ids.append(user_id)

        if assignee_ids:
            payload['assignees'] = assignee_ids
    if task_data.get('priority'):
        # Convert priority names to ClickUp values
        priority_map = {'urgent': 1, 'high': 2, 'normal': 3, 'low': 4}
        payload['priority'] = priority_map.get(task_data['priority'], 3)
    if task_data.get('due_date'):
        payload['due_date'] = int(task_data['due_date'])

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating task: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None


def create_clickup_tasks_via_mcp(action_items, destination, meeting_title, claude_mode=False):
    """
    Step 5: Create tasks in ClickUp using MCP tools.

    Args:
        action_items: List of parsed action items with context and due dates
        destination: Dict with list_id and other destination info
        meeting_title: Title of the meeting for context
        claude_mode: If True, will call MCP tools via subprocess

    Returns:
        dict: Results with 'created', 'failed', 'task_urls', and 'prepared_tasks'
    """
    print("\n" + "=" * 60)
    print("CREATING TASKS IN CLICKUP")
    print("=" * 60)

    if not destination.get('list_id'):
        print("Error: No list_id specified in destination")
        return {'created': 0, 'failed': len(action_items), 'task_urls': [], 'ready': False}

    # Prepare tasks for bulk creation
    tasks_to_create = []

    # Auto-detect meeting tags from title
    meeting_tags = []
    meeting_lower = meeting_title.lower()
    if 'bevmo' in meeting_lower:
        meeting_tags.append('bevmo')
    elif 'total wine' in meeting_lower:
        meeting_tags.append('total-wine')
    elif 'vfx' in meeting_lower or 'visual effects' in meeting_lower:
        meeting_tags.append('vfx')
    # Add default tag
    meeting_tags.append('meeting-action-item')

    for i, item in enumerate(action_items, 1):
        print(f"\nPreparing Task {i}/{len(action_items)}: {item['task'][:50]}...")

        # Check if assignee is in our map
        mentioned_assignee = item.get('assignee')
        resolved_email = None
        if mentioned_assignee:
            resolved_email = resolve_assignee_email(mentioned_assignee)

        # Build the task description with markdown formatting (use original_task in description)
        original_text = item.get('original_task', item['task'])
        description_parts = [
            f"**Action Item:** {original_text}",
            ""
        ]

        # If assignee mentioned but not in map, add them to description
        if mentioned_assignee and not resolved_email:
            # Person not in assignee map, mention them in description
            description_parts.append(f"**Mentioned Assignee:** {mentioned_assignee}")
            description_parts.append("")

        description_parts.extend([
            "**Context from Meeting:**",
            item.get('context', 'No additional context available'),
            "",
            f"**Source:** {meeting_title}"
        ])

        full_description = "\n".join(description_parts)

        # Condense task name: remove assignee name and extra words
        condensed_name = item['task']

        # Remove assignee name from beginning (e.g., "Matt Rose will" -> "will")
        if item.get('assignee'):
            assignee_pattern = rf"^{re.escape(item['assignee'])}\s+(will|should|needs to|to|must|can)\s+"
            condensed_name = re.sub(assignee_pattern, '', condensed_name, flags=re.IGNORECASE)

        # Remove common prefixes
        condensed_name = re.sub(r'^(will|should|needs to|need to|must|can)\s+', '', condensed_name, flags=re.IGNORECASE)

        # Capitalize first letter
        if condensed_name:
            condensed_name = condensed_name[0].upper() + condensed_name[1:]

        # Intelligently truncate if too long (at word/phrase boundaries)
        if len(condensed_name) > 80:
            # Try to break at natural boundaries (by/after/for/with/at/before)
            truncate_at = 80
            boundaries = [' by ', ' after ', ' for ', ' with ', ' at ', ' before ', ' and ', ' to ']

            # Find the last boundary before position 80
            best_pos = -1
            for boundary in boundaries:
                pos = condensed_name[:80].rfind(boundary)
                if pos > best_pos and pos > 40:  # Don't truncate too early
                    best_pos = pos

            if best_pos > 40:
                condensed_name = condensed_name[:best_pos]
            else:
                # No good boundary found, just truncate at last space before 80
                last_space = condensed_name[:80].rfind(' ')
                if last_space > 40:
                    condensed_name = condensed_name[:last_space]
                else:
                    condensed_name = condensed_name[:80]

        # Detect per-task destination (overrides meeting-level destination)
        from gut_automate.task_learning import detect_task_destination
        task_destination_result = detect_task_destination(
            task_text=item['task'],
            task_context=item.get('context', ''),
            meeting_context=meeting_title
        )

        # Use detected destination if confidence is high enough
        task_list_id = destination['list_id']  # Default to meeting destination
        if task_destination_result:
            task_dest, confidence, source = task_destination_result
            if confidence >= 0.7:  # Only override if confident
                task_list_id = task_dest.get('list_id', destination['list_id'])
                print(f"    → Detected specific destination: {task_dest.get('list_name', 'unknown')} (confidence: {confidence:.0%}, source: {source})")

        # Build task object for ClickUp MCP
        task_obj = {
            'name': condensed_name,
            'markdown_description': full_description,
            'tags': meeting_tags,
            'list_id': task_list_id  # Store per-task list_id
        }

        # Use resolved email from earlier, or fall back to default
        # (resolved_email was set when building description)
        assignee_email = resolved_email if resolved_email else os.getenv('DEFAULT_ASSIGNEE')

        if assignee_email:
            task_obj['assignees'] = [assignee_email]

        # Add priority if available
        if item.get('priority'):
            task_obj['priority'] = item['priority']

        # Add due date if available
        if item.get('due_date') and item['due_date'].get('due_date_ms'):
            # Store due_date based on mode:
            # - MCP tools expect STRING
            # - REST API expects INTEGER
            try:
                if claude_mode:
                    # MCP tools need due_date as string
                    task_obj['due_date'] = str(int(item['due_date']['due_date_ms']))
                else:
                    # REST API needs due_date as integer
                    task_obj['due_date'] = int(item['due_date']['due_date_ms'])
            except (ValueError, TypeError):
                # If conversion fails, skip the due date
                pass

        tasks_to_create.append(task_obj)

    print(f"\n✓ Prepared {len(tasks_to_create)} tasks for ClickUp creation")
    print(f"  List ID: {destination['list_id']}")
    print(f"  Tags: {', '.join(meeting_tags)}")

    # If in claude mode, actually create the tasks via MCP
    if claude_mode:
        print(f"\n🤖 CLAUDE MODE: Creating tasks via MCP...")

        # Write tasks to a temp JSON file for MCP to read
        import json
        import tempfile

        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        mcp_payload = {
            'list_id': destination['list_id'],
            'tasks': tasks_to_create
        }
        json.dump(mcp_payload, temp_file)
        temp_file.close()

        print(f"  Task data written to: {temp_file.name}")
        print(f"  Run this command via Claude Code:")
        print(f"    mcp__clickup__clickup_create_bulk_tasks with list_id={destination['list_id']}")

        return {
            'prepared_tasks': tasks_to_create,
            'temp_file': temp_file.name,
            'destination': destination,
            'ready': True,
            'count': len(tasks_to_create),
            'meeting_title': meeting_title,
            'claude_mode': True
        }
    else:
        # Standalone mode - just return the prepared tasks
        return {
            'prepared_tasks': tasks_to_create,
            'destination': destination,
            'ready': True,
            'count': len(tasks_to_create),
            'meeting_title': meeting_title,
            'claude_mode': False
        }


def create_clickup_tasks(action_items, destination, meeting_title):
    """
    Legacy wrapper for create_clickup_tasks_via_mcp.
    Kept for backwards compatibility.
    """
    return create_clickup_tasks_via_mcp(action_items, destination, meeting_title, claude_mode=False)


def prompt_for_meeting_approval(emails, claude_mode=False):
    """
    Show list of meetings and prompt user to select which ones to process.
    In claude_mode, auto-approves all meetings.

    Args:
        emails: List of email dicts with meeting info
        claude_mode: If True, auto-approve all meetings without prompting

    Returns:
        list: Indices of emails approved for processing
    """
    print(f"\n{'='*60}")
    print(f"FOUND {len(emails)} UNREAD MEETING NOTE(S)")
    print(f"{'='*60}\n")

    # Show each meeting
    for i, email in enumerate(emails, 1):
        meeting_title = email['subject'].replace('Notes: ', '').strip('"')
        print(f"Meeting {i}: {meeting_title}")
        print(f"  Date: {email['date']}")
        print(f"  Email ID: {email['email_id']}")
        print()

    print(f"{'='*60}")

    # Interactive mode - prompt user
    print("\nWhich meetings would you like to process?")
    print("  • Enter 'all' to process all meetings")
    print("  • Enter 'none' or 'skip' to skip all")
    print("  • Enter numbers (comma-separated, e.g., '1,2' or '2')")

    # Check for MEETING_SELECTION environment variable (works in both modes)
    selection = os.environ.get('MEETING_SELECTION', '')

    if selection:
        # Using environment variable
        print(f"\n✓ Using MEETING_SELECTION={selection}")
        response = selection.strip().lower()
    else:
        # Interactive mode
        response = get_user_input("\nYour choice: ", 'all').lower()

    # Handle 'all' or 'y'
    if response in ['all', 'y', 'yes']:
        return list(range(len(emails)))  # All meetings

    # Handle 'none', 'skip', or 'n'
    elif response in ['none', 'skip', 'n', 'no', '']:
        return []  # No meetings

    # Handle direct number entry (e.g., '2' or '1,3')
    else:
        try:
            # Parse comma-separated numbers
            indices = [int(x.strip()) - 1 for x in response.split(',')]
            # Validate indices
            valid_indices = [i for i in indices if 0 <= i < len(emails)]

            if valid_indices:
                # Show confirmation of selected meetings
                print(f"\n✓ Selected {len(valid_indices)} meeting(s):")
                for i in valid_indices:
                    meeting_title = emails[i]['subject'].replace('Notes: ', '').strip('"')
                    print(f"  - Meeting {i+1}: {meeting_title}")
                return valid_indices
            else:
                print(f"⚠️  Invalid selection. No valid meeting numbers found.")
                return []
        except ValueError:
            print(f"⚠️  Invalid input '{response}'. Please enter numbers, 'all', or 'none'.")
            return []


def main(mode='auto'):
    """
    Main entry point for gutAutomate.

    Always runs in automatic mode using REST API.
    Claude consultation available for low-confidence decisions.

    Args:
        mode: Deprecated parameter (kept for backward compatibility)
    """
    print("🚀 gutAutomate - Intelligent Meeting Note Processing")
    print("   Using: REST API (direct) + Optional Claude consultation")
    print()

    # Complete workflow: Find meeting notes, fetch content, parse action items, preview tasks
    emails = find_gemini_meeting_notes()

    if not emails:
        print("\nNo meeting notes emails found to process.")
    else:
        # Step 1: Show all meetings and get approval BEFORE fetching content
        approved_indices = prompt_for_meeting_approval(emails)

        if not approved_indices:
            print("\n✗ No meetings approved for processing.")
        else:
            print(f"\n✓ {len(approved_indices)} meeting(s) approved")

            print(f"\n{'='*60}")
            print(f"Fetching content for approved meetings...")
            print(f"{'='*60}\n")

            # Step 2: Process only approved meetings
            meetings_data = []

            for idx in approved_indices:
                email = emails[idx]
                if email['meeting_notes_link']:
                    # Extract meeting title from subject
                    meeting_title = email['subject'].replace('Notes: ', '').strip('"')

                    print(f"Processing: {meeting_title}")

                    # Extract document ID for copying
                    doc_id = extract_document_id(email['meeting_notes_link'])

                    # Check if this meeting has already been processed
                    from gut_automate.duplicate_detection import check_meeting_processed
                    already_processed = check_meeting_processed(
                        doc_id=doc_id,
                        email_id=email['email_id']
                    )

                    if already_processed:
                        print(f"⏭️  SKIPPED: This meeting was already processed on {already_processed.get('processed_date')}")
                        print(f"   {len(already_processed.get('tasks_created', []))} tasks were created")
                        print(f"   To re-process, delete this meeting from data/processed_meetings.json\n")
                        continue

                    # Copy document to shared drive
                    if doc_id:
                        copy_result = copy_doc_to_shared_drive(doc_id, meeting_title)
                        if not copy_result['success']:
                            print(f"⚠️  Failed to copy document, continuing anyway...")

                    # Get document content
                    content = get_meeting_notes_content(email['meeting_notes_link'])

                    if content:
                        # Parse action items (pass meeting_title for date extraction)
                        action_items = parse_action_items(content, meeting_title, debug=False)

                        # Smart destination detection
                        destination = smart_destination_detection(meeting_title)

                        # Store meeting data
                        meetings_data.append({
                            'email_id': email['email_id'],
                            'doc_id': doc_id,
                            'meeting_title': meeting_title,
                            'action_items': action_items,
                            'destination': destination
                        })

            if not meetings_data:
                print("\n✗ No meetings with valid content found.")
            else:
                # Step 3: Show detailed summary (they already approved at high level)
                print(f"\n{'='*60}")
                print(f"SUMMARY OF APPROVED MEETINGS")
                print(f"{'='*60}\n")

                for i, meeting in enumerate(meetings_data, 1):
                    print(f"Meeting {i}: {meeting['meeting_title']}")
                    print(f"  Action Items: {len(meeting['action_items'])}")
                    print(f"  Destination: {meeting['destination']['space_name']} → {meeting['destination']['folder_name']} → {meeting['destination']['list_name']}")
                    print()

                # Track all meetings processed for summary notification
                meetings_for_notification = []

                # Step 4: Process each approved meeting
                for idx, meeting in enumerate(meetings_data):
                    print(f"\n{'='*60}")
                    print(f"Processing Meeting {idx + 1}: {meeting['meeting_title']}")
                    print(f"{'='*60}")

                    # Preview detailed tasks for this meeting
                    should_create = preview_clickup_tasks(
                        meeting['action_items'],
                        meeting['meeting_title'],
                        meeting['destination']
                    )

                    if should_create:
                        print("\n✓ User confirmed - Creating tasks via ClickUp REST API...")

                        # Prepare tasks for ClickUp
                        result = create_clickup_tasks_via_mcp(
                            meeting['action_items'],
                            meeting['destination'],
                            meeting['meeting_title'],
                            claude_mode=False  # Always use REST API format
                        )

                        if result.get('ready'):
                            print(f"\n✓ Tasks prepared successfully!")
                            print(f"  {result['count']} tasks ready to be created in ClickUp")

                            # Get API token
                            api_token = get_clickup_api_token()

                            if not api_token:
                                print(f"\n⚠️  Skipping task creation (no API token)")
                                print(f"\nTo create these tasks later:")
                                print(f"  1. Get API token from https://app.clickup.com/settings/apps")
                                print(f"  2. Run: export CLICKUP_API_TOKEN='your_token'")
                                print(f"  3. Re-run this script")
                            else:
                                # Import duplicate detection functions
                                from gut_automate.duplicate_detection import (
                                    find_similar_tasks, compare_tasks,
                                    merge_descriptions, create_update_comment
                                )

                                # Fetch existing tasks from destination list for duplicate detection
                                print(f"\n🔍 Checking for duplicate tasks in destination list...")
                                existing_tasks = get_tasks_from_list(meeting['destination']['list_id'], api_token)
                                print(f"   Found {len(existing_tasks)} existing tasks")

                                # Create tasks via API with duplicate detection
                                created_count = 0
                                updated_count = 0
                                skipped_count = 0
                                failed_count = 0
                                task_urls = []
                                tasks_for_notification = []  # Track task details for notification

                                for task_data in result['prepared_tasks']:
                                    # Use per-task list_id if available, otherwise use meeting destination
                                    if 'list_id' not in task_data:
                                        task_data['list_id'] = destination['list_id']

                                    print(f"\n📝 Processing: {task_data['name'][:60]}...")

                                    # Check for duplicates
                                    matches = find_similar_tasks(task_data, existing_tasks, threshold=0.85)

                                    if matches:
                                        # Found potential duplicate
                                        existing_task, similarity = matches[0]

                                        # Compare to see what changed
                                        changes = compare_tasks(task_data, existing_task)

                                        # Prompt user for action
                                        action = prompt_duplicate_action(
                                            task_data, existing_task, similarity, changes
                                        )

                                        if action == 'skip':
                                            print("   ⏭️  Skipped (duplicate)")
                                            skipped_count += 1
                                            continue

                                        elif action == 'update':
                                            print("   🔄 Updating existing task...", end=" ")

                                            # Prepare updates
                                            updates = {}

                                            # Update due date if changed
                                            if changes.get('due_date_changed'):
                                                updates['due_date'] = changes['new_due_date']

                                            # Update assignees if changed
                                            if changes.get('assignee_changed'):
                                                updates['assignees'] = task_data.get('assignees', [])

                                            # Merge descriptions if different
                                            if changes.get('description_different'):
                                                merged_desc = merge_descriptions(
                                                    changes['old_description'],
                                                    changes['new_description']
                                                )
                                                updates['markdown_description'] = merged_desc

                                            # Update the task
                                            if updates:
                                                update_response = update_clickup_task(
                                                    existing_task['id'], updates, api_token
                                                )

                                                if update_response:
                                                    # Add comment explaining the update
                                                    comment_text = create_update_comment(meeting_title, changes)
                                                    add_task_comment(existing_task['id'], comment_text, api_token)

                                                    updated_count += 1
                                                    task_url = existing_task.get('url', '')
                                                    task_urls.append(task_url)
                                                    print("✓")
                                                else:
                                                    failed_count += 1
                                                    print("✗")
                                            else:
                                                print("(no changes needed)")
                                                skipped_count += 1

                                            continue

                                    # No duplicate or user chose to create anyway
                                    print("   ➕ Creating new task...", end=" ")
                                    response = create_clickup_task_via_api(task_data, api_token)

                                    if response:
                                        created_count += 1
                                        task_urls.append(response.get('url'))

                                        # Collect task info for notification
                                        # Extract assignee name from email
                                        assignee_name = ''
                                        assignees = task_data.get('assignees', [])
                                        if assignees:
                                            first_assignee = assignees[0]
                                            if isinstance(first_assignee, str) and '@' in first_assignee:
                                                # Extract name from email (e.g., drew@gutfeeling.agency -> Drew)
                                                assignee_name = first_assignee.split('@')[0].title()

                                        task_info = {
                                            'name': task_data.get('name', ''),
                                            'assignee_name': assignee_name,
                                            'priority': task_data.get('priority'),
                                            'folder_name': meeting['destination'].get('folder_name', 'Unknown'),
                                            'list_name': meeting['destination'].get('list_name', 'Unknown')
                                        }
                                        tasks_for_notification.append(task_info)
                                        print("✓")
                                    else:
                                        failed_count += 1
                                        print("✗")

                                # Summary
                                print(f"\n{'='*60}")
                                print(f"TASK PROCESSING COMPLETE")
                                print(f"{'='*60}")
                                print(f"➕ Created: {created_count}")
                                if updated_count > 0:
                                    print(f"🔄 Updated: {updated_count}")
                                if skipped_count > 0:
                                    print(f"⏭️  Skipped: {skipped_count}")
                                if failed_count > 0:
                                    print(f"✗ Failed: {failed_count}")

                                if task_urls:
                                    print(f"\nProcessed tasks:")
                                    for url in task_urls[:5]:  # Show first 5
                                        if url:
                                            print(f"  {url}")
                                    if len(task_urls) > 5:
                                        print(f"  ... and {len(task_urls) - 5} more")

                                # Record this meeting as processed (processing history is source of truth)
                                if created_count > 0 or updated_count > 0:
                                    from gut_automate.duplicate_detection import record_processed_meeting
                                    tasks_created_records = [
                                        {
                                            'task_id': url.split('/')[-1] if url else None,
                                            'task_name': task_data.get('name', ''),
                                            'list_id': meeting['destination']['list_id']
                                        }
                                        for task_data, url in zip(result['prepared_tasks'], task_urls)
                                        if url
                                    ]
                                    record_processed_meeting(
                                        doc_id=meeting.get('doc_id', ''),
                                        meeting_title=meeting['meeting_title'],
                                        email_id=meeting['email_id'],
                                        tasks_created=tasks_created_records
                                    )
                                    print(f"\n✓ Recorded meeting as processed in history database")
                                    print(f"   (Email left unread - you can mark it read when you're done with it)")

                                    # Add this meeting to notification list
                                    if tasks_for_notification:
                                        meetings_for_notification.append({
                                            'meeting_title': meeting['meeting_title'],
                                            'tasks_created': tasks_for_notification
                                        })
                                else:
                                    print(f"\n⚠️  No tasks created/updated - meeting NOT recorded as processed")
                        else:
                            print("\n✗ Failed to prepare tasks")
                    else:
                        print("\n✗ Task creation cancelled by user.")

                # Create summary notification after all meetings processed
                if meetings_for_notification:
                    print(f"\n{'='*60}")
                    print(f"Creating summary notification...")
                    print(f"{'='*60}")

                    notification = send_drew_notification(meetings_for_notification)
                    notif_response = create_clickup_task_via_api(notification, api_token)

                    if notif_response:
                        print(f"✓ Summary notification created")
                        print(f"  {notif_response.get('url', '')}")
                    else:
                        print(f"✗ Failed to create summary notification")


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='gutAutomate - Automate ClickUp task creation from Gemini meeting notes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 -m gut_automate.core               # Auto mode (REST API)
  MEETING_SELECTION="all" python3 -m ...     # Skip meeting selection
  TASK_CONFIRMATION="y" python3 -m ...       # Skip task confirmation
        """
    )
    # Keep mode argument for backward compatibility but ignore it
    parser.add_argument(
        'mode',
        nargs='?',
        default='auto',
        help='Deprecated - kept for backward compatibility only'
    )
    args = parser.parse_args()

    main()
