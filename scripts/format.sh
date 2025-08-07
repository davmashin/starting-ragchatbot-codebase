#!/bin/bash

# Format code script for the RAG chatbot project
# Automatically fix formatting and import order

echo "🎨 Formatting code..."
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Sort imports
echo -e "${YELLOW}📦 Sorting imports with isort...${NC}"
uv run isort backend/
echo

# Format code with black
echo -e "${YELLOW}🎨 Formatting code with black...${NC}"
uv run black backend/
echo

echo -e "${GREEN}✅ Code formatting complete!${NC}"
echo
echo "Run './scripts/quality.sh' to verify all quality checks pass."