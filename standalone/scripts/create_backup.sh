#!/bin/bash
# Backup Script for gutAutomate
# Creates a git tag with timestamp and optional description

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current date for tag
DATE=$(date +%Y%m%d-%H%M%S)

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Prompt for backup type
echo -e "${BLUE}=== gutAutomate Backup Creator ===${NC}"
echo ""
echo "What type of backup?"
echo "1) Working feature backup (creates tag: working/YYYYMMDD-HHMMSS)"
echo "2) Stable release backup (creates tag: stable/YYYYMMDD-HHMMSS)"
echo "3) Custom tag name"
echo ""
read -p "Select option (1-3): " BACKUP_TYPE

case $BACKUP_TYPE in
    1)
        TAG_PREFIX="working"
        ;;
    2)
        TAG_PREFIX="stable"
        ;;
    3)
        read -p "Enter custom tag prefix: " TAG_PREFIX
        ;;
    *)
        echo -e "${YELLOW}Invalid option. Using 'working' as default.${NC}"
        TAG_PREFIX="working"
        ;;
esac

# Prompt for description
read -p "Enter backup description (optional): " DESCRIPTION

# Create tag name
TAG_NAME="${TAG_PREFIX}/${DATE}"

# Create the tag
if [ -z "$DESCRIPTION" ]; then
    git tag -a "$TAG_NAME" -m "Backup created on $DATE from branch $BRANCH"
else
    git tag -a "$TAG_NAME" -m "$DESCRIPTION"
fi

echo ""
echo -e "${GREEN}✓ Backup created successfully!${NC}"
echo -e "  Tag: ${BLUE}$TAG_NAME${NC}"
echo -e "  Branch: ${BLUE}$BRANCH${NC}"
echo -e "  Commit: ${BLUE}$(git rev-parse --short HEAD)${NC}"
echo ""
echo "To restore this backup later:"
echo -e "  ${YELLOW}git checkout $TAG_NAME${NC}"
echo ""
echo "To push this backup to GitHub:"
echo -e "  ${YELLOW}git push origin $TAG_NAME${NC}"
echo ""
echo "To list all backups:"
echo -e "  ${YELLOW}git tag -l 'working/*' 'stable/*'${NC}"
echo ""
