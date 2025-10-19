#!/usr/bin/env python3
import os
print(f"MEETING_SELECTION = '{os.environ.get('MEETING_SELECTION', 'NOT SET')}'")
print(f"TASK_CONFIRMATION = '{os.environ.get('TASK_CONFIRMATION', 'NOT SET')}'")
