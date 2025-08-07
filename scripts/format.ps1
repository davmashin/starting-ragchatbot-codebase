# Format code script for Windows PowerShell
# Automatically fix formatting and import order

Write-Host "🎨 Formatting code..." -ForegroundColor Cyan
Write-Host ""

# Sort imports
Write-Host "📦 Sorting imports with isort..." -ForegroundColor Yellow
& uv run isort backend/
Write-Host ""

# Format code with black
Write-Host "🎨 Formatting code with black..." -ForegroundColor Yellow
& uv run black backend/
Write-Host ""

Write-Host "✅ Code formatting complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Run './scripts/quality.ps1' to verify all quality checks pass." -ForegroundColor Cyan