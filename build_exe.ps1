param(
  [string]$Entry = "src\DownloadBeast\gui\app.py",
  [string]$Name = "DownloadBeast_Pro",
  [switch]$OneFile
)
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Write-Host "Python not found." -ForegroundColor Red; exit 1 }
$specArgs = @("pyinstaller","--noconfirm","--name",$Name,"--add-data","version.txt;.")
if ($OneFile) { $specArgs += "--onefile" }
$specArgs += $Entry
& $py.Source $specArgs
