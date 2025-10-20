# gutAutomate Standalone Edition

**Create ClickUp tasks directly from Gemini meeting notes using the ClickUp REST API**

This is the **standalone version** of gutAutomate that requires **no Claude/MCP dependencies**. It creates tasks directly via the ClickUp REST API.

## Features

✅ **Fully Independent** - No Claude/MCP required
✅ **Direct REST API** - Creates tasks directly in ClickUp
✅ **Interactive Approvals** - Review before creating each meeting's tasks
✅ **Smart Destination Detection** - Auto-routes tasks to correct lists
✅ **Duplicate Detection** - Prevents creating duplicate tasks
✅ **Learning System** - Improves destination detection over time
✅ **Team Assignment** - Automatically assigns tasks to team members
✅ **Due Date Extraction** - Intelligently parses dates from context

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/gfdrew/gutAutomate.git
cd gutAutomate
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.template .env
# Edit .env with your ClickUp API token and other settings
```

4. Set up Google OAuth credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API, Google Drive API, and Google Docs API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download credentials and save as `client_secrets.json`

### Usage

#### Interactive Mode (with approval prompts)
```bash
python3 -m gut_automate.core
# or
./bin/gut-automate
```

#### Batch Mode (auto-approve all)
```bash
./bin/gut-automate --batch
```

#### Claude Mode (create tasks via MCP)
```bash
./bin/gut-automate --claude
```

#### Batch + Claude Mode
```bash
./bin/gut-automate --batch --claude
```

## Project Structure

```
gutAutomate/
├── gut_automate/           # Main package
│   ├── __init__.py
│   ├── core.py             # Core automation logic
│   ├── learning.py         # Pattern learning system
│   ├── task_learning.py    # Task-level pattern matching
│   └── helpers.py          # Helper functions
├── bin/                    # Entry point scripts
│   └── gut-automate        # Main CLI script
├── scripts/                # Utility scripts
│   ├── create_backup.sh    # Create git backup tags
│   └── list_backups.sh     # List available backups
├── config/                 # Configuration files (not tracked in git)
├── data/                   # Data files
│   └── meeting_patterns_learned.json
├── tests/                  # Test files
├── docs/                   # Documentation
│   ├── USAGE_GUIDE.md
│   ├── APPROVAL_WORKFLOW_GUIDE.md
│   ├── SMART_DESTINATION_GUIDE.md
│   ├── CLAUDE_MODE_GUIDE.md
│   ├── CONTENT_BASED_MATCHING.md
│   └── ...
├── archive/                # Archived/legacy code
├── .env                    # Environment variables (not tracked in git)
├── .env.template           # Template for environment variables
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Configuration

### Environment Variables (.env)

```bash
# ClickUp API Token
CLICKUP_API_TOKEN=your_token_here

# Default assignee
DEFAULT_ASSIGNEE=your_email@gutfeeling.agency

# Assignee name mapping
ASSIGNEE_MAP=Name1=email1,Name2=email2

# Names to ignore
IGNORE_ASSIGNEES=Name1,Name2

# Google Drive archive path
MEETING_NOTES_ARCHIVE_PATH=/path/to/google/drive/folder
```

## How It Works

1. **Email Detection**: Scans Gmail for unread emails from Gemini with meeting notes
2. **Content Extraction**: Fetches Google Docs content and parses action items
3. **Smart Destination**: Uses learned patterns and keyword matching to determine the correct ClickUp destination
4. **Assignee Detection**: Extracts assignees from action items using the ASSIGNEE_MAP
5. **Task Creation**: Creates tasks in ClickUp with due dates, assignees, and descriptions
6. **Learning**: Stores successful patterns for future meetings

## Learning System

The learning system improves destination detection over time using:

- **Project Aliases**: Explicit project mentions (e.g., "bitkey", "bevmo")
- **Keyword Patterns**: Content-based keywords (e.g., "overlay test" → Block project)
- **Participant Patterns**: Meeting attendees as signals
- **Title Patterns**: Meeting title patterns (weakest signal)

Patterns are stored in `data/meeting_patterns_learned.json` and automatically applied to future meetings.

## Creating Backups

Before making significant changes, create a backup:

```bash
./scripts/create_backup.sh
```

This creates a git tag with a timestamp. To restore:

```bash
git checkout stable/YYYYMMDD-HHMMSS
```

## Documentation

- [Usage Guide](docs/USAGE_GUIDE.md) - Detailed usage instructions
- [Approval Workflow Guide](docs/APPROVAL_WORKFLOW_GUIDE.md) - Interactive approval process
- [Smart Destination Guide](docs/SMART_DESTINATION_GUIDE.md) - How destination detection works
- [Claude Mode Guide](docs/CLAUDE_MODE_GUIDE.md) - Using with Claude Code
- [Content Matching Guide](docs/CONTENT_BASED_MATCHING.md) - Pattern matching algorithms

## Development

### Running Tests

```bash
python3 -m pytest tests/
```

### Code Style

This project follows PEP 8 style guidelines. Format code with:

```bash
black gut_automate/
```

## Troubleshooting

### Google OAuth Issues

If you get authentication errors:
1. Delete `token.json`
2. Run the script again to re-authenticate
3. Make sure you've enabled the required APIs in Google Cloud Console

### ClickUp API Issues

- Verify your API token in `.env`
- Check that you have permission to create tasks in the target lists
- Visit https://app.clickup.com/settings/apps to manage your API token

## Differences from Claude Version

This standalone version differs from the main Claude/MCP version:

| Feature | Standalone Edition | Claude/MCP Version |
|---------|-------------------|-------------------|
| **Task Creation** | ClickUp REST API | MCP Tools via Claude Code |
| **Dependencies** | No Claude/Anthropic | Requires Claude Code + MCP |
| **Parsing** | Regex-based | Claude AI + Regex fallback |
| **Setup** | Simple pip install | Requires MCP server setup |
| **Usage** | Always interactive | Can be automated via Claude |
| **Location** | `/standalone` folder | Root directory |

**When to use Standalone:**
- You want simple, direct API integration
- You don't have Claude Code setup
- You prefer explicit control over task creation
- You want minimal dependencies

**When to use Claude/MCP version:**
- You have Claude Code with MCP servers
- You want AI-powered parsing for better accuracy
- You want integration with Claude workflows

## License

Proprietary - Gut Feeling Agency

## Support

For issues or questions, contact:
- Drew Gilbert: drew@gutfeeling.agency
- GitHub Issues: https://github.com/gfdrew/gutAutomate/issues

---

**Note:** This is the standalone edition. For the Claude/MCP version, see the root directory README.
