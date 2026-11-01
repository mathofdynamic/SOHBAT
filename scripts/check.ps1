$ErrorActionPreference = 'Stop'
& "$PSScriptRoot/../.venv/Scripts/python.exe" -m ruff check sohbat tests
if ($LASTEXITCODE) { exit $LASTEXITCODE }
& "$PSScriptRoot/../.venv/Scripts/python.exe" -m mypy sohbat
if ($LASTEXITCODE) { exit $LASTEXITCODE }
& "$PSScriptRoot/../.venv/Scripts/python.exe" -m pytest -q
exit $LASTEXITCODE
