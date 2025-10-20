# gutAutomate

Automatically create ClickUp tasks from Gemini meeting notes.

## Features

✅ Finds unread Gemini meeting notes from Gmail
✅ Automatically marks processed emails as read (prevents duplicates)
✅ Copies meeting docs to "Collective Meeting Notes" shared drive
✅ Extracts action items with context from Google Docs
✅ Smart destination detection based on meeting title
✅ Automatic due date extraction from meeting context
✅ Team member assignment with single-name shortcuts (drew, art, matt, kato, paula)
✅ Filters out Ryan Joseph from task assignments
✅ Interactive approval workflow with flexible meeting selection
✅ Rich task descriptions with meeting context
✅ Notification tasks in Automation Summaries list

## Installation

1. Install required packages:
```bash
pip3 install google-auth-oauthlib google-auth-httplib2 google-api-python-client requests python-dotenv
```

2. Set up Google OAuth credentials:
   - Place `client_secrets.json` in the project directory
   - Run the script once to authenticate
   - **Note**: Requires Google Drive access for copying meeting notes to shared drive
   - If you previously used this script, delete `token.json` to re-authenticate with new scopes

3. Configure `.env` file:
   Create a `.env` file with the following settings:
   ```
   # ClickUp API Token (get from: https://app.clickup.com/settings/apps)
   CLICKUP_API_TOKEN=your_token_here

   # Default assignee for tasks (when no one is specifically mentioned)
   DEFAULT_ASSIGNEE=drew@gutfeeling.agency

   # Assignee name mapping (maps names from meeting notes to ClickUp emails)
   # Supports both full names and single-name nicknames (case-insensitive)
   ASSIGNEE_MAP=Drew=drew@gutfeeling.agency,Drew Gilbert=drew@gutfeeling.agency,drew=drew@gutfeeling.agency,Art=art@gutfeeling.agency,Art Okoro=art@gutfeeling.agency,art=art@gutfeeling.agency,Matt=matt@gutfeeling.agency,Matt Rose=matt@gutfeeling.agency,matt=matt@gutfeeling.agency,Kato=kato@gutfeeling.agency,Kato Ceaser=kato@gutfeeling.agency,kato=kato@gutfeeling.agency

   # Names to IGNORE when assigning tasks (never assign to these people)
   # Format: comma-separated list of names
   IGNORE_ASSIGNEES=Ryan Joseph
   ```

   **Team Member Shortcuts:**
   The script recognizes these single-name mentions (case-insensitive):
   - `drew` → Drew Gilbert (drew@gutfeeling.agency)
   - `art` → Art Okoro (art@gutfeeling.agency)
   - `matt` → Matt Rose (matt@gutfeeling.agency)
   - `kato` → Kato Ceaser (kato@gutfeeling.agency)
   - `paula` → Paula Aparicio (paula@gutfeeling.agency)

   **Assignee Resolution Logic:**
   1. **Name Extraction**:
      - Full names: "Drew Gilbert", "Art Okoro", "Matt Rose", "Kato Ceaser", "Paula Aparicio"
      - Single names: "drew", "art", "matt", "kato", "paula" (case-insensitive)
   2. **Ignore List**: Filters out names in `IGNORE_ASSIGNEES` (Ryan Joseph is NEVER assigned)
   3. **Resolution**:
      - If valid names found → assign to first non-ignored person
      - If only ignored names found → assign to `DEFAULT_ASSIGNEE`
      - If no names found → assign to `DEFAULT_ASSIGNEE`
   4. **Email Mapping**: Resolves names to emails using `ASSIGNEE_MAP`

   **Examples:**
   - `"Drew will review"` → drew@gutfeeling.agency
   - `"drew needs to update docs"` → drew@gutfeeling.agency (case-insensitive)
   - `"Art and Matt coordinate"` → art@gutfeeling.agency (first person)
   - `"kato to deploy"` → kato@gutfeeling.agency
   - `"Ryan Joseph will handle"` → drew@gutfeeling.agency (ignored → default)
   - `"Update the docs"` → drew@gutfeeling.agency (no name → default)

## Usage

### Standalone Mode (Create Tasks via ClickUp API)
```bash
python3 gutAutomate.py
```
- Reviews all unread Gemini meeting notes
- Shows previews of tasks to be created
- **Creates tasks directly using ClickUp REST API**
- Requires ClickUp API token (prompted if not found)

### Claude Mode (Create Tasks in ClickUp)
```bash
python3 gutAutomate.py claude
```
- Same as standalone mode, but actually creates tasks
- Requires Claude Code with ClickUp MCP access
- Creates tasks via `mcp__clickup__clickup_create_bulk_tasks`
- Sends notifications to Automation Summaries list

