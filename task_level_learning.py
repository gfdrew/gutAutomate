#!/usr/bin/env python3
"""
task_level_learning.py - Task-Level Pattern Matching for Learning System

This module provides functions to match individual tasks against learned patterns,
allowing multi-project meetings to have tasks distributed to different destinations.
"""

import json
import os
import re
from typing import Dict, List, Optional, Tuple
from meeting_learning import load_learned_patterns, normalize_text


def detect_task_destination(task_text: str, task_context: str = "",
                           meeting_context: str = "") -> Optional[Tuple[Dict, float, str]]:
    """
    Detect destination for a single task using task-level learned patterns.

    This analyzes the individual task text (not the whole meeting) to determine
    which project it belongs to. Supports multi-project meetings.

    Args:
        task_text: The task description text
        task_context: Additional context about the task (assignee, related items, etc.)
        meeting_context: Overall meeting context (used as weak signal only)

    Returns:
        Tuple of (destination, confidence, source) if match found, None otherwise
        destination: Dict with folder_name, list_name, list_id
        confidence: Float between 0 and 1
        source: String describing which pattern matched
    """
    patterns = load_learned_patterns()
    task_level = patterns.get('patterns', {}).get('task_level', {})

    # Normalize text for matching
    normalized_task = normalize_text(task_text)
    normalized_context = normalize_text(task_context)
    combined_text = f"{normalized_task} {normalized_context}"

    # Priority 1: Check project aliases (strongest signal - explicit mentions)
    result = check_project_aliases_in_task(combined_text, task_level)
    if result:
        return result

    # Priority 2: Check keyword patterns (strong signals)
    result = check_keyword_patterns_in_task(combined_text, normalized_task, task_level)
    if result:
        return result

    # Priority 3: Check person patterns (medium signal)
    result = check_person_patterns_in_task(combined_text, task_level)
    if result:
        return result

    # No task-level match found
    return None


def check_project_aliases_in_task(task_text: str, task_level: Dict) -> Optional[Tuple[Dict, float, str]]:
    """
    Check if task mentions any project aliases explicitly.
    These are the strongest signals (e.g., "Update Bitkey deliverables").
    """
    project_aliases = task_level.get('project_aliases', {})

    # Track best match
    best_match = None
    best_confidence = 0.0

    for alias, pattern_data in project_aliases.items():
        if alias in task_text:
            confidence = pattern_data.get('confidence', 0.95)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = (
                    pattern_data['destination'],
                    confidence,
                    f"project_alias ({alias})"
                )

    return best_match


def check_keyword_patterns_in_task(combined_text: str, task_text: str,
                                   task_level: Dict) -> Optional[Tuple[Dict, float, str]]:
    """
    Check if task contains learned keyword patterns.
    These are strong signals (e.g., "overlay test" → Bitkey).
    """
    keyword_patterns = task_level.get('keyword_patterns', {})

    # Track best match
    best_match = None
    best_confidence = 0.0

    for keyword, pattern_data in keyword_patterns.items():
        # Check if keyword is in task
        if keyword in task_text or keyword in combined_text:
            # Check if context is required
            context_required = pattern_data.get('context_required', [])

            if context_required:
                # Must have at least one required context word
                has_context = any(ctx in combined_text for ctx in context_required)
                if not has_context:
                    continue  # Skip this pattern

            confidence = pattern_data.get('confidence', 0.85)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = (
                    pattern_data['destination'],
                    confidence,
                    f"keyword_pattern ({keyword})"
                )

    return best_match


def check_person_patterns_in_task(task_text: str, task_level: Dict) -> Optional[Tuple[Dict, float, str]]:
    """
    Check if task mentions people who are associated with specific projects.
    These are medium-strength signals.
    """
    person_patterns = task_level.get('person_patterns', {})

    for person_name, pattern_data in person_patterns.items():
        if person_name in task_text:
            # Person patterns return likely projects with probabilities
            likely_projects = pattern_data.get('likely_projects', [])

            if likely_projects:
                # Return the highest probability project
                best_project = max(likely_projects, key=lambda p: p.get('probability', 0))

                # Create destination dict
                destination = {
                    'folder_name': best_project['folder_name'],
                    'list_name': best_project['list_name'],
                    'list_id': best_project['list_id']
                }

                confidence = pattern_data.get('confidence', 0.65)
                return (destination, confidence, f"person_pattern ({person_name})")

    return None


