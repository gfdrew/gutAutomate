# Smart Destination Detection System

## Overview
The meeting processing automation now uses intelligent destination detection to automatically route tasks to the correct ClickUp folder and list based on meeting content.

## How It Works

### 3-Tier Detection Strategy

#### Tier 1: Fuzzy Matching (Primary)
- Extracts keywords from meeting title (e.g., "Gopuff NYE Team Sync" → ["gopuff", "nye"])
- Fetches your entire ClickUp workspace hierarchy
- Scores each folder/list against the keywords using:
  - **Exact substring matching**: "gopuff" in "Gopuff" folder = 80% confidence
  - **Fuzzy string matching**: "bevmo" vs "BevMo" = high similarity score
  - **Weighted scoring**: Folder name (70%) + List name (30%)
- **Threshold**: 50% confidence required to accept match

#### Tier 2: AI Analysis (Fallback)
If fuzzy matching confidence < 50%:
- Sends meeting content to Claude for analysis
- Claude reads the discussion and identifies which project it relates to
- Searches ClickUp workspace for matching project
- **Threshold**: 60% confidence required to accept AI suggestion

#### Tier 3: Default Fallback
If both methods fail:
- Routes to "Operations" list in "Gut Feeling" folder
- You can manually move tasks later

## File Structure

### Updated Files

**taskUpSolo.py** (Non-interactive automation)
- Updated `smart_destination_detection()` to accept meeting content
- Added fuzzy matching logic with workspace hierarchy support
- Added AI analysis fallback hooks
- Passes meeting content through the pipeline

**process_meetings_smart.py** (NEW - Claude Code integration)
- Prepares meeting data for Claude Code
- Outputs JSON with instructions for Claude to:
  1. Fetch workspace hierarchy via MCP
  2. Run smart destination detection
  3. Use AI analysis if needed
  4. Create tasks in correct location

**gutAutomate.py** (Helper functions)
- Contains shared fuzzy matching logic
- Defines AI analysis prompt generation
- Backwards compatible with existing scripts

## Usage

### With Claude Code (Recommended)
```bash
# Simply say to Claude:
"process my meetings"
```

Claude will:
1. Run the Python script to get meeting data
2. Fetch your workspace hierarchy via ClickUp MCP
3. Run smart fuzzy matching
4. Use AI analysis if fuzzy matching is uncertain
5. Create tasks in the correct destination
6. Show you where each task was created with confidence scores

### Standalone Mode
```bash
python3 taskUpSolo.py claude
```

Note: Standalone mode won't have access to MCP tools, so it can't fetch workspace hierarchy. It will use the legacy default fallback.

## Examples

### Example 1: High Confidence Match
```
Meeting: "Gopuff NYE Team Sync Oct 17, 2025"

🔍 Smart Destination Detection
Key words from title: gopuff, nye

✓ Found match: Gopuff → NYE RR + WK
  Confidence: 82% (folder: 80%, list: 85%)
  Method: fuzzy_match
```

### Example 2: AI Fallback
```
Meeting: "Q4 Review Meeting"

🔍 Smart Destination Detection
Key words from title: q4, review

✗ No confident match found (best score: 35%)

Strategy: AI analysis of meeting content...
✓ AI identified project: BevMo → Holiday CTV 2025
  Confidence: 75%
  Method: ai_analysis
```

### Example 3: Default Fallback
```
Meeting: "Team Lunch Discussion"

🔍 Smart Destination Detection
Key words from title: lunch, discussion

✗ No confident match found (best score: 12%)
✗ AI analysis did not produce confident result

⚠️ Using default fallback: Operations list
```

## Configuration

### Adjusting Confidence Thresholds

Edit `taskUpSolo.py`:

```python
# Line ~854: Fuzzy match threshold
threshold = 0.5  # 50% confidence required

# Line ~911: AI analysis threshold
if ai_result and ai_result.get('confidence', 0) > 0.6:  # 60% required
```

### Customizing Stopwords

Edit `taskUpSolo.py`:

```python
# Line ~857: Words to ignore in meeting titles
stopwords = {'meeting', 'sync', 'standup', 'team', 'recurring', 'notes', 'the', 'a', 'an'}
```

### Adjusting Score Weighting

Edit `taskUpSolo.py`:

```python
# Line ~885: Change folder vs list importance
combined_score = (folder_score * 0.6) + (list_score * 0.4)
# Higher folder weight = prioritize matching folder name
# Higher list weight = prioritize matching list name
```

## Troubleshooting

### Tasks going to wrong location?
1. Check the confidence score in the output
2. If confidence < 70%, the match might be uncertain
3. Add more specific keywords to your meeting titles
4. Ensure your ClickUp folder/list names match your meeting naming conventions

### Tasks defaulting to Operations?
1. Check if the meeting title contains meaningful project keywords
2. Verify your ClickUp workspace hierarchy includes the expected folders/lists
3. Try adding the project name explicitly to the meeting title

### AI analysis not working?
1. Ensure you're running through Claude Code (not standalone)
2. Check that meeting content was successfully fetched
3. Verify meeting content actually mentions the project/client name

## Future Enhancements

Potential improvements:
- [ ] Learn from manual corrections (if you move tasks, remember the mapping)
- [ ] Support for custom keyword mappings in .env file
- [ ] Confidence score history/analytics
- [ ] Multi-project detection (split tasks across multiple destinations)
- [ ] Integration with meeting attendees to infer project
