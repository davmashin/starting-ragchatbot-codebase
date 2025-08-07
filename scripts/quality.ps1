# Quality check script for Windows PowerShell
# Run all code quality tools and report results

Write-Host "🔍 Running code quality checks..." -ForegroundColor Cyan
Write-Host ""

# Track overall success
$overallSuccess = $true

# Function to run a command and report results
function Invoke-QualityCheck {
    param(
        [string]$Name,
        [string]$Command,
        [string]$Emoji
    )
    
    Write-Host "$Emoji Running $Name..." -ForegroundColor Yellow
    $result = Invoke-Expression $Command
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $Name passed" -ForegroundColor Green
    } else {
        Write-Host "❌ $Name failed" -ForegroundColor Red
        $script:overallSuccess = $false
    }
    Write-Host ""
}

# Format code first
Write-Host "🎨 Checking code formatting..." -ForegroundColor Yellow
& uv run isort backend/ --diff --check-only
if ($LASTEXITCODE -ne 0) { Write-Host "⚠️  Import order needs fixing" -ForegroundColor Yellow }

& uv run black backend/ --check
if ($LASTEXITCODE -ne 0) { Write-Host "⚠️  Code formatting needs fixing" -ForegroundColor Yellow }
Write-Host ""

# Run quality checks
Invoke-QualityCheck "Black formatting" "uv run black backend/ --check --diff" "🎨"
Invoke-QualityCheck "Import sorting (isort)" "uv run isort backend/ --diff --check-only" "📦"
Invoke-QualityCheck "Flake8 linting" "uv run flake8 backend/ --max-line-length=88 --extend-ignore=E203,W503" "🔍"
Invoke-QualityCheck "Type checking (mypy)" "uv run mypy backend/" "🏷️"
Invoke-QualityCheck "Tests" "uv run pytest backend/tests/ -v" "🧪"

# Summary
Write-Host "=" * 50 -ForegroundColor White
if ($overallSuccess) {
    Write-Host "🎉 All quality checks passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "💥 Some quality checks failed" -ForegroundColor Red
    exit 1
}