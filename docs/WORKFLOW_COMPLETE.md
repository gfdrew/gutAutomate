# Complete Workflow Documentation

## How It Works Now

When you say **"process my meeting notes"**, here's what happens:

### Step 1: Find Meetings
I run Python code to find unread Gemini meeting notes:
```python
from gutAutomate import find_gemini_meeting_notes
emails = find_gemini_meeting_notes()
```

### Step 2: Ask for Your Approval
I use `AskUserQuestion` to show you the meetings and ask which to process.

### Step 3: Run gutAutomate.py in Claude Mode
I execute:
```bash
python3 process_with_mcp.py "<your_selection>" "y"
```

This wrapper:
1. Runs gutAutomate.py with your selection
2. Marks emails as read
3. Copies docs to shared drive
4. Parses action items with full context
5. Outputs JSON with prepared tasks

### Step 4: Parse JSON Output
I extract the JSON containing:
- All prepared tasks (with full context)
- Notification task details
- List ID and destination info

### Step 5: Ask for Final Confirmation
I show you a preview of the tasks and ask:
"Create these X tasks in ClickUp?"

### Step 6: Create Tasks via MCP
I call:
```
mcp__clickup__clickup_create_bulk_tasks(
  list_id=...,
  tasks=[...prepared tasks with full context...]
)
```

### Step 7: Create Notification
I call:
```
mcp__clickup__clickup_create_task(
  list_id="901112235176",  # Automation Summaries
  name="🤖 gutAutomate processed meeting...",
  assignees=["drew@gutfeeling.agency"],
  ...
)
```

## Benefits

✅ **You control approval** - Asked at every step via AskUserQuestion
✅ **All context preserved** - Details section included in task descriptions
✅ **MCP tools used** - Direct ClickUp integration
✅ **Fully automated** - No manual copy/paste needed
✅ **Reliable** - Script handles all the parsing and preparation

## Usage

Just tell me: **"Process my meeting notes"**

That's it! I'll handle the rest and ask for your approval at each step.

## Technical Flow

```
You: "Process my meeting notes"
  ↓
Claude Code: find_gemini_meeting_notes()
  ↓
Claude Code: AskUserQuestion (which meetings?)
  ↓
You: Select meetings
  ↓
Claude Code: python3 process_with_mcp.py "2" "y"
  ↓
gutAutomate.py:
  - Mark as read
  - Copy to drive
  - Parse actions
  - Extract context
  - Output JSON
  ↓
Claude Code: Parse JSON
  ↓
Claude Code: AskUserQuestion (create tasks?)
  ↓
You: Confirm
  ↓
Claude Code: mcp__clickup__clickup_create_bulk_tasks()
  ↓
Claude Code: mcp__clickup__clickup_create_task() [notification]
  ↓
Done! ✅
```

## Files

- **gutAutomate.py** - Main script with all parsing logic
- **process_with_mcp.py** - Wrapper that runs gutAutomate and outputs JSON
- **This file** - Complete workflow documentation

## Example

```
You: "Process my meeting notes"

Me: I found 2 unread meetings:
    1. Gopuff NYE Team Sync
    2. BevMo Recurring StandUp
    Which would you like to process?

You: [Select "BevMo Recurring StandUp"]

Me: Processing BevMo meeting...
    Found 5 action items:
    1. Provide realistic budget for shoot (Matt Rose)
    2. Confirm graphic outro card details (Matt Rose)
    3. Confirm discussion points and send invite (Matt Rose)
    4. Include Total Wine references (Art Okoro)
    5. Go over shot list tonight (Art Okoro) [URGENT]

    Create these 5 tasks?

You: [Confirm]

Me: ✅ Created 5 tasks in Holiday CTV 2025
    ✅ Created notification in Automation Summaries
    All tasks have full context from meeting notes!
```
