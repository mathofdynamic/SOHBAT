$ErrorActionPreference = 'Stop'
& "$PSScriptRoot/../.venv/Scripts/python.exe" "$PSScriptRoot/download_model.py"
exit $LASTEXITCODE
