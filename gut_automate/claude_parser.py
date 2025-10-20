"""
Claude API integration for intelligent meeting notes parsing.

Uses Anthropic's Claude API to parse action items from meeting notes
with better accuracy than regex-based parsing.
"""

import os
import json
from anthropic import Anthropic

def parse_with_claude(notes_content, meeting_title=""):
    """
    Use Claude API to parse action items from meeting notes.

    Args:
        notes_content: Text content of meeting notes
        meeting_title: Title of the meeting

    Returns:
        list: List of action items with assignee, priority, due_date, context
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set - falling back to regex parsing")
        return None

    try:
        client = Anthropic(api_key=api_key)

        prompt = f"""Parse the following meeting notes and extract action items. For each action item:

1. Identify WHO is assigned (person's name)
2. Extract the TASK (what needs to be done)
3. Determine PRIORITY (urgent/high/normal/low)
4. Extract or infer DUE DATE (if mentioned, otherwise use meeting date)
5. Find relevant CONTEXT from the meeting details
6. IMPORTANT: Identify the PROJECT/CLIENT name that this task belongs to

Meeting Title: {meeting_title}

Meeting Notes:
{notes_content}

Return a JSON array with this structure:
[
  {{
    "task": "action item description",
    "assignee": "Person Name",
    "priority": "normal",
    "due_date_text": "end of day" or "tomorrow" or "next week",
    "context": "For PROJECT_NAME: relevant context explaining why this task is needed",
    "project": "PROJECT_NAME (e.g., BevMo, Gopuff, Total Wine, or leave empty if general)"
  }}
]

Rules:
- Skip vague items like "no suggested next steps"
- TEAM MEMBERS (valid assignees): Drew, Drew Gilbert, Matt, Matt Rose, Art, Art Okoro, Kato, Kato Ceaser, Paula, Paula Aparicio
- EXTERNAL PEOPLE (NOT valid assignees): Ryan Joseph, clients, agencies, vendors
- CRITICAL: The assignee must ALWAYS be a TEAM MEMBER, never an external person
- If the action involves communicating WITH an external person, assign to the team member doing the work
- Examples:
  * "Matt will talk to Ryan Joseph about the budget" → Assignee: "Matt Rose"
  * "Drew needs to send the brief to Ryan" → Assignee: "Drew Gilbert"
  * "Art will review shot list with Ryan Joseph" → Assignee: "Art Okoro"
  * "Go over shot list and send to Ryan" → Assignee: Look for WHO will do this (Drew/Matt/Art/etc)
- If no team member is mentioned explicitly, infer from context who would logically do this task
- Priority: urgent (same day), high (this week), normal (default), low (no rush)
- Keep task descriptions concise but clear
- IMPORTANT: In the context field, ALWAYS mention the project/client name (e.g., "BevMo", "Gopuff", "Total Wine") if the task relates to a specific client or project
- Extract context that explains WHY this task is needed and WHICH project it's for

Return ONLY the JSON array, no other text."""

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Track API usage
        usage = message.usage
        result = {
            'action_items': None,
            'usage': {
                'input_tokens': usage.input_tokens,
                'output_tokens': usage.output_tokens
            }
        }

        # Extract the response
        response_text = message.content[0].text.strip()

        # Parse JSON
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()

        action_items = json.loads(response_text)
        result['action_items'] = action_items

        print(f"✓ Claude API parsed {len(action_items)} action items")
        print(f"  Tokens: {usage.input_tokens} in, {usage.output_tokens} out")

        return result

    except Exception as e:
        print(f"⚠️  Claude API error: {e}")
        print("   Falling back to regex parsing")
        return None
