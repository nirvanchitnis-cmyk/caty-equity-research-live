#!/bin/bash
#
# AUTO-HASH PRIMARY SOURCE ARCHIVAL SCRIPT
# Per Derek's governance requirement (Cross-Exam Q10)
#
# Usage: ./scripts/archive_primary_source.sh <source_file> <source_url> <description>
#
# Example:
#   ./scripts/archive_primary_source.sh \
#     ~/Downloads/CATY_Q3_2025_10Q.htm \
#     "https://www.sec.gov/Archives/edgar/data/861842/0001437749-25-034567/caty20250930_10q.htm" \
#     "Q3 2025 10-Q filing"

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Validate arguments
if [ "$#" -lt 3 ]; then
    echo -e "${RED}ERROR: Insufficient arguments${NC}"
    echo ""
    echo "Usage: $0 <source_file> <source_url> <description>"
    echo ""
    echo "Arguments:"
    echo "  source_file   : Path to the file to archive"
    echo "  source_url    : URL where the file was obtained"
    echo "  description   : Brief description of the document"
    echo ""
    echo "Example:"
    echo "  $0 ~/Downloads/2025-Q3_10Q.pdf 'https://www.sec.gov/...' 'Q3 2025 10-Q filing'"
    exit 1
fi

SOURCE_FILE="$1"
SOURCE_URL="$2"
DESCRIPTION="$3"

# Check if source file exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo -e "${RED}ERROR: Source file does not exist: $SOURCE_FILE${NC}"
    exit 1
fi

# Set up paths
EVIDENCE_DIR="evidence/primary_sources"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S %Z")
DATE_SHORT=$(date +"%Y%m%d")
FILENAME=$(basename "$SOURCE_FILE")
DEST_FILE="$EVIDENCE_DIR/$FILENAME"

# Create evidence directory if it doesn't exist
mkdir -p "$EVIDENCE_DIR"

# Copy file to evidence folder
echo -e "${BLUE}📄 Copying file to evidence folder...${NC}"
cp "$SOURCE_FILE" "$DEST_FILE"

# Generate SHA256 hash
echo -e "${BLUE}🔐 Generating SHA256 hash...${NC}"
HASH=$(shasum -a 256 "$DEST_FILE" | awk '{print $1}')

# Get file size
FILESIZE=$(ls -lh "$DEST_FILE" | awk '{print $5}')

# Log to evidence README
echo -e "${BLUE}📝 Updating evidence/README.md...${NC}"

# Check if primary sources section exists
if ! grep -q "### .*$FILENAME" evidence/README.md 2>/dev/null; then
    # Find the line number for "## FILE INVENTORY" and insert after
    INVENTORY_LINE=$(grep -n "## FILE INVENTORY" evidence/README.md | head -1 | cut -d: -f1)

    # Create temp file with new entry
    {
        head -n "$((INVENTORY_LINE + 1))" evidence/README.md
        echo ""
        echo "### primary_sources/$FILENAME"
        echo "**Purpose:** $DESCRIPTION"
        echo "**Status:** ✅ ARCHIVED"
        echo "**File Size:** $FILESIZE"
        echo "**SHA256:** \`$HASH\`"
        echo "**Download Date:** $TIMESTAMP"
        echo "**Source URL:** $SOURCE_URL"
        echo "**Archived By:** Auto-hash script (archive_primary_source.sh)"
        tail -n "+$((INVENTORY_LINE + 2))" evidence/README.md
    } > evidence/README.md.tmp

    mv evidence/README.md.tmp evidence/README.md
fi

# Update document control log
echo -e "${BLUE}📊 Updating document control log...${NC}"

# Find the document control log table and append new row
if grep -q "## DOCUMENT CONTROL LOG" evidence/README.md; then
    # Create temp file with new log entry
    awk -v date="$DATE_SHORT" -v time="$(date +%H:%M)" -v desc="$DESCRIPTION" -v file="$FILENAME" -v hash="$HASH" '
    /\| 2025-/ && !done {
        print $0
        printf "| %s | %s | Primary source archived | %s | SHA256: %s | ✅ ARCHIVED |\n", date, time, file, substr(hash, 1, 16) "..."
        done = 1
        next
    }
    { print }
    ' evidence/README.md > evidence/README.md.tmp

    mv evidence/README.md.tmp evidence/README.md
fi

# Output summary
echo ""
echo -e "${GREEN}✅ PRIMARY SOURCE ARCHIVED SUCCESSFULLY${NC}"
echo ""
echo -e "${YELLOW}File Details:${NC}"
echo "  Original:   $SOURCE_FILE"
echo "  Archived:   $DEST_FILE"
echo "  Size:       $FILESIZE"
echo "  SHA256:     $HASH"
echo ""
echo -e "${YELLOW}Metadata:${NC}"
echo "  Timestamp:  $TIMESTAMP"
echo "  Source URL: $SOURCE_URL"
echo "  Description: $DESCRIPTION"
echo ""
echo -e "${YELLOW}Documentation Updated:${NC}"
echo "  ✅ evidence/README.md (FILE INVENTORY section)"
echo "  ✅ evidence/README.md (DOCUMENT CONTROL LOG table)"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Review evidence/README.md to verify entry"
echo "  2. Git commit with message: 'Archive primary source: $FILENAME'"
echo "  3. Push to remote repository"
echo ""
echo -e "${GREEN}Hash verification command:${NC}"
echo "  shasum -a 256 $DEST_FILE"
echo ""
