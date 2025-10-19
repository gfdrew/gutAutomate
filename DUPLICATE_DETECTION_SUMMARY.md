# Duplicate Detection Feature Summary

## Date: October 19, 2025

## Overview

Implemented comprehensive duplicate detection and smart update system to prevent creating duplicate tasks when re-processing emails or when tasks are mentioned in multiple meetings.

## Problem Solved

**Before**: Re-processing old emails or tasks mentioned in multiple meetings would create duplicate tasks in ClickUp.

**After**: System detects duplicates, shows what changed, and lets you skip, update, or create.

## Key Features

### 1. Fuzzy Matching (85% threshold)
- Uses Python's `SequenceMatcher` for intelligent string comparison
- Detects duplicates even with minor wording differences
- Example: "Create overlay test for bitkey wallet" matches "Create overlay test for bitkey" at 92%

### 2. Smart Change Detection
Automatically detects:
- Due date changes
- Assignee changes
- New description information

### 3. Interactive Prompts
Shows side-by-side comparison and offers 3 options:
1. **Skip** - Don't create (task already exists)
2. **Update** - Update existing task with new info
3. **Create** - Create anyway (ignore duplicate warning)

### 4. Intelligent Updates
When updating:
- Due dates are updated if changed
- Assignees are updated if changed
- Descriptions are **merged** (old content preserved + new content added)
- Comment added explaining what changed

Example merged description:
```markdown
Original task description from first meeting

---
Updated from new meeting notes:
Additional context from the latest meeting
```

Example comment:
```markdown
Updated from meeting: **Drew : Chad standup**
Date: 2025-10-19 14:30
Due date changed: 2025-10-25 → 2025-10-30
New information added to description
```

### 5. Meeting Tracking
- Tracks processed meetings in `data/processed_meetings.json`
- Links tasks back to source meetings
- Prevents accidental re-processing

### 6. Batch Mode Support
- Automatically skips duplicates in batch mode
- Logs to console for review
- No interactive prompts

## Real-World Example

### Scenario: Task in Multiple Meetings

**Monday Meeting**: "Create overlay test for bitkey wallet"
- Creates task in ClickUp
- Due: Oct 25
- Assignee: Drew

**Friday Meeting**: Same task mentioned with updates
- "Create overlay test for bitkey - due Friday instead"
- System detects 92% match
- Shows comparison:
  ```
  Existing: Due Oct 25
  New:      Due Oct 30
  ```
- You choose "Update"
- Task updated with new due date
- Comment added: "Updated from meeting: Friday standup"

**Result**: One task with latest info, not a duplicate

## Implementation Details

### New Module: `gut_automate/duplicate_detection.py`

**Functions:**
- `find_similar_tasks()` - Fuzzy matching against existing tasks
- `compare_tasks()` - Detects what changed between tasks
- `merge_descriptions()` - Intelligently merges old and new descriptions
- `create_update_comment()` - Generates comment explaining changes
- `load_processed_meetings()` / `save_processed_meetings()` - Meeting tracking

### Core Enhancements: `gut_automate/core.py`

**New Functions:**
- `get_tasks_from_list()` - Fetch all existing tasks from ClickUp list
- `update_clickup_task()` - Update existing task via API
- `add_task_comment()` - Add comment to task via API
- `prompt_duplicate_action()` - Interactive duplicate handling prompt

**Workflow Integration:**
1. Fetch existing tasks from destination list (1 API call)
2. For each new task:
   - Check for duplicates using fuzzy matching
   - If duplicate found, compare to detect changes
   - Prompt user for action
   - Execute: skip / update / create
3. Show summary with created/updated/skipped counts

### API Calls

**Per meeting processing:**
- 1 call to fetch existing tasks from list
- 1 call per task update (if updating)
- 1 call per comment (if updating)

**Example**: 10 tasks, 3 duplicates updated:
- 1 fetch + 3 updates + 3 comments = 7 API calls
- Well within ClickUp's 100 requests/minute limit

## Usage

### Interactive Mode
```bash
./bin/gut-automate
```

When duplicates found, you'll be prompted to choose Skip/Update/Create for each.

### Batch Mode
```bash
./bin/gut-automate --batch
```

Duplicates automatically skipped and logged.

## Configuration

### Similarity Threshold

Default: 85%

Change in `gut_automate/core.py`:
```python
matches = find_similar_tasks(task_data, existing_tasks, threshold=0.85)
```

### Batch Behavior

Default: Auto-skip duplicates

Change in `prompt_duplicate_action()`:
```python
if BATCH_MODE:
    return 'skip'  # Change to 'update' or 'create' if desired
```

## Data Files

### `data/processed_meetings.json`

Tracks meeting processing history:

```json
{
  "version": "1.0",
  "last_updated": "2025-10-19 14:30:00",
  "meetings": [
    {
      "doc_id": "abc123",
      "meeting_title": "Drew : Chad standup",
      "email_id": "xyz789",
      "processed_date": "2025-10-19 14:30:00",
      "tasks_created": [
        {"task_id": "86h3fn9kt", "task_name": "Create overlay test", "list_id": "901112154120"}
      ]
    }
  ]
}
```

## Summary Output

### Before
```
TASK CREATION COMPLETE
✓ Created: 5
```

### After
```
TASK PROCESSING COMPLETE
➕ Created: 3
🔄 Updated: 2
⏭️  Skipped: 0
✗ Failed: 0
```

## Benefits

1. **No More Duplicates** - Re-processing emails doesn't create duplicates
2. **Always Current** - Tasks updated with latest info from newest meeting
3. **Context Preserved** - Merged descriptions keep all historical context
4. **Audit Trail** - Comments show when and why tasks were updated
5. **Flexible** - Choose skip/update/create for each duplicate
6. **Fast** - Single API call fetches all existing tasks

## Testing Recommendations

1. **Test with old email**: Mark an old processed email as unread and run again
2. **Test with updated task**: Create task, then process meeting with updated due date
3. **Test batch mode**: Run with --batch flag and verify duplicates skipped
4. **Test false positives**: Try similar but different task names

## Documentation

- **Full Guide**: `docs/DUPLICATE_DETECTION_GUIDE.md`
- Usage examples
- Configuration options
- Troubleshooting

## Git History

- **Commit**: `6db87b2` - "Add comprehensive duplicate detection and update system"
- **Branch**: `drew-gut-automate`
- **Files Modified**: 3
- **Lines Added**: 897

## Next Steps

1. Test with real meetings
2. Adjust similarity threshold if needed (85% is recommended starting point)
3. Monitor for false positives/negatives
4. Consider adding workspace-wide duplicate detection (currently list-scoped)