## Workflow

1. **Email Discovery**: Finds unread emails from Gemini with "Notes" in subject
2. **Initial Approval**: Shows meeting list, prompts for approval
3. **Mark as Read**: Approved emails are automatically marked as read (prevents re-processing)
4. **Archive Copy**: Copies meeting doc to "Collective Meeting Notes" shared drive with same title
5. **Content Fetching**: Fetches Google Docs content for approved meetings only
6. **Action Item Parsing**: Extracts action items from "Suggested next steps" section
7. **Smart Destination**: Auto-detects ClickUp list based on meeting title
8. **Preview & Confirm**: Shows detailed task preview for final approval
9. **Task Creation**: (Claude mode only) Creates tasks and notifications

## Interactive Prompts

### Meeting Selection
```
Process ALL meetings? (y/n/select):
```
- `y` - Process all meetings
- `n` - Process none
- `select` - Choose specific meetings (e.g., "1,3,4")

### Task Confirmation
```
Create these tasks in ClickUp? (y/n):
```
- `y` - Proceed with task creation
- `n` - Cancel and skip this meeting

## Smart Features

### Destination Detection
The script automatically routes tasks to the correct ClickUp list based on keywords:
- "BevMo" or "Holiday CTV" → Clients → BevMo → Holiday CTV 2025
- Default → Clients → Gut Feeling → Operations

### Due Date Extraction
Automatically infers due dates from meeting context:
- "by end of day" / "today" → Same day as meeting
- "tonight" → Same day (marked urgent)
- "Monday" → Next Monday from meeting date
- "in advance" → Day before referenced date

### Ryan Joseph Filtering
When multiple people are mentioned in a task (e.g., "Art Okoro and Ryan Joseph will..."), the task is assigned to the other person, not Ryan Joseph.

## Task Structure

Each created task includes:
- **Name**: The action item text
- **Description**: Full action item + relevant context from meeting + source
- **Assignee**: Auto-resolved from name
- **Due Date**: Extracted from context (relative to meeting date)
- **Priority**: urgent/high/normal based on keywords
- **Tags**: meeting-action-item, [project-tag]

## Notification

After processing, a notification task is created in:
- **List**: Automation Summaries (Clients → Gut Feeling)
- **Name**: 🤖 gutAutomate in full effect
- **Content**: Meeting name, task count, timestamp
- **Assigned to**: drew@gutfeeling.agency

## Examples

### Example 1: Single Meeting
```bash
$ python3 gutAutomate.py

Found 1 unread meeting note(s)

Meeting 1: "BevMo Recurring StandUp" Oct 17, 2025
  Date: Fri, 17 Oct 2025 19:07:18 +0000

Process ALL meetings? (y/n/select): y

✓ 1 meeting(s) approved
Fetching content...
Found 5 action items
Destination: Clients → BevMo → Holiday CTV 2025

[Shows task preview]

Create these tasks in ClickUp? (y/n): y

✓ Tasks prepared successfully!
```

### Example 2: Multiple Meetings with Selection
```bash
$ python3 gutAutomate.py claude

Found 3 unread meeting note(s)

Meeting 1: "VFX Production Approach" Oct 17, 2025
Meeting 2: "BevMo Recurring StandUp" Oct 17, 2025
Meeting 3: "Team Sync" Oct 18, 2025

Process ALL meetings? (y/n/select): select

Enter meeting numbers to process: 1,3

✓ 2 meeting(s) approved
[Processes meetings 1 and 3, skips 2]
```

## Configuration

### Adding New Destination Mappings

Edit the `smart_destination_detection()` function:

```python
keyword_mappings = {
    'bevmo': {
        'space_name': 'Clients',
        'folder_name': 'BevMo',
        'list_name': 'Holiday CTV 2025',
        'list_id': '901112154120'
    },
    'your-project': {
        'space_name': 'Clients',
        'folder_name': 'Your Folder',
        'list_name': 'Your List',
        'list_id': 'YOUR_LIST_ID'
    },
}
```

## Files

- `gutAutomate.py` - Main script
- `client_secrets.json` - Google OAuth credentials (not in repo)
- `token.json` - Google OAuth token (generated on first run)

## Requirements

- Python 3.7+
- Google Workspace account with Gmail & Drive access
- ClickUp account (for Claude mode)
- Claude Code with ClickUp MCP server (for Claude mode)

## Notes

- The script uses the meeting date from the title (e.g., "Oct 17, 2025") as the reference point for relative due dates
- Action items are extracted from the "Suggested next steps" section of Gemini notes
- Context is matched using keywords from the action item and the "Details" section
- Tasks are created with markdown descriptions for rich formatting in ClickUp
