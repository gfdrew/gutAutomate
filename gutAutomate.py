#!/usr/bin/env python3
"""
gutAutomate - Google Drive and Gmail Automation
"""

import os.path
import re
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/gmail.modify'  # Read and modify Gmail
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


if __name__ == '__main__':
    # Test Step 1: Find Gemini meeting notes
    find_gemini_meeting_notes()
