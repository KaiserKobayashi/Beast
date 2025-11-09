<#
Update packaging metadata to "downloadbeast-leviathon" and ensure src/ layout exists.
Non-destructive: writes pyproject.toml and setup.py (overwrites if present).
Usage from repo root:
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force; .\update_package_files.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$pyproject = @'
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "downloadbeast-leviathon"
version = "6.3.3"
description = "DownloadBeast - Leviathon: URL & video downloader with subtitle, transcription, translation, embedding and dubbing tools."
readme = "README.md"
authors = [
  { name="Colin KaiserKobayashi Gerrard", email="kaiserkobayashi1984@gmail.com" }
]
requires-python = ">=3.8"
dependencies = [
  "PySimpleGUI>=4.0"
]

[tool.setuptools.packages.find]
where = ["src"]
exclude = ["tests*"]

[project.scripts]
downloadbeast-leviathon = "downloadbeast.__main__:main"
'@

$setup = @'
from setuptools import setup, find_packages

setup(
    name="downloadbeast-leviathon",
    version="6.3.3",
    description="DownloadBeast - Leviathon: URL & Video downloader with subtitle, transcription, translation and dubbing tools",
    author="Colin KaiserKobayashi Gerrard",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "downloadbeast-leviathon = downloadbeast.__main__:main",
        ],
    },
)
'@

# Ensure src folder and package stub exist
if (-not (Test-Path -Path .\src)) { New-Item -ItemType Directory -Path .\src | Out-Null }
if (-not (Test-Path -Path .\src\downloadbeast)) { New-Item -ItemType Directory -Path .\src\downloadbeast | Out-Null }

# Write/overwrite pyproject.toml and setup.py
[System.IO.File]::WriteAllText((Join-Path $PWD 'pyproject.toml'), $pyproject, [System.Text.Encoding]::UTF8)
Write-Host "Wrote pyproject.toml"

[System.IO.File]::WriteAllText((Join-Path $PWD 'setup.py'), $setup, [System.Text.Encoding]::UTF8)
Write-Host "Wrote setup.py"

# Ensure minimal package __init__ and __main__ exist (only create if missing)
$initPath = Join-Path $PWD 'src\downloadbeast\__init__.py'
if (-not (Test-Path $initPath)) {
    @'
"""
DownloadBeast package bootstrap.
"""

__all__ = []
__version__ = "6.3.3"
'@ | Set-Content -Path $initPath -Encoding utf8
    Write-Host "Created src\downloadbeast\__init__.py"
} else {
    Write-Host "src\downloadbeast\__init__.py already exists; left unchanged"
}

$mainPath = Join-Path $PWD 'src\downloadbeast\__main__.py'
if (-not (Test-Path $mainPath)) {
    @'
import importlib
import sys

def _try_import_and_run(module_name, func_name="main"):
    try:
        mod = importlib.import_module(module_name)
    except Exception:
        return False
    fn = getattr(mod, func_name, None)
    if callable(fn):
        fn()
        return True
    for alt in ("run", "start", "launch"):
        fn = getattr(mod, alt, None)
        if callable(fn):
            fn()
            return True
    return False

def main():
    candidates = [
        "downloadbeast.gui",
        "downloadbeast.app",
        "downloadbeast.interface",
        "gui",
        "app",
    ]
    for c in candidates:
        if _try_import_and_run(c, "main"):
            return

    print("No GUI entrypoint found by downloadbeast-leviathon.")
    print("Create src/downloadbeast/gui.py (with a main() function) or tell me where the GUI entrypoint is.")
    sys.exit(1)

if __name__ == "__main__":
    main()
'@ | Set-Content -Path $mainPath -Encoding utf8
    Write-Host "Created src\downloadbeast\__main__.py"
} else {
    Write-Host "src\downloadbeast\__main__.py already exists; left unchanged"
}

Write-Host ""
Write-Host "Done. Review the files and then run the install steps described by the assistant."