#!/usr/bin/env python3
"""
smart_meeting_processor.py - Helper functions for Claude Code to process meetings with approval

This module contains functions that Claude Code calls to implement the smart meeting
processing workflow with user approval.
"""

import re
from difflib import SequenceMatcher
from meeting_learning import load_learned_patterns, apply_learned_patterns


def fuzzy_match_score(str1, str2):
    """Calculate fuzzy match score between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def check_abbreviation_match(keyword, text):
    """
    Check if a keyword matches common abbreviations in text.

    Examples:
    - "rick ross" matches "RR"
    - "wiz khalifa" matches "WK"
    - "new year" matches "NYE"

    Returns:
        float: Confidence score 0.0-1.0
    """
    keyword_lower = keyword.lower()
    text_lower = text.lower()

    # Common abbreviation mappings
    abbreviations = {
        'rr': ['rick ross', 'rick', 'ross'],
        'wk': ['wiz khalifa', 'wiz', 'khalifa'],
        'nye': ['new year', 'newyear', 'new years'],
        'ctv': ['connected tv', 'ctv'],
        'mmb': ['mike', 'honey']
    }

    # Check if text contains any abbreviation
    for abbrev, expansions in abbreviations.items():
        if abbrev in text_lower:
            # Check if keyword matches any expansion
            for expansion in expansions:
                if expansion in keyword_lower or keyword_lower in expansion:
                    return 0.9  # High confidence for abbreviation match

    # Check if keyword is an abbreviation that matches text
    for abbrev, expansions in abbreviations.items():
        if abbrev == keyword_lower:
            for expansion in expansions:
                if expansion in text_lower:
                    return 0.9

    return 0.0


def detect_destination_from_hierarchy(meeting_title, meeting_content, workspace_hierarchy):
    """
    Detect ClickUp destination using learned patterns first, then fuzzy matching.

    Args:
        meeting_title: Title of the meeting
        meeting_content: Full meeting notes content (including transcript)
        workspace_hierarchy: ClickUp workspace structure with spaces/folders/lists

    Returns:
        dict: Best match with confidence score, or None if no good match
    """
    # STEP 1: Check learned patterns first (highest priority)
    patterns = load_learned_patterns()
    learned_result = apply_learned_patterns(meeting_title, meeting_content, patterns)

    if learned_result:
        destination, confidence, source = learned_result
        print(f"  ✓ Learned pattern match found via {source} (confidence: {confidence:.0%})")

        # If it's a project alias (no list_id), we need to resolve it
        if destination.get('list_id') is None:
            print(f"    Resolving list_id for: {destination['folder_name']} → {destination['list_name']}")
            # Find the list_id from workspace hierarchy
            for space in workspace_hierarchy.get('spaces', []):
                for folder in space.get('folders', []):
                    if folder.get('name', '') == destination['folder_name']:
                        for list_item in folder.get('lists', []):
                            if list_item.get('name', '') == destination['list_name']:
                                destination['list_id'] = list_item.get('id', '')
                                break

        # Return learned pattern match with high confidence
        return {
            'space_name': 'Clients',  # Default space
            'folder_name': destination['folder_name'],
            'list_name': destination['list_name'],
            'list_id': destination['list_id'],
            'confidence': confidence,
            'method': f'learned_pattern ({source})',
            'folder_score': confidence,
            'list_score': confidence
        }

    # STEP 2: Fall back to fuzzy matching if no learned pattern
    print("  No learned pattern match, falling back to fuzzy matching...")

    best_match = None
    best_score = 0.0
    threshold = 0.5  # Minimum confidence score

    # Extract key words from BOTH meeting title AND content (ignore common words)
    stopwords = {
        'meeting', 'sync', 'standup', 'team', 'recurring', 'notes', 'the', 'a', 'an',
        'fwd', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep',
        '2024', '2025', '2026', 'will', 'would', 'could', 'should', 'have', 'has', 'had',
        'this', 'that', 'these', 'those', 'with', 'from', 'about', 'into', 'through',
        'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
        'all', 'each', 'other', 'some', 'such', 'only', 'own', 'same', 'than', 'too',
        'very', 'can', 'just', 'don', 'now', 'discussion', 'suggested'
    }

    # Get words from title
    title_words = [w.lower() for w in re.findall(r'\b\w+\b', meeting_title) if w.lower() not in stopwords]

    # Get words from content (extract meaningful keywords)
    # Focus on capitalized words (likely names/brands) and content words
    content_text = meeting_content[:5000] if meeting_content else ""  # First 5000 chars

    # Extract capitalized words (likely proper nouns - client/project names)
    proper_nouns = set(re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', content_text))

    # Extract all words and count frequency
    all_content_words = re.findall(r'\b\w+\b', content_text.lower())
    word_freq = {}
    for word in all_content_words:
        if word not in stopwords and len(word) > 3:  # Skip short and common words
            word_freq[word] = word_freq.get(word, 0) + 1

    # Get top 20 most frequent meaningful words from content
    frequent_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
    content_keywords = [word for word, _ in frequent_words]

    # Combine: title words (highest priority) + proper nouns + frequent content words
    all_keywords = title_words + [pn.lower() for pn in proper_nouns] + content_keywords

    # Remove duplicates while preserving order
    seen = set()
    keywords = []
    for word in all_keywords:
        if word not in seen and word not in stopwords:
            seen.add(word)
            keywords.append(word)

    print(f"  Keywords extracted: {', '.join(keywords[:15])}...")  # Show first 15

    # Traverse hierarchy and score matches
    for space in workspace_hierarchy.get('spaces', []):
        for folder in space.get('folders', []):
            folder_name = folder.get('name', '')

            # Score folder name against ALL keywords (title + content)
            folder_score = 0.0
            for word in keywords:
                # Exact substring match
                if word in folder_name.lower() or folder_name.lower() in word:
                    folder_score = max(folder_score, 0.9)
                # Fuzzy match
                else:
                    folder_score = max(folder_score, fuzzy_match_score(word, folder_name))

            for list_item in folder.get('lists', []):
                list_name = list_item.get('name', '')
                list_id = list_item.get('id', '')

                # Score list name against ALL keywords (title + content)
                list_score = 0.0
                for word in keywords:
                    # Check abbreviation match first (e.g., "rick ross" → "RR")
                    abbrev_score = check_abbreviation_match(word, list_name)
                    if abbrev_score > 0:
                        list_score = max(list_score, abbrev_score)
                    # Exact substring match
                    elif word in list_name.lower() or list_name.lower() in word:
                        list_score = max(list_score, 0.9)
                    # Fuzzy match
                    else:
                        list_score = max(list_score, fuzzy_match_score(word, list_name))

                # Combined score (weighted: folder 70%, list 30%)
                combined_score = (folder_score * 0.7) + (list_score * 0.3)

                if combined_score > best_score:
                    best_score = combined_score
                    best_match = {
                        'space_name': space.get('name', 'Clients'),
                        'folder_name': folder_name,
                        'list_name': list_name,
                        'list_id': list_id,
                        'confidence': combined_score,
                        'method': 'fuzzy_match',
                        'folder_score': folder_score,
                        'list_score': list_score
                    }

    if best_match and best_score >= threshold:
        return best_match
    else:
        return None


def generate_ai_analysis_prompt(meeting_content, meeting_title, workspace_hierarchy):
    """
    Generate a prompt for Claude to analyze meeting content and determine project.

    Args:
        meeting_content: Full meeting notes content
        meeting_title: Meeting title
        workspace_hierarchy: Available folders/lists in workspace

    Returns:
        str: Prompt for Claude to analyze
    """
    # Extract list of available projects from hierarchy
    projects = []
    for space in workspace_hierarchy.get('spaces', []):
        for folder in space.get('folders', []):
            for list_item in folder.get('lists', []):
                projects.append({
                    'folder': folder.get('name'),
                    'list': list_item.get('name'),
                    'list_id': list_item.get('id')
                })

    # Limit to first 30 projects for context
    projects_text = "\n".join([f"- {p['folder']} → {p['list']}" for p in projects[:30]])

    # Get first 2000 chars of content for analysis
    content_preview = meeting_content[:2000]
    if len(meeting_content) > 2000:
        content_preview += "\n\n[... content truncated ...]"

    prompt = f"""Analyze this meeting and determine which ClickUp project/client it relates to.

