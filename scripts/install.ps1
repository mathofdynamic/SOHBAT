param([switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot/.."
if (!$SkipBuild) {
    & "$PSScriptRoot/package.ps1"
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
}
$installRoot = Join-Path $env:LOCALAPPDATA 'Programs/SOHBAT'
$installed = Get-ItemProperty 'HKCU:/Software/Microsoft/Windows/CurrentVersion/Uninstall/{D0E533D9-A5F2-44B0-B513-BDA47EE40618}_is1' -ErrorAction SilentlyContinue
if ($installed -and $installed.InstallLocation) { $installRoot = $installed.InstallLocation.TrimEnd('\') }
$legacyRoot = Join-Path $env:LOCALAPPDATA 'Programs/Flowlet'
$allowedExecutables = @((Join-Path $installRoot 'SOHBAT.exe'), (Join-Path $legacyRoot 'Flowlet.exe'))
$running = Get-Process SOHBAT,Flowlet -ErrorAction SilentlyContinue | Where-Object { $_.Path -in $allowedExecutables }
foreach ($process in $running) {
    $process | Stop-Process
    $process.WaitForExit()
}
New-Item -ItemType Directory -Force $installRoot | Out-Null
Copy-Item -Path 'dist/SOHBAT/*' -Destination $installRoot -Recurse -Force
& .venv/Scripts/python -c "from pathlib import Path; from sohbat.config import Config; c=Config.load(); local=Path('models/tiny-streaming-en').resolve(); c.model_path=c.model_path or (str(local) if local.is_dir() else ''); c.save()"
if ($LASTEXITCODE) { exit $LASTEXITCODE }
$configPath = Join-Path $env:LOCALAPPDATA 'SOHBAT/config.json'
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$exe = Join-Path $installRoot 'SOHBAT.exe'
$runKey = 'HKCU:/Software/Microsoft/Windows/CurrentVersion/Run'
Remove-ItemProperty -Path $runKey -Name Flowlet -ErrorAction SilentlyContinue
if ($config.autostart) {
    New-ItemProperty -Path $runKey -Name SOHBAT -Value ('"' + $exe + '"') -PropertyType String -Force | Out-Null
} else {
    Remove-ItemProperty -Path $runKey -Name SOHBAT -ErrorAction SilentlyContinue
}
$programs = [Environment]::GetFolderPath('Programs')
$legacyShortcut = Join-Path $programs 'Flowlet.lnk'
if (Test-Path -LiteralPath $legacyShortcut) { Remove-Item -LiteralPath $legacyShortcut }
$shortcutPath = Join-Path $programs 'SOHBAT.lnk'
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exe
$shortcut.WorkingDirectory = $installRoot
$shortcut.IconLocation = $exe
$shortcut.Save()
Start-Process -FilePath $exe -WorkingDirectory $installRoot -WindowStyle Normal
Write-Output "Installed and started $exe"
