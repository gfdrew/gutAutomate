#!/bin/bash
# List all backups created with create_backup.sh

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== gutAutomate Backups ===${NC}"
echo ""

# List working backups
echo -e "${GREEN}Working Feature Backups:${NC}"
git tag -l 'working/*' --format='%(refname:short) - %(contents:subject)' | sed 's/^/  /'
echo ""

# List stable backups
echo -e "${GREEN}Stable Release Backups:${NC}"
git tag -l 'stable/*' --format='%(refname:short) - %(contents:subject)' | sed 's/^/  /'
echo ""

# Show current branch and commit
echo -e "${YELLOW}Current State:${NC}"
echo -e "  Branch: $(git rev-parse --abbrev-ref HEAD)"
echo -e "  Commit: $(git rev-parse --short HEAD)"
echo ""
