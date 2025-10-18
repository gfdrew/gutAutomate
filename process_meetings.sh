#!/bin/bash
# process_meetings.sh - Wrapper script for Claude Code to process meetings with approval
# This script is called BY Claude Code after getting user approval

# Usage:
#   MEETING_SELECTION="2" TASK_CONFIRMATION="y" ./process_meetings.sh

# Validate inputs
if [ -z "$MEETING_SELECTION" ]; then
    echo "Error: MEETING_SELECTION environment variable required"
    echo "Example: MEETING_SELECTION=\"2\" TASK_CONFIRMATION=\"y\" ./process_meetings.sh"
    exit 1
fi

if [ -z "$TASK_CONFIRMATION" ]; then
    echo "Error: TASK_CONFIRMATION environment variable required"
    echo "Example: MEETING_SELECTION=\"2\" TASK_CONFIRMATION=\"y\" ./process_meetings.sh"
    exit 1
fi

# Run gutAutomate in claude mode
echo "Running gutAutomate.py with:"
echo "  MEETING_SELECTION=$MEETING_SELECTION"
echo "  TASK_CONFIRMATION=$TASK_CONFIRMATION"
echo ""

python3 gutAutomate.py claude
