# Meeting Processing Approval Workflow

## Overview
The meeting automation now includes an **interactive approval workflow** where you review everything before tasks are created in ClickUp.

## How It Works

### Step-by-Step Workflow

When you say **"process my meetings"** to Claude Code:

#### 1. Discovery Phase
```
🔍 Finding unread meeting notes emails...
✓ Found 2 unread meeting(s)
```

Claude shows you:
- How many meetings were found
- Meeting titles
- Email dates

#### 2. Destination Detection Phase
For each meeting, Claude:
- Fetches your workspace hierarchy via ClickUp MCP
- Runs **fuzzy matching** on meeting title keywords
- If confidence < 50%, uses **AI analysis** of meeting content
- Shows you the detected destination with confidence score

Example output:
```
📋 "VFX Production Approach" Oct 17, 2025
📍 Destination: Gopuff → NYE RR + WK
🎯 Confidence: 75% (ai_analysis)
📊 Action Items: 9

  1. Pablo Saltiveri will record everything with an Insta 360 camera...
     👤 Pablo Saltiveri | ⚡ normal | 📅 No due date

  2. Aidan Wilde will do some research on the exact lens to use...
     👤 Aidan Wilde | ⚡ normal | 📅 No due date

  [... 7 more tasks ...]
```

#### 3. Approval Phase
Claude asks you to approve:
```
Found 2 meetings with 15 total tasks.

Do you want to:
1. Create all tasks (approve all)
2. Select specific meetings to process
3. Cancel (don't create any tasks)
```

Your options:
- **"all"** or **"1"**: Create all tasks from all meetings
- **"select"** or **"2"**: Choose which meetings to process
- **"cancel"** or **"3"**: Don't create any tasks

If you select specific meetings:
```
Which meetings do you want to process? (comma-separated numbers)
Example: 1,3 or just 2

Your choice: 1
```

#### 4. Creation Phase
Claude creates the approved tasks:
```
✓ Creating 9 tasks in Gopuff → NYE RR + WK...
  ✓ Task 1/9 created
  ✓ Task 2/9 created
  ...
  ✓ Task 9/9 created

✓ Copied meeting notes to Collective Meeting Notes
✓ Marked email as read
✓ Created notification task for Drew

Summary:
• 9 tasks created in Gopuff → NYE RR + WK
• View tasks: https://app.clickup.com/...
```

## Confidence Levels Explained

### High Confidence (>70%)
**What it means**: Very likely the correct destination

**Examples**:
- Meeting title: "Gopuff NYE Team Sync"
- Detected: Gopuff → NYE RR + WK
- Confidence: 82% (fuzzy_match)

**Action**: Safe to approve

### Medium Confidence (50-70%)
**What it means**: Probably correct, but review recommended

**Examples**:
- Meeting title: "VFX Production Approach"
- Detected: Gopuff → NYE RR + WK (via AI analysis of "Rick Ross", "Wiz" mentions)
- Confidence: 65% (ai_analysis)

**Action**: Review the destination before approving

### Low Confidence (<50%)
**What it means**: No confident match found, using default

**Examples**:
- Meeting title: "Team Lunch Discussion"
- Detected: Gut Feeling → Operations (fallback)
- Confidence: 0% (fallback)

**Action**: Review and potentially move tasks later, or cancel and manually specify destination

## Approval Options

### Option 1: Approve All
Best when:
- All destinations look correct
- All confidence scores are >70%
- You trust the automation

What happens:
- All tasks from all meetings are created
- Emails marked as read
- Docs copied to shared drive
- Notification created

### Option 2: Select Specific Meetings
Best when:
- Some destinations are uncertain
- You want to process only certain meetings
- Mixed confidence levels

What happens:
- Only selected meetings are processed
- Unselected emails remain unread for later
- Can re-run the automation for remaining meetings

### Option 3: Cancel
Best when:
- Destinations look wrong
- You need to reorganize ClickUp first
- You want to review meeting content manually

What happens:
- No tasks created
- No emails marked as read
- No changes to ClickUp
- Can re-run the automation anytime

## Manual Override

If the detected destination is wrong, you can:

1. **Cancel the automation**
2. **Manually specify the destination** (future feature)
3. **Let it create in default location**, then move tasks in ClickUp

## Common Scenarios

### Scenario 1: Perfect Match
```
📋 "Gopuff NYE Team Sync" Oct 17, 2025
🎯 Confidence: 82% (fuzzy_match)
📍 Gopuff → NYE RR + WK

Action: Approve immediately ✓
```

### Scenario 2: AI Fallback (Good)
```
📋 "VFX Production Approach" Oct 17, 2025
🎯 Confidence: 75% (ai_analysis)
📍 Gopuff → NYE RR + WK
💡 Reasoning: Meeting discusses Rick Ross, Wiz, and references Gopuff campaign

Action: Review reasoning, then approve ✓
```

### Scenario 3: No Match (Default)
```
📋 "Weekly Team Standup" Oct 17, 2025
🎯 Confidence: 0% (fallback)
📍 Gut Feeling → Operations
⚠️  No project identified from title or content

Action: Review, consider canceling and adding more context to meeting title
```

### Scenario 4: Multiple Meetings
```
Found 3 meetings:

1. Gopuff NYE Team Sync (82% confidence) - 5 tasks
2. BevMo Holiday CTV Review (78% confidence) - 8 tasks
3. Team Lunch Discussion (0% confidence) - 2 tasks

Action: Select meetings 1 and 2, cancel meeting 3
```

## Tips for Better Detection

### 1. Use Descriptive Meeting Titles
**Good**: "Gopuff NYE Campaign - VFX Review"
**Bad**: "Friday Meeting"

### 2. Mention Client/Project Names
Include the client or project name in the meeting title for better fuzzy matching.

### 3. Keep Meeting Notes Organized
The AI analyzes the content, so having client names and project details in the notes helps.

### 4. Review Low Confidence Matches
Always review destinations with <70% confidence before approving.

## Comparison: Old vs New Workflow

### Old Workflow (No Approval)
```
You: "process my meetings"
Claude: *immediately creates all tasks*
You: "Wait, those went to the wrong place!"
```

### New Workflow (With Approval)
```
You: "process my meetings"
Claude: *shows preview with destinations and confidence*
You: *reviews and approves*
Claude: *creates tasks in correct locations*
You: "Perfect!"
```

## Future Enhancements

Planned improvements:
- [ ] Manual destination override during approval
- [ ] Save custom mappings (learn from corrections)
- [ ] Batch edit destinations before creating
- [ ] Preview task details (full description, context)
- [ ] Confidence score improvements
- [ ] Support for multi-project meetings (split tasks)

## Troubleshooting

### "All destinations showing 0% confidence"
**Cause**: Meeting titles too generic, no project keywords in content
**Fix**: Add project/client names to meeting titles

### "Wrong destination detected with high confidence"
**Cause**: Similar keywords (e.g., "BevMo" and "Bev")
**Fix**: Use more specific project names in ClickUp or meeting titles

### "AI analysis taking too long"
**Cause**: Very long meeting notes (>10,000 chars)
**Fix**: Normal, be patient - AI reads the full content

### "Can't approve, script hangs"
**Cause**: Waiting for input but not showing prompt
**Fix**: Check terminal output, look for approval question

## Commands Summary

```bash
# Process meetings with approval (recommended)
> process my meetings

# Process specific meeting by email ID (advanced)
> process meeting EMAIL_ID

# Reprocess meetings that were skipped
> process my meetings again
```
