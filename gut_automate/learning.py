#!/usr/bin/env python3
"""
meeting_learning.py - Learning System for Meeting Destination Detection

This module provides functions to:
1. Load learned patterns from JSON database
2. Apply learned patterns to detect meeting destinations
3. Save new patterns when corrections are made
4. Update statistics on pattern usage and accuracy
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Get the project root directory (parent of gut_automate package)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATTERNS_FILE = os.path.join(PROJECT_ROOT, 'data', 'meeting_patterns_learned.json')


def load_learned_patterns(json_file_path: str = None) -> Dict:
    """
    Load learned patterns from JSON database.

    Args:
        json_file_path: Path to the patterns JSON file (defaults to data/meeting_patterns_learned.json)

    Returns:
        Dictionary containing all learned patterns, or empty structure if file doesn't exist
    """
    if json_file_path is None:
        json_file_path = DEFAULT_PATTERNS_FILE

    if not os.path.exists(json_file_path):
        return {
            "version": "1.0",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "patterns": {
                "title_patterns": {},
                "participant_patterns": {},
                "keyword_patterns": {},
                "project_aliases": {}
            },
            "statistics": {
                "total_patterns_learned": 0,
                "successful_applications": 0,
                "corrections_applied": 0,
                "accuracy_improvement": "pending"
            }
        }

    with open(json_file_path, 'r') as f:
        return json.load(f)


def normalize_text(text: str) -> str:
    """
    Normalize text for pattern matching.
    - Convert to lowercase
    - Remove extra spaces
    - Remove special characters except spaces
    """
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)  # Remove special chars
    text = re.sub(r'\s+', ' ', text)  # Normalize spaces
    return text.strip()


def check_title_pattern(meeting_title: str, patterns: Dict) -> Optional[Tuple[Dict, float]]:
    """
    Check if meeting title matches any learned title patterns.

    Args:
        meeting_title: The meeting title to check
        patterns: The patterns dictionary from load_learned_patterns()

    Returns:
        Tuple of (destination, confidence) if match found, None otherwise
    """
    normalized_title = normalize_text(meeting_title)
    title_patterns = patterns.get('patterns', {}).get('title_patterns', {})

    # Common variations for compound words
    common_compounds = {
        'standup': ['stand up', 'stand-up'],
        'sync': ['syncing', 'synchronization'],
        'meetup': ['meet up', 'meet-up']
    }

    for pattern_key, pattern_data in title_patterns.items():
        # Expand pattern with compound word variations
        pattern_expanded = pattern_key
        for compound, variants in common_compounds.items():
            if compound in pattern_key:
                # Try replacing compound with space-separated version
                for variant in variants:
                    pattern_expanded = pattern_key.replace(compound, variant)

        # Method 1: Check if pattern words are in title
        pattern_words = set(pattern_expanded.split())
        title_words = set(normalized_title.split())

        # Calculate match score - what percentage of pattern words are in title?
        if pattern_words:
            matched_words = pattern_words.intersection(title_words)
            match_ratio = len(matched_words) / len(pattern_words)

            # If 80%+ of pattern words match, it's a good match
            if match_ratio >= 0.8:
                destination = pattern_data['destination']
                confidence = pattern_data.get('confidence', 0.9) * match_ratio
                return (destination, confidence)

        # Method 2: Simple substring matching (fallback)
        if pattern_key in normalized_title:
            destination = pattern_data['destination']
            confidence = pattern_data.get('confidence', 0.9)
            return (destination, confidence)

    return None


def check_participant_pattern(meeting_content: str, patterns: Dict) -> Optional[Tuple[Dict, float]]:
    """
    Check if meeting participants match any learned participant patterns.

    Args:
        meeting_content: The meeting content/transcript
        patterns: The patterns dictionary from load_learned_patterns()

    Returns:
        Tuple of (destination, confidence) if match found, None otherwise
    """
    normalized_content = normalize_text(meeting_content)
    participant_patterns = patterns.get('patterns', {}).get('participant_patterns', {})

    for pattern_key, pattern_data in participant_patterns.items():
        # Pattern key is like "chad+drew+rose"
        participants = pattern_key.split('+')

        # Check if all participants are mentioned in content
        all_found = all(participant in normalized_content for participant in participants)

        if all_found:
            destination = pattern_data['destination']
            confidence = pattern_data.get('confidence', 0.85)
            return (destination, confidence)

    return None


def check_keyword_patterns(meeting_content: str, patterns: Dict) -> Optional[Tuple[Dict, float]]:
    """
    Check if meeting content contains any learned keyword patterns.

    Args:
        meeting_content: The meeting content/transcript
        patterns: The patterns dictionary from load_learned_patterns()

    Returns:
        Tuple of (destination, confidence) if match found, None otherwise
    """
    normalized_content = normalize_text(meeting_content)
    keyword_patterns = patterns.get('patterns', {}).get('keyword_patterns', {})

    # Track best match (highest confidence)
    best_match = None
    best_confidence = 0.0

    for pattern_key, pattern_data in keyword_patterns.items():
        # Pattern key might be single keyword or "keyword1+keyword2"
        keywords = pattern_key.split('+')

        # Check if all keywords are in content
        all_found = all(keyword in normalized_content for keyword in keywords)

        if all_found:
            confidence = pattern_data.get('confidence', 0.8)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = pattern_data['destination']

    if best_match:
        return (best_match, best_confidence)

    return None


def check_project_aliases(meeting_content: str, patterns: Dict) -> Optional[Tuple[str, str]]:
    """
    Check if meeting content contains any project aliases.

    Args:
        meeting_content: The meeting content/transcript
        patterns: The patterns dictionary from load_learned_patterns()

    Returns:
        Tuple of (folder_name, list_name) if match found, None otherwise
    """
    normalized_content = normalize_text(meeting_content)
    project_aliases = patterns.get('patterns', {}).get('project_aliases', {})

    for alias, location in project_aliases.items():
        if alias in normalized_content:
            # location is [folder_name, list_name]
            if len(location) == 2:
                return tuple(location)

    return None


def apply_learned_patterns(meeting_title: str, meeting_content: str,
                          patterns: Dict) -> Optional[Tuple[Dict, float, str]]:
    """
    Apply all learned patterns to detect meeting destination.
    Checks patterns in priority order: title > keywords > participants > aliases

    Args:
        meeting_title: The meeting title
        meeting_content: The meeting content/transcript
        patterns: The patterns dictionary from load_learned_patterns()

    Returns:
        Tuple of (destination, confidence, source) if match found, None otherwise
        destination: Dict with folder_name, list_name, list_id
        confidence: Float between 0 and 1
        source: String describing which pattern matched (e.g., "title_pattern", "keyword_pattern")
    """
    # Priority 1: Check title patterns (highest confidence)
    result = check_title_pattern(meeting_title, patterns)
    if result:
        return (result[0], result[1], "title_pattern")

    # Priority 2: Check keyword patterns (medium-high confidence)
    result = check_keyword_patterns(meeting_content, patterns)
    if result:
        return (result[0], result[1], "keyword_pattern")

    # Priority 3: Check participant patterns (medium confidence)
    result = check_participant_pattern(meeting_content, patterns)
    if result:
        return (result[0], result[1], "participant_pattern")

    # Priority 4: Check project aliases (provides folder/list names, not full destination)
    alias_result = check_project_aliases(meeting_content, patterns)
    if alias_result:
        # Return partial destination - caller will need to resolve list_id
        destination = {
            "folder_name": alias_result[0],
            "list_name": alias_result[1],
            "list_id": None  # Needs to be resolved by caller
        }
        return (destination, 0.75, "project_alias")

    return None


def save_learned_pattern(pattern_type: str, pattern_key: str, destination: Dict,
                        context: Dict, json_file_path: str = None):
    """
    Save a new learned pattern to the database.

    Args:
        pattern_type: Type of pattern ("title_patterns", "keyword_patterns", etc.)
        pattern_key: The pattern key (e.g., "chad drew rose standup")
        destination: Dict with folder_name, list_name, list_id
        context: Dict with meeting_title, date, context_text, notes
        json_file_path: Path to save the patterns JSON file (defaults to data/meeting_patterns_learned.json)
    """
    if json_file_path is None:
        json_file_path = DEFAULT_PATTERNS_FILE

    patterns = load_learned_patterns(json_file_path)

    # Ensure pattern_type exists
    if pattern_type not in patterns['patterns']:
        patterns['patterns'][pattern_type] = {}

    # Check if pattern already exists
    existing_pattern = patterns['patterns'][pattern_type].get(pattern_key)

    if existing_pattern:
        # Update existing pattern - add example and increase confidence
        if 'examples' not in existing_pattern:
            existing_pattern['examples'] = []

        existing_pattern['examples'].append({
            "meeting_title": context.get('meeting_title', ''),
            "date": context.get('date', datetime.now().strftime("%Y-%m-%d")),
            "context": context.get('context_text', '')
        })

        # Increase confidence slightly (cap at 0.98)
        current_confidence = existing_pattern.get('confidence', 0.85)
        existing_pattern['confidence'] = min(0.98, current_confidence + 0.02)

    else:
        # Create new pattern
        patterns['patterns'][pattern_type][pattern_key] = {
            "destination": destination,
            "confidence": 0.85,  # Start with medium-high confidence
            "learned_from": "manual_correction",
            "examples": [{
                "meeting_title": context.get('meeting_title', ''),
                "date": context.get('date', datetime.now().strftime("%Y-%m-%d")),
                "context": context.get('context_text', '')
            }],
            "notes": context.get('notes', '')
        }

        # Update statistics
        patterns['statistics']['total_patterns_learned'] += 1

    # Update last_updated
    patterns['last_updated'] = datetime.now().strftime("%Y-%m-%d")
    patterns['statistics']['corrections_applied'] += 1

    # Save to file
    with open(json_file_path, 'w') as f:
        json.dump(patterns, f, indent=2)


def update_pattern_statistics(pattern_applied: bool, json_file_path: str = None):
    """
    Update statistics when a pattern is applied.

    Args:
        pattern_applied: True if pattern was successfully applied
        json_file_path: Path to the patterns JSON file (defaults to data/meeting_patterns_learned.json)
    """
    if json_file_path is None:
        json_file_path = DEFAULT_PATTERNS_FILE

    patterns = load_learned_patterns(json_file_path)

    if pattern_applied:
        patterns['statistics']['successful_applications'] += 1

    # Calculate accuracy improvement
    total = patterns['statistics']['corrections_applied']
    successful = patterns['statistics']['successful_applications']

    if total > 0:
        accuracy = (successful / total) * 100
        patterns['statistics']['accuracy_improvement'] = f"{accuracy:.1f}%"

    # Update last_updated
    patterns['last_updated'] = datetime.now().strftime("%Y-%m-%d")

    # Save to file
    with open(json_file_path, 'w') as f:
        json.dump(patterns, f, indent=2)


def add_project_alias(alias: str, folder_name: str, list_name: str,
                     json_file_path: str = None):
    """
    Add a new project alias to the database.

    Args:
        alias: The alias text (e.g., "bitkey", "go puff")
        folder_name: The ClickUp folder name
        list_name: The ClickUp list name
        json_file_path: Path to the patterns JSON file (defaults to data/meeting_patterns_learned.json)
    """
    if json_file_path is None:
        json_file_path = DEFAULT_PATTERNS_FILE

    patterns = load_learned_patterns(json_file_path)

    # Normalize alias
    alias = normalize_text(alias)

    # Add to project_aliases
    patterns['patterns']['project_aliases'][alias] = [folder_name, list_name]

    # Update last_updated
    patterns['last_updated'] = datetime.now().strftime("%Y-%m-%d")

    # Save to file
    with open(json_file_path, 'w') as f:
        json.dump(patterns, f, indent=2)


if __name__ == '__main__':
    # Example usage
    patterns = load_learned_patterns()

    # Test with example meeting
    test_title = "Chad : Drew : Rose 15 min stand up"
    test_content = """
    Discussion about Bitkey deliverables.
    Need to complete overlay test by end of week.
    Packaging updates required.
    """

    result = apply_learned_patterns(test_title, test_content, patterns)

    if result:
        destination, confidence, source = result
        print(f"Match found via {source}:")
        print(f"  Destination: {destination['folder_name']} > {destination['list_name']}")
        print(f"  Confidence: {confidence * 100:.0f}%")
    else:
        print("No learned pattern match found")
