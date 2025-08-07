#!/bin/bash

# Quality check script for the RAG chatbot project
# Run all code quality tools and report results

echo "🔍 Running code quality checks..."
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall success
overall_success=true

# Function to run a command and report results
run_check() {
    local name="$1"
    local command="$2"
    local emoji="$3"
    
    echo -e "${emoji} Running $name..."
    if eval "$command"; then
        echo -e "${GREEN}✅ $name passed${NC}"
    else
        echo -e "${RED}❌ $name failed${NC}"
        overall_success=false
    fi
    echo
}

# Format code first
echo -e "${YELLOW}🎨 Formatting code...${NC}"
uv run isort backend/ --diff --check-only || echo -e "${YELLOW}⚠️  Import order needs fixing${NC}"
uv run black backend/ --check || echo -e "${YELLOW}⚠️  Code formatting needs fixing${NC}"
echo

# Run quality checks
run_check "Black formatting" "uv run black backend/ --check --diff" "🎨"
run_check "Import sorting (isort)" "uv run isort backend/ --diff --check-only" "📦"
run_check "Flake8 linting" "uv run flake8 backend/ --max-line-length=88 --extend-ignore=E203,W503" "🔍"
run_check "Type checking (mypy)" "uv run mypy backend/" "🏷️"
run_check "Tests" "uv run pytest backend/tests/ -v" "🧪"

# Summary
echo "=" * 50
if [ "$overall_success" = true ]; then
    echo -e "${GREEN}🎉 All quality checks passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some quality checks failed${NC}"
    exit 1
fi