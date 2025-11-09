# Setup Instructions for DownloadBeast

## Where Are Your Files?

Based on your error, the subtitle translator isn't in `C:\Build\Beast` yet. You need to:

1. **Download the files from this chat** (they're in the outputs)
2. **Place them in your project directory**

## Quick Setup

### Option 1: Download from Chat (Recommended)

The files are available for download in this conversation. Save them to your project:

```powershell
# Navigate to your project
cd C:\Build\Beast

# Create src directory if it doesn't exist (for organized structure)
mkdir -Force src\downloadbeast

# Download/save these files to C:\Build\Beast\src\downloadbeast\:
# - dialect_translate_ultra2.py
# - subtitle_translate_ultra.py
# - tech_terms_example.csv (rename to tech_terms.csv)
```

### Option 2: Place in Root Directory

Alternatively, save directly to `C:\Build\Beast\`:

```powershell
cd C:\Build\Beast

# Save these files here:
# - subtitle_translate_ultra.py
# - dialect_translate_ultra2.py
# - tech_terms.csv
```

## After Downloading Files

### Test the Subtitle Translator

```powershell
# If files are in root:
cd C:\Build\Beast
.\.venv\Scripts\Activate.ps1
python subtitle_translate_ultra.py

# If files are in src\downloadbeast:
cd C:\Build\Beast
.\.venv\Scripts\Activate.ps1
python src\downloadbeast\subtitle_translate_ultra.py
```

Expected output:
```
======================================================================
SUBTITLE TRANSLATOR ULTRA - Test Suite
======================================================================

📝 Translating test subtitles...

✅ Translation complete!
...
✅ All tests passed!
```

### Test the Dialect Translator

```powershell
# Depending on where you saved it:
python dialect_translate_ultra2.py
# or
python src\downloadbeast\dialect_translate_ultra2.py
```

## Recommended Directory Structure

```
C:\Build\Beast\
├── .venv\                          # Your virtual environment
├── src\
│   └── downloadbeast\
│       ├── __init__.py             # Make it a package (can be empty)
│       ├── subtitle_translate_ultra.py
│       ├── dialect_translate_ultra2.py
│       └── config\
│           └── tech_terms.csv
├── scripts\                        # Your PowerShell scripts
│   ├── download_video.ps1
│   ├── translate_subtitles.ps1    # New!
│   └── ...
├── videos\                         # Output directory
└── README.md
```

## Install Dependencies

```powershell
.\.venv\Scripts\Activate.ps1

# For subtitle translation
pip install openai

# Optional: other providers
pip install anthropic  # For Claude
pip install deepl      # For DeepL
```

## Set API Key

```powershell
# Set for current session
$env:OPENAI_API_KEY = "sk-your-key-here"

# Or set permanently (User level)
[Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-your-key-here', 'User')

# Or create a .env file
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

## Create PowerShell Wrapper (Optional)

Create `scripts\translate_subtitles.ps1`:

```powershell
# scripts\translate_subtitles.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$InputSrt,
    
    [Parameter(Mandatory=$true)]
    [string]$TargetLang,
    
    [string]$Context = "Video translation"
)

$ErrorActionPreference = "Stop"

# Check if file exists
if (-not (Test-Path $InputSrt)) {
    Write-Error "Input file not found: $InputSrt"
    exit 1
}

# Generate output filename
$dir = Split-Path $InputSrt
$basename = (Get-Item $InputSrt).BaseName -replace '_en$', ''
$OutputSrt = Join-Path $dir "${basename}_${TargetLang}.srt"

Write-Host "Translating to $TargetLang..." -ForegroundColor Cyan

# Call Python (adjust path to where you saved the file)
$pythonScript = Join-Path $PSScriptRoot "..\src\downloadbeast\subtitle_translate_ultra.py"

python -c @"
import sys
sys.path.insert(0, r'$PSScriptRoot\..\src\downloadbeast')

from subtitle_translate_ultra import SubtitleTranslator, TranslationProvider

try:
    tx = SubtitleTranslator(
        provider=TranslationProvider.OPENAI,
        batch_size=20
    )
    
    stats = tx.translate_file(
        r'$InputSrt',
        r'$OutputSrt',
        'en',
        '$TargetLang',
        r'$Context'
    )
    
    print(f'✓ Translated {stats[\"translations\"]} entries')
    print(f'✓ Output: $OutputSrt')
    sys.exit(0)
    
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
"@

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Done!" -ForegroundColor Green
} else {
    Write-Error "Translation failed"
    exit 1
}
```

Usage:
```powershell
.\scripts\translate_subtitles.ps1 -InputSrt "videos\video_en.srt" -TargetLang "ja"
```

## Quick Test Without Installing

If you want to test immediately without organizing files:

```powershell
cd C:\Build\Beast

# Save subtitle_translate_ultra.py to current directory
# Then:

.\.venv\Scripts\Activate.ps1
python subtitle_translate_ultra.py
```

## Verify Everything Works

```powershell
# 1. Check Python
python --version
# Should show: Python 3.11.x or similar

# 2. Check virtual environment is active
where python
# Should show: C:\Build\Beast\.venv\Scripts\python.exe

# 3. Check OpenAI installed
pip show openai
# Should show version info

# 4. Check API key set
echo $env:OPENAI_API_KEY
# Should show: sk-...

# 5. Test the translator
python subtitle_translate_ultra.py
# Should show: ✅ All tests passed!
```

## Next Steps

1. ✅ Download the Python files from this chat
2. 📁 Place them in your project (choose structure above)
3. 🔧 Install dependencies (`pip install openai`)
4. 🔑 Set your API key
5. 🧪 Run the test: `python subtitle_translate_ultra.py`
6. 🎬 Start translating your videos!

## Troubleshooting

### "python: can't open file"
→ File not in current directory. Check path:
```powershell
Get-ChildItem -Recurse -Filter "subtitle_translate_ultra.py"
```

### "Module 'openai' not found"
→ Install in venv:
```powershell
.\.venv\Scripts\Activate.ps1
pip install openai
```

### "API key not set"
→ Set environment variable:
```powershell
$env:OPENAI_API_KEY = "your-key"
```

Need help? Check the file locations first!
