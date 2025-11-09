$path = 'auto_srt_all.py' 
$s = Get-Content $path -Raw -Encoding UTF8 $insert = @' 
import sys try: # Ensure stdout can emit UTF-8 (prevents UnicodeEncodeError on Windows consoles) sys.stdout.reconfigure(encoding="utf-8", errors="replace") except Exception: # Older Pythons or weird environments may not support reconfigure; ignore pass
'@ 
if ($s -notmatch 'sys.stdout.reconfigure') { Set-Content -Path $path -Value ($insert + $s) -Encoding UTF8 Write-Host 'patched: auto_srt_all.py' } else { Write-Host 'already patched: auto_srt_all.py' }