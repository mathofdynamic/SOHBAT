$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot/.."
if (!(Test-Path .venv/Scripts/python.exe)) { throw 'Run scripts/setup.ps1 first.' }
# Windows PowerShell treats redirected native stderr as ErrorRecords. Both pip
# and PyInstaller use stderr for progress, so use exit codes for native tools.
$ErrorActionPreference = 'Continue'
& .venv/Scripts/python -m pip install --disable-pip-version-check --quiet pyinstaller
if ($LASTEXITCODE) { exit $LASTEXITCODE }
& .venv/Scripts/python scripts/write_version_info.py
if ($LASTEXITCODE) { exit $LASTEXITCODE }
& .venv/Scripts/python -m PyInstaller --noconfirm --windowed --name SOHBAT --version-file build/version-info.txt --icon sohbat/assets/brand/app.ico --add-data "sohbat/assets;sohbat/assets" --collect-all moonshine_voice --collect-submodules comtypes.gen scripts/launch.py
exit $LASTEXITCODE