def get_meeting_level_suggestions(meeting_title: str, meeting_content: str) -> List[Dict]:
    """
    Get weak suggestions from meeting-level patterns.
    These are NOT used for hard assignment, only as hints/defaults.

    Returns:
        List of likely projects with probabilities, sorted by probability
    """
    patterns = load_learned_patterns()
    meeting_level = patterns.get('patterns', {}).get('meeting_level', {})

    normalized_title = normalize_text(meeting_title)
    title_patterns = meeting_level.get('title_patterns', {})

    # Check title patterns
    for pattern_key, pattern_data in title_patterns.items():
        pattern_words = set(pattern_key.split())
        title_words = set(normalized_title.split())

        # Flexible matching - check if most pattern words are in title
        if pattern_words:
            matched_words = pattern_words.intersection(title_words)
            match_ratio = len(matched_words) / len(pattern_words)

            if match_ratio >= 0.7:  # 70% of words match
                return pattern_data.get('likely_projects', [])

    # No meeting-level match
    return []


def analyze_tasks_with_learning(action_items: List[Dict], meeting_title: str,
                                meeting_content: str) -> List[Dict]:
    """
    Analyze each task individually and suggest destinations based on learned patterns.

    Args:
        action_items: List of parsed action items from meeting
        meeting_title: Title of the meeting
        meeting_content: Full meeting content

    Returns:
        List of action items with added 'learned_destination' field containing
        detected destination and confidence
    """
    # Get meeting-level suggestions (weak signals)
    meeting_suggestions = get_meeting_level_suggestions(meeting_title, meeting_content)
    default_suggestion = meeting_suggestions[0] if meeting_suggestions else None

    # Analyze each task individually
    enriched_items = []

    for item in action_items:
        task_text = item.get('task', '')
        assignee = item.get('assignee', '')

        # Build task context
        task_context = f"{assignee}"

        # Detect destination for this specific task
        result = detect_task_destination(task_text, task_context, meeting_content)

        # Add learned destination to item
        enriched_item = item.copy()

        if result:
            destination, confidence, source = result
            enriched_item['learned_destination'] = {
                'folder_name': destination['folder_name'],
                'list_name': destination['list_name'],
                'list_id': destination['list_id'],
                'confidence': confidence,
                'source': source,
                'signal_strength': 'strong' if confidence >= 0.85 else 'medium'
            }
        elif default_suggestion:
            # Use meeting-level suggestion as weak fallback
            enriched_item['learned_destination'] = {
                'folder_name': default_suggestion['folder_name'],
                'list_name': default_suggestion['list_name'],
                'list_id': default_suggestion['list_id'],
                'confidence': 0.5,  # Weak signal
                'source': 'meeting_level_fallback',
                'signal_strength': 'weak'
            }
        else:
            enriched_item['learned_destination'] = None

        enriched_items.append(enriched_item)

    return enriched_items


if __name__ == '__main__':
    # Test with example tasks
    test_tasks = [
        {
            'task': 'Complete overlay test for packaging',
            'assignee': 'Drew Gilbert'
        },
        {
            'task': 'Send production brief around for review',
            'assignee': 'Art Okoro'
        },
        {
            'task': 'Update BevMo creative concepts',
            'assignee': 'Drew Gilbert'
        },
        {
            'task': 'Review Gopuff NYE campaign timeline',
            'assignee': 'Rose'
        }
    ]

    print("Testing task-level pattern matching:")
    print("=" * 70)

    for i, task in enumerate(test_tasks, 1):
        print(f"\nTask {i}: {task['task']}")
        print(f"Assignee: {task['assignee']}")

        result = detect_task_destination(task['task'], task['assignee'])

        if result:
            dest, confidence, source = result
            print(f"✓ Match found via {source}")
            print(f"  → {dest['folder_name']} > {dest['list_name']}")
            print(f"  Confidence: {confidence:.0%}")
        else:
            print("✗ No learned pattern match")
