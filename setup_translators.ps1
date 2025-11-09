# =====================================================================
# TRANSLATION ENGINES - QUICK RUNNER
# =====================================================================
# Copy-paste this entire script into PowerShell and run it!
# It will check your setup and tell you exactly what to do next.
# =====================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TRANSLATION ENGINES - QUICK CHECK" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Where are we?
$currentPath = Get-Location
Write-Host "Current directory: $currentPath" -ForegroundColor Yellow

# Check for Python
Write-Host "`nChecking Python..." -NoNewline
try {
    $pyVer = python --version 2>&1
    Write-Host " ✓ $pyVer" -ForegroundColor Green
} catch {
    Write-Host " ✗ NOT FOUND" -ForegroundColor Red
    Write-Host "Install Python first: https://python.org" -ForegroundColor Yellow
    exit 1
}

# Check for venv
Write-Host "Checking virtual environment..." -NoNewline
if ($env:VIRTUAL_ENV) {
    Write-Host " ✓ Active" -ForegroundColor Green
} else {
    Write-Host " ⚠ Not active" -ForegroundColor Yellow
    Write-Host "  Activate it: .\.venv\Scripts\Activate.ps1" -ForegroundColor Gray
}

# Check for OpenAI
Write-Host "Checking openai package..." -NoNewline
try {
    $null = python -c "import openai" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓ Installed" -ForegroundColor Green
    } else {
        Write-Host " ✗ Not installed" -ForegroundColor Red
        Write-Host "  Install: pip install openai" -ForegroundColor Gray
    }
} catch {
    Write-Host " ✗ Not installed" -ForegroundColor Red
    Write-Host "  Install: pip install openai" -ForegroundColor Gray
}

# Check for translator files
Write-Host "`nSearching for translator files..." -ForegroundColor Yellow

$files = Get-ChildItem -Path . -Filter "*translate*.py" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 10

if ($files) {
    Write-Host "  Found:" -ForegroundColor Green
    foreach ($file in $files) {
        Write-Host "    $($file.FullName)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✗ No translator files found!" -ForegroundColor Red
}

# Specific check
$subtitleFile = "src\downloadbeast\subtitle_translate_ultra.py"
$subtitleRoot = "subtitle_translate_ultra.py"

Write-Host "`nLooking for specific files..." -ForegroundColor Yellow

if (Test-Path $subtitleFile) {
    Write-Host "  ✓ Found: $subtitleFile" -ForegroundColor Green
    $foundSubtitle = $subtitleFile
} elseif (Test-Path $subtitleRoot) {
    Write-Host "  ✓ Found: $subtitleRoot" -ForegroundColor Green
    $foundSubtitle = $subtitleRoot
} else {
    Write-Host "  ✗ subtitle_translate_ultra.py NOT FOUND" -ForegroundColor Red
    $foundSubtitle = $null
}

# Check API key
Write-Host "`nChecking API key..." -NoNewline
if ($env:OPENAI_API_KEY) {
    $keyPreview = $env:OPENAI_API_KEY.Substring(0, [Math]::Min(10, $env:OPENAI_API_KEY.Length))
    Write-Host " ✓ Set ($keyPreview...)" -ForegroundColor Green
} else {
    Write-Host " ✗ Not set" -ForegroundColor Red
    Write-Host "  Set it: `$env:OPENAI_API_KEY = 'sk-your-key'" -ForegroundColor Gray
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "WHAT TO DO NEXT:" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($foundSubtitle) {
    Write-Host "✓ Files found! Test them:" -ForegroundColor Green
    Write-Host "  python $foundSubtitle" -ForegroundColor Cyan
} else {
    Write-Host "✗ Files NOT found. You need to:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Find these files in the chat:" -ForegroundColor White
    Write-Host "     - subtitle_translate_ultra.py" -ForegroundColor Gray
    Write-Host "     - dialect_translate_ultra2.py" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Copy the code" -ForegroundColor White
    Write-Host ""
    Write-Host "  3. Save to one of these locations:" -ForegroundColor White
    Write-Host "     Option A: $currentPath\subtitle_translate_ultra.py" -ForegroundColor Cyan
    Write-Host "     Option B: $currentPath\src\downloadbeast\subtitle_translate_ultra.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  4. Run this script again" -ForegroundColor White
}

Write-Host "`nDirectory structure should be:" -ForegroundColor Yellow
Write-Host "  C:\Build\Beast\" -ForegroundColor Gray
Write-Host "    ├── .venv\" -ForegroundColor Gray
Write-Host "    ├── src\" -ForegroundColor Gray  
Write-Host "    │   └── downloadbeast\" -ForegroundColor Gray
Write-Host "    │       ├── subtitle_translate_ultra.py  ← Put here" -ForegroundColor Cyan
Write-Host "    │       └── dialect_translate_ultra2.py  ← Or here" -ForegroundColor Cyan
Write-Host "    └── (or put files in root)" -ForegroundColor Gray

Write-Host "`n========================================`n" -ForegroundColor Cyan