Meeting Title: {meeting_title}

Meeting Content:
{content_preview}

Available Projects in ClickUp:
{projects_text}

Based on the meeting content, which project does this meeting most likely relate to?

Look for:
- Client/company names mentioned in the content
- Project names or campaign names
- People mentioned who work on specific projects
- Context clues about the work being discussed

Respond in JSON format ONLY:
{{
    "folder_name": "exact folder name from list above",
    "list_name": "exact list name from list above",
    "list_id": "the list ID",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of why this is the right project"
}}

If you cannot determine with confidence > 0.6, respond with:
{{"error": "insufficient_context", "reasoning": "explanation"}}
"""

    return prompt


def format_task_preview(meeting_title, action_items, destination):
    """
    Format tasks for preview display.

    Args:
        meeting_title: Title of the meeting
        action_items: List of action items with task/assignee/priority/etc
        destination: Detected destination with confidence

    Returns:
        str: Formatted preview text
    """
    lines = []

    lines.append(f"\n📋 **{meeting_title}**")
    lines.append(f"📍 Destination: {destination['folder_name']} → {destination['list_name']}")
    lines.append(f"🎯 Confidence: {destination['confidence']:.0%} ({destination['method']})")
    lines.append(f"📊 Action Items: {len(action_items)}")
    lines.append("")

    for i, item in enumerate(action_items, 1):
        task_preview = item['task'][:80] + ('...' if len(item['task']) > 80 else '')
        assignee = item.get('assignee', 'Unassigned')
        priority = item.get('priority', 'normal')
        due_date = item.get('due_date', {}).get('date_string', 'No due date')

        lines.append(f"  {i}. {task_preview}")
        lines.append(f"     👤 {assignee} | ⚡ {priority} | 📅 {due_date}")

    return "\n".join(lines)
