# Granular Approval Workflow

## What You Want

> "When you process my meeting notes I want to be asked for approval of each meeting
> and then approval of each meeting's tasks. As in if I approve 2 meetings I want to
> approve each set of tasks separately"

## New Workflow

### Step 1: Find All Meetings
I find all unread Gemini meeting notes.

### Step 2: Ask Which Meetings to Process
I show you ALL meetings and you select which ones (can be multiple).
**Example:** You select meetings 1 and 2.

### Step 3: Process Each Meeting Separately

For **each** selected meeting, I will:

#### 3a. Process the meeting
- Mark email as read
- Copy doc to shared drive
- Fetch content
- Parse action items with context

#### 3b. Show Preview
Show you the tasks for THIS meeting with full context.

#### 3c. Ask for Approval
**"Create these X tasks from [Meeting Title]?"**

You decide YES or NO for this specific meeting.

#### 3d. If YES: Create Tasks
Create the tasks via MCP for this meeting only.

#### 3e. Move to Next Meeting
Repeat 3a-3d for the next selected meeting.

## Example Flow

```
You: "Process my meeting notes"

Me: Found 3 unread meetings:
    1. Gopuff NYE Team Sync
    2. BevMo Recurring StandUp
    3. VFX Production Approach

    Which meetings would you like to process?

You: [Select "Gopuff NYE Team Sync" and "BevMo Recurring StandUp"]

Me: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Processing Meeting 1 of 2: "Gopuff NYE Team Sync"
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ✓ Marked email as read
    ✓ Copied to shared drive
    ✓ Found 3 action items:

    1. Finalize shot list (Art) - URGENT
       Context: Team needs to lock shot list before location scout...

    2. Book location for Dec 30 (Matt)
       Context: Venue must be secured by end of week...

    3. Review lighting setup (Pablo)
       Context: Client requested specific lighting approach...

    Create these 3 tasks from "Gopuff NYE Team Sync"?

You: [YES]

Me: ✓ Created 3 tasks in Gopuff NYE list

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Processing Meeting 2 of 2: "BevMo Recurring StandUp"
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ✓ Marked email as read
    ✓ Copied to shared drive
    ✓ Found 5 action items:

    1. Provide realistic budget (Matt)
       Context: Budget discussion for upcoming shoot...

    2. Confirm graphic outro card details (Matt)
       Context: Need to finalize design for video outro...

    3. Confirm discussion points and send invite (Matt)
       Context: Prepare agenda for client meeting...

    4. Include Total Wine references (Art)
       Context: Make sure creative includes brand elements...

    5. Go over shot list tonight (Art) - URGENT
       Context: Review and finalize complete shot list...

    Create these 5 tasks from "BevMo Recurring StandUp"?

You: [NO] (or YES)

Me: ✗ Skipped task creation for "BevMo Recurring StandUp"

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    SUMMARY
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ✓ "Gopuff NYE Team Sync" - 3 tasks created
    ✗ "BevMo Recurring StandUp" - skipped

    ✓ Created notification in Automation Summaries
```

## Benefits

✅ **Full control** - Approve each meeting's tasks independently
✅ **See context first** - Review tasks before approving
✅ **Selective creation** - Can skip meetings if needed
✅ **Clear separation** - Each meeting processed completely before moving to next

## Technical Implementation

For each selected meeting:
1. Run `process_with_mcp.py` for that single meeting
2. Parse JSON output
3. Show preview
4. AskUserQuestion: "Create these X tasks from [Meeting Title]?"
5. If YES: Call MCP tools
6. Move to next meeting

## Key Change

**Before:** Batch process all meetings, one approval at end
**After:** Process each meeting individually with separate approval
