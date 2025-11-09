# temp_repair_auto_srt.ps1 — safe in-place repair (creates a backup)
$path = 'auto_srt_all.py'
# make a backup first
Copy-Item $path ($path + '.bak_after_corruption') -ErrorAction SilentlyContinue -Force

# read file
$s = Get-Content $path -Raw -Encoding UTF8

# Remove obvious PowerShell lines accidentally inserted at top that start with $ or contain "Get-Content" etc.
# This will remove any leading lines up to the first occurrence of the coding header or a Python import line.
# Find the index of first Python marker we expect (either "# -*- coding: utf-8 -*-" or "import ").
$posCoding = $s.IndexOf("# -*- coding: utf-8 -*-")
$posImport = $s.IndexOf("import ")

if ($posCoding -ge 0) {
    # keep from the coding header onward
    $s = $s.Substring($posCoding)
} elseif ($posImport -ge 0) {
    # keep from the first import onward
    $s = $s.Substring($posImport)
} else {
    Write-Host "Repair aborted: could not find a Python header or import line to anchor on."
    exit 1
}

# Prepend the UTF-8 stdout reconfigure snippet (idempotent)
$prefix = @'
import sys
try:
    # Ensure stdout can emit UTF-8 (prevents UnicodeEncodeError on Windows consoles)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

'@

if ($s -notmatch 'sys\.stdout\.reconfigure') {
    $s = $prefix + $s
}

Set-Content -Path $path -Value $s -Encoding UTF8
Write-Host "Repair applied and backup saved as $($path + '.bak_after_corruption')"