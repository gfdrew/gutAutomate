#!/usr/bin/env python3
"""Mark specific emails as unread"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from core.py
from gut_automate.core import get_gmail_service

# The 6 original email IDs
email_ids = [
    '199f3483e3423ae8',  # "Stand Up" Oct 17, 2025
    '199f2c2fdc75307e',  # "Chad : Drew : Rose 15 min stand up" Oct 17, 2025
    '199ee598584e0141',  # "aidanwilde / dgenz.world / Gut Feeling" Oct 16, 2025
    '199ee3263f241206',  # "Project Management Meeting" Oct 16, 2025
    '199ea0081196c33f',  # "Work Session: Shotlist for Gopuff" Oct 15, 2025
    '199e4047bca588e0',  # "Project Management Meeting" Oct 14, 2025
]

# Get Gmail service
service = get_gmail_service()

print(f"Marking {len(email_ids)} emails as unread...")
success_count = 0

for email_id in email_ids:
    try:
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'addLabelIds': ['UNREAD']}
        ).execute()
        print(f"✓ Marked {email_id} as unread")
        success_count += 1
    except Exception as e:
        print(f"✗ Error marking {email_id}: {e}")

print(f"\n✓ Successfully marked {success_count}/{len(email_ids)} emails as unread")
