# gutAutomate Usage Guide

## Two Versions Available

### 1. **gutAutomate.py** - Interactive/Claude Mode Version
**Best for:** Manual runs with control OR automated Claude Code integration

**Usage:**
```bash
# Interactive mode (prompts for confirmation)
cd /Users/drew/Desktop/into_the_future
python3 gutAutomate.py

# Claude mode (fully automated with MCP)
python3 gutAutomate.py claude
```

**Features:**
- ✅ **Interactive Mode:** Prompts you to select meetings and confirm tasks
- ✅ **Claude Mode:** Auto-approves all meetings, creates tasks via MCP
- ✅ Shows preview with FULL CONTEXT from meeting notes
- ✅ Preserves Details section context in task descriptions
- ✅ Auto-detects and applies meeting tags (bevmo, vfx, total-wine)
- ✅ Extracts and assigns due dates from task text

**When in Interactive Mode:**
1. **"Your choice:"** → Enter meeting numbers (e.g., `2` or `1,2` or `all`)
2. **"Create these tasks?"** → Enter `y` to confirm

**When in Claude Mode:**
- ✅ Auto-approves ALL meetings
- ✅ Auto-confirms task creation
- ✅ Creates tasks directly in ClickUp via MCP tools
- ✅ ALL context preserved in task descriptions

---

### 2. **taskUpSolo.py** - Non-Interactive Version
**Best for:** Automated workflows, cron jobs, or when you want to process everything automatically

**Usage:**
```bash
cd /Users/drew/Desktop/into_the_future
python3 taskUpSolo.py claude
```

**Features:**
- ✅ Auto-processes ALL unread meeting notes
- ✅ No prompts or confirmations
- ✅ Perfect for automation
- ✅ Same functionality, just automated

**Behavior:**
- Automatically approves all meetings
- Automatically confirms task creation
- Runs from start to finish without user input

---

## Workflow (Both Versions)

1. **Email Discovery** - Find unread Gemini meeting notes
2. **Meeting Approval** - Select meetings (interactive) or auto-approve (claude/solo)
3. **Mark as Read** - Mark approved emails as read
4. **Archive Copy** - Copy docs to "Collective Meeting Notes" shared drive
5. **Content Fetch** - Get Google Doc content (with checkbox filtering)
6. **Parse Actions** - Extract action items with context from Details section
7. **Extract Context** - Find relevant context for each action item
8. **Extract Due Dates** - Parse natural language due dates from tasks
9. **Assign Team** - Resolve assignees (drew, art, matt, kato, paula)
10. **Detect Destination** - Auto-detect ClickUp list (bevmo, vfx, etc.)
11. **Auto-Tag** - Apply meeting-specific tags automatically
12. **Preview Tasks** - Show tasks with FULL context and confirm (interactive) or auto-confirm (claude/solo)
13. **Create Tasks** - Create in ClickUp via MCP (claude) or REST API (standalone)
14. **Send Notification** - Create summary task in Automation Summaries

---

## Examples

### Process specific meetings (Interactive)
```bash
python3 gutAutomate.py claude
# When prompted: "2" (for meeting 2 only)
# When prompted: "y" (to confirm)
```

### Process all meetings automatically (Non-Interactive)
```bash
python3 taskUpSolo.py claude
# No input needed - runs automatically
```

---

## Team Member Assignment

Both versions support these shortcuts (case-insensitive):
- `drew` → drew@gutfeeling.agency
- `art` → art@gutfeeling.agency
- `matt` → matt@gutfeeling.agency
- `kato` → kato@gutfeeling.agency
- `paula` → paula@gutfeeling.agency

**Note:** Ryan Joseph is automatically filtered out and never assigned tasks.

---

## Files

- **gutAutomate.py** - Interactive version (original)
- **taskUpSolo.py** - Non-interactive version (automated)
- **secureGut101825.py** - Backup from Oct 18, 2025
- **.env** - Configuration (API keys, team mapping)
- **token.json** - Google OAuth credentials (auto-generated)
- **client_secrets.json** - Google OAuth client secrets

---

## Troubleshooting

**"FileNotFoundError: client_secrets.json"**
→ The script now uses absolute paths, so this should be fixed

**"Weird 'Proj' characters in tasks"**
→ Fixed! Google Docs checkboxes are now filtered out

**"Need to re-authenticate"**
→ Delete `token.json` and run the script to get new OAuth permissions

**"Can't find shared drive"**
→ Make sure you have access to "Collective Meeting Notes" shared drive

---

## Which Version Should I Use?

| Scenario | Use This Version |
|----------|------------------|
| Manual run, want to review | `gutAutomate.py` |
| Want to skip some meetings | `gutAutomate.py` |
| Automated/scheduled run | `taskUpSolo.py` |
| Process everything quickly | `taskUpSolo.py` |
| Cron job or script | `taskUpSolo.py` |

