# Place your ffmpeg.exe / yt-dlp.exe / aria2c.exe into .\bin and ensure app prefers them.
$bin = Join-Path (Get-Location) "bin"
New-Item -ItemType Directory -Force -Path $bin | Out-Null
Write-Host "Put ffmpeg.exe, yt-dlp.exe, aria2c.exe into: $bin"
