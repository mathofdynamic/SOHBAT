$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot/.."
if (!(Test-Path .venv/Scripts/python.exe)) { python -m venv .venv }
& .venv/Scripts/python -m pip install -e . pytest ruff mypy psutil
if ($LASTEXITCODE) { exit $LASTEXITCODE }
& "$PSScriptRoot/download-model.ps1"
