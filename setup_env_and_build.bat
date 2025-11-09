# PowerShell setup script: no bashisms, no here-doc for CMD
$ErrorActionPreference = 'Stop'

$PROJ  = 'C:\Build\Beast'
$VENV  = Join-Path $PROJ 'venv'
$PY    = 'py'
$PYEXE = Join-Path $VENV 'Scripts\python.exe'
$PIP   = Join-Path $VENV 'Scripts\pip.exe'

Write-Host "`n[1/5] Creating venv at $VENV ..."
if (Test-Path $VENV) {
  Write-Host "   venv already exists."
} else {
  & $PY -m venv $VENV
}

Write-Host "`n[2/5] Upgrading pip/setuptools/wheel..."
& $PYEXE -m pip install -U pip setuptools wheel

Write-Host "`n[3/5] Installing runtime deps..."
& $PIP install -U `
  yt-dlp `
  PySimpleGUI `
  pyperclip `
  pyinstaller `
  faster-whisper `
  deep-translator

Write-Host "`n[4/5] Verifying imports..."
$code = @"
import sys
mods = [
  "yt_dlp","PySimpleGUI","pyperclip","faster_whisper",
  "deep_translator","onnxruntime","numpy","requests"
]
bad=[]
for m in mods:
    try:
        __import__(m)
        print("OK  ", m)
    except Exception as e:
        print("FAIL", m, "-", e)
        bad.append(m)
if bad:
    sys.exit(2)
else:
    print("All imports OK")
"@
& $PYEXE - <<<$code

Write-Host "`n[5/5] (Optional) Building GUI exe with PyInstaller..."
$gui = Join-Path $PROJ 'DownloadBeast_GUI.py'
if (Test-Path $gui) {
  & $PYEXE -m PyInstaller -F -w -n DownloadBeast_Pro `
     --add-data "C:\Build\Beast\auto_srt_all.py;." `
     --paths $PROJ `
     $gui
  Write-Host "   Build output (if succeeded): $PROJ\dist\DownloadBeast_Pro.exe"
} else {
  Write-Host "   GUI not found at $gui - skipping."
}

Write-Host "`nDone."
