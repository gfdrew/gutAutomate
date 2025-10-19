# Claude Mode Usage Guide

## Overview

When you want to use gutAutomate with Claude Code AND still have approval control, you have two options:

### Option 1: Let Claude Code Handle the Workflow (Recommended)

Simply tell Claude Code: **"Process my meeting notes"**

Claude Code will:
1. Import Python functions from gutAutomate.py
2. Find unread meeting notes
3. Show you the list and ask which ones to process (using AskUserQuestion)
4. Fetch content and parse action items
5. Show you a preview of tasks with full context
6. Ask for your confirmation (using AskUserQuestion)
7. Create tasks directly via MCP tools (with all context preserved)
8. Send you a notification

**Benefits:**
- ✅ You control approval at every step
- ✅ All context preserved in tasks
- ✅ Uses MCP tools directly
- ✅ No blocking input() prompts

### Option 2: Run gutAutomate.py Manually (Interactive)

```bash
python3 gutAutomate.py
```

This runs in standalone mode:
- Prompts you for meeting selection via terminal
- Shows preview with full context
- Creates tasks via REST API (requires CLICKUP_API_TOKEN)

## How Option 1 Works

When you say "process my meeting notes", Claude Code will execute this workflow:

```python
# 1. Find emails
from gutAutomate import find_gemini_meeting_notes
emails = find_gemini_meeting_notes()

# 2. Ask you which meetings to process
# (Claude Code uses AskUserQuestion tool)

# 3. Process approved meetings
from gutAutomate import (
    get_meeting_notes_content,
    parse_action_items,
    smart_destination_detection,
    mark_emails_as_read,
    copy_doc_to_shared_drive,
    extract_document_id
)

for email in approved_emails:
    content = get_meeting_notes_content(email['meeting_notes_link'])
    action_items = parse_action_items(content, meeting_title)
    destination = smart_destination_detection(meeting_title)
    # ... etc

# 4. Ask you to confirm tasks
# (Claude Code uses AskUserQuestion tool)

# 5. Create tasks via MCP
from mcp__clickup__clickup_create_bulk_tasks
# ... creates tasks with full context
```

## Example Conversation

**You:** "Process my meeting notes"

**Claude Code:**
- Finds 2 unread meeting notes
- Shows you: "VFX Production Approach" and "BevMo Recurring StandUp"
- Asks: "Which meetings would you like to process?"

**You:** Select meetings via UI

**Claude Code:**
- Fetches content from Google Docs
- Parses action items with context
- Shows preview: "Found 5 tasks from BevMo meeting..."
- Shows full context for each task
- Asks: "Create these tasks?"

**You:** Confirm via UI

**Claude Code:**
- Creates all 5 tasks via MCP with full context
- All assignees, tags, priorities preserved
- Sends notification

## Key Differences

### gutAutomate.py claude (Old Approach)
```bash
python3 gutAutomate.py claude
```
❌ Auto-approves everything (you asked to change this)
❌ Can't use AskUserQuestion (it's a Python script)

### Claude Code Direct (New Approach)
**You:** "Process my meeting notes"

✅ You approve each step
✅ Claude Code uses AskUserQuestion tool
✅ All context preserved
✅ MCP tools used directly

## What Changed

We updated gutAutomate.py so:
- Functions can be imported and called individually
- `create_clickup_tasks_via_mcp()` builds rich task descriptions
- Context extraction works standalone
- Claude Code can orchestrate the workflow

## When to Use Each

| Scenario | Use This |
|----------|----------|
| Want approval control + MCP | Tell Claude Code: "Process my meeting notes" |
| Want fully automated | Use taskUpSolo.py |
| Want REST API (no Claude Code) | Use gutAutomate.py (no arguments) |
| Testing/debugging | Use claude_automate.py wrapper |

## Summary

**Old Way (What you didn't like):**
```bash
python3 gutAutomate.py claude  # Auto-approves everything
```

**New Way (What you want):**
```
[Tell Claude Code directly]
"Process my meeting notes"  # You approve each step
```

This way:
- ✅ You control approval
- ✅ All context preserved
- ✅ MCP tools used
- ✅ No input() blocking

Just talk to Claude Code naturally and it will handle the workflow with your approval at each step!
