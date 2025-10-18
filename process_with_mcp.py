#!/usr/bin/env python3
"""
process_with_mcp.py - Parse gutAutomate JSON output and create tasks via Claude Code MCP

This script is meant to be called BY Claude Code, not run directly.
It runs gutAutomate.py in claude mode, parses the JSON output, and returns
the task data for Claude Code to create via MCP tools.
"""

import sys
import json
import subprocess
import os
import re


def run_gutAutomate_and_get_json(meeting_selection, task_confirmation):
    """
    Run gutAutomate.py in claude mode and extract the JSON output.

    Args:
        meeting_selection: Which meetings to process (e.g., "1" or "1,2" or "all")
        task_confirmation: Whether to create tasks ("y" or "n")

    Returns:
        dict: Parsed JSON output from gutAutomate
    """
    # Set environment variables
    env = os.environ.copy()
    env['MEETING_SELECTION'] = str(meeting_selection)
    env['TASK_CONFIRMATION'] = str(task_confirmation)

    # Run gutAutomate.py in claude mode
    result = subprocess.run(
        ['python3', 'gutAutomate.py', 'claude'],
        env=env,
        capture_output=True,
        text=True,
        timeout=120
    )

    # Extract JSON from output
    output = result.stdout

    # Find JSON between markers
    json_match = re.search(
        r'JSON_OUTPUT_START\n(.*?)\nJSON_OUTPUT_END',
        output,
        re.DOTALL
    )

    if not json_match:
        print("ERROR: No JSON output found in gutAutomate output")
        print("Output was:")
        print(output)
        return None

    json_text = json_match.group(1)

    try:
        data = json.loads(json_text)
        return data
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON: {e}")
        print(f"JSON text was: {json_text}")
        return None


def main():
    """
    Main entry point - this is called by Claude Code
    """
    if len(sys.argv) < 3:
        print("Usage: python3 process_with_mcp.py <meeting_selection> <task_confirmation>")
        print("Example: python3 process_with_mcp.py '2' 'y'")
        sys.exit(1)

    meeting_selection = sys.argv[1]
    task_confirmation = sys.argv[2]

    print(f"Running gutAutomate with:")
    print(f"  Meeting Selection: {meeting_selection}")
    print(f"  Task Confirmation: {task_confirmation}")
    print()

    # Run gutAutomate and get JSON
    data = run_gutAutomate_and_get_json(meeting_selection, task_confirmation)

    if not data:
        print("ERROR: Failed to get data from gutAutomate")
        sys.exit(1)

    # Output the data for Claude Code to parse
    print("\n" + "=" * 80)
    print("PARSED DATA FOR CLAUDE CODE")
    print("=" * 80)
    print(json.dumps(data, indent=2))
    print("=" * 80)

    return data


if __name__ == '__main__':
    main()
