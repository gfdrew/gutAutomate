# Duplicate Detection & Update System

## Overview

The duplicate detection system prevents creating duplicate tasks in ClickUp and allows you to update existing tasks when new information is found in subsequent meetings.

## Key Features

1. **Fuzzy Matching** - Detects similar tasks even with minor wording differences (85% similarity threshold)
2. **Smart Comparison** - Identifies what changed (due date, assignee, description)
3. **Interactive Prompts** - Choose to skip, update, or create for each duplicate
4. **Intelligent Updates** - Merges descriptions and adds comments explaining changes
5. **Batch Mode Support** - Auto-skips duplicates in batch mode
6. **Meeting Tracking** - Records which meetings have been processed

## How It Works

### 1. Duplicate Detection Process

When creating tasks, the system:

1. **Fetches existing tasks** from the destination ClickUp list
2. **Compares each new task** against existing tasks using fuzzy string matching
3. **Calculates similarity score** - 85% or higher = potential duplicate
4. **Compares task details** - checks due date, assignees, description
5. **Prompts for action** - asks what to do with the duplicate

### 2. Similarity Matching

The system uses `SequenceMatcher` to calculate how similar two task names are:

```python
"Create overlay test for bitkey wallet"
vs
"Create overlay test for bitkey"

= 92% match (detected as duplicate)
```

**Threshold: 85%**
- Tasks with 85%+ similarity are flagged as potential duplicates
- You can override and create anyway if it's not a real duplicate

### 3. Change Detection

The system detects these changes:

- **Due Date Changes** - Old: "2025-10-25" → New: "2025-10-30"
- **Assignee Changes** - Old: Drew → New: Art
- **Description Changes** - New information added to description

### 4. Interactive Prompt

When a duplicate is found, you see:

```
==================================================================
⚠️  POTENTIAL DUPLICATE DETECTED
==================================================================

📋 Existing Task (92% match):
   Name: Create overlay test for bitkey wallet
   ID: 86h3fn9kt
   URL: https://app.clickup.com/t/86h3fn9kt
   Status: In Progress
   Assignees: Drew
   Due Date: 2025-10-25

🆕 New Task:
   Name: Create overlay test for bitkey
   Assignees: Drew
   Due Date: 2025-10-30

📝 Detected Changes:
   Due date: 2025-10-25 → 2025-10-30

==================================================================
What would you like to do?
  1) Skip - Don't create (task already exists)
  2) Update - Update existing task with new information
  3) Create - Create new task anyway (ignore duplicate)
==================================================================

Your choice (1/2/3): _
```

### 5. Update Behavior

When you choose to **Update**:

1. **Due date is updated** if it changed
2. **Assignees are updated** if they changed
3. **Descriptions are merged**:
   ```markdown
   Original description content

   ---
   Updated from new meeting notes:
   New information from the latest meeting
   ```

4. **Comment is added**:
   ```markdown
   Updated from meeting: **Drew : Chad standup**
   Date: 2025-10-19 14:30
   Due date changed: 2025-10-25 → 2025-10-30
   New information added to description
   ```

## Usage

### Interactive Mode (Default)

```bash
./bin/gut-automate
```

When duplicates are found, you'll be prompted to choose an action for each one.

### Batch Mode

```bash
./bin/gut-automate --batch
```

In batch mode, duplicates are **automatically skipped** and logged to console.

## Use Cases

### Use Case 1: Task Mentioned in Multiple Meetings

**Scenario**: A task was created from Monday's meeting, then mentioned again in Friday's meeting with an updated due date.

**What happens**:
1. System detects the existing task (high similarity)
2. Identifies due date changed
3. Prompts you to update
4. Updates the due date and adds a comment

**Result**: One task with updated info, not a duplicate

### Use Case 2: Re-processing Old Emails

**Scenario**: You mark old emails as unread and re-process them.

**What happens**:
1. System fetches all existing tasks from destination list
2. Compares each "new" task against existing ones
3. Finds matches and prompts to skip
4. No duplicates created

**Result**: Existing tasks preserved, no duplicates

### Use Case 3: Similar but Different Tasks

**Scenario**: Two related tasks with similar names:
- "Create overlay test for bitkey wallet"
- "Create overlay test for bitkey app"

**What happens**:
1. System calculates 88% similarity (above threshold)
2. Shows both tasks side-by-side
3. You choose option 3 (Create) because they're different
4. Both tasks exist

**Result**: Both tasks created (not a false positive)

## Meeting Tracking

The system tracks which meetings have been processed in:

```
data/processed_meetings.json
```

**Example**:
```json
{
  "version": "1.0",
  "last_updated": "2025-10-19 14:30:00",
  "meetings": [
    {
      "doc_id": "abc123def456",
      "meeting_title": "Drew : Chad standup",
      "email_id": "xyz789",
      "processed_date": "2025-10-19 14:30:00",
      "tasks_created": [
        {
          "task_id": "86h3fn9kt",
          "task_name": "Create overlay test",
          "list_id": "901112154120"
        }
      ]
    }
  ]
}
```

This helps:
- Track which meetings you've already processed
- Link tasks back to source meetings
- Avoid re-processing the same meeting multiple times

## Configuration

### Similarity Threshold

Default: **85%**

To change, modify the threshold in `gut_automate/core.py`:

```python
matches = find_similar_tasks(task_data, existing_tasks, threshold=0.85)
```

**Recommendations**:
- **90%+** - Very strict (only near-exact matches)
- **85%** - Recommended (catches real duplicates, few false positives)
- **80%** - More lenient (more false positives)

### Batch Mode Behavior

In batch mode, duplicates are automatically skipped. To change this behavior, modify the `prompt_duplicate_action` function in `gut_automate/core.py`:

```python
if BATCH_MODE:
    print("[BATCH MODE: auto-selecting 'skip']")
    return 'skip'  # Change to 'update' or 'create' if desired
```

## Limitations

1. **List Scope Only** - Only checks the destination list, not entire workspace
2. **Name-Based Matching** - Relies on task name similarity (doesn't check description content)
3. **No Archived Tasks** - Doesn't check archived or closed tasks
4. **Sequential Processing** - Each task is checked one at a time (not bulk)

## Future Enhancements

Possible improvements:
- Check entire workspace for duplicates
- Content-based matching (not just name)
- Bulk duplicate detection before processing
- Machine learning for better matching
- Duplicate detection for subtasks

## Troubleshooting

### "Too many false positives"

**Solution**: Increase similarity threshold to 90%+

### "Missing real duplicates"

**Solution**: Decrease similarity threshold to 80%

### "Want to check entire workspace, not just list"

**Solution**: Modify `get_tasks_from_list()` to fetch from workspace instead

### "Batch mode creating duplicates"

**Solution**: Verify `BATCH_MODE` environment variable is set correctly

## API Rate Limits

**API Calls Per Meeting**:
- 1 call to fetch existing tasks (per destination list)
- 1 call per task update (if updating)
- 1 call per comment (if updating)

**Example**: Processing 10 tasks with 3 duplicates (all updated):
- 1 fetch + 3 updates + 3 comments = 7 API calls

This is well within ClickUp's rate limits (100 requests/minute).

## Related Documentation

- [Usage Guide](USAGE_GUIDE.md) - How to run gutAutomate
- [Approval Workflow Guide](APPROVAL_WORKFLOW_GUIDE.md) - Interactive approval process
- [Smart Destination Guide](SMART_DESTINATION_GUIDE.md) - How destinations are detected
