param([switch]$SkipPackage)
$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot/.."
if (!$SkipPackage) {
    & "$PSScriptRoot/package.ps1"
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
}
$version = & .venv/Scripts/python scripts/prepare_installer.py
if ($LASTEXITCODE) { exit $LASTEXITCODE }
$binary = Join-Path $PWD 'dist/SOHBAT/SOHBAT.exe'
if (!(Test-Path -LiteralPath $binary) -or (Get-Item -LiteralPath $binary).VersionInfo.ProductVersion -ne $version) {
    throw 'Packaged executable version does not match source. Rebuild without -SkipPackage.'
}
$candidates = @($env:ISCC_PATH, "$env:LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe", "${env:ProgramFiles(x86)}/Inno Setup 6/ISCC.exe", "$PWD/.perfection/tools/inno/ISCC.exe")
$compiler = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (!$compiler) {
    $found = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($found) { $compiler = $found.Source }
}
if (!$compiler) { throw 'Install Inno Setup 6.7.4+ or set ISCC_PATH to ISCC.exe.' }
& $compiler ('/DAppVersion=' + $version) ('/DPayloadDir=' + "$PWD/.perfection/installer-payload") installer/SOHBAT.iss
if ($LASTEXITCODE) { exit $LASTEXITCODE }
$setup = Join-Path $PWD ("dist/installers/SOHBAT-Setup-" + $version + '-windows-x64.exe')
$hash = (Get-FileHash -LiteralPath $setup -Algorithm SHA256).Hash.ToLowerInvariant()
($hash + '  ' + (Split-Path $setup -Leaf)) | Set-Content -Encoding ascii -LiteralPath (Join-Path (Split-Path $setup -Parent) 'SHA256SUMS.txt')
Write-Output $setup
