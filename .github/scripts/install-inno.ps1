# Installs Inno Setup on a Windows CI runner - a pinned version, checked
# against its SHA256 like everything else the Windows build downloads
# (packaging/build_windows.py pins Python and FFmpeg the same way).
#
#   pwsh .github/scripts/install-inno.ps1      -> adds ISCC.exe's folder to PATH
#
# NOTE: from Inno Setup's own GitHub releases (jrsoftware/issrc); the file is
# Authenticode-signed by Pyrsys B.V. (Inno Setup's maintainers). Bump the
# version, URL and hash together, and rebuild the installer by hand once.

$ErrorActionPreference = "Stop"

$version = "6.7.3"
$url = "https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe"
$sha256 = "9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732"
$target = "C:\InnoSetup"

$installer = Join-Path $env:RUNNER_TEMP "innosetup-$version.exe"
Invoke-WebRequest -Uri $url -OutFile $installer
$actual = (Get-FileHash $installer -Algorithm SHA256).Hash.ToLower()
if ($actual -ne $sha256) {
    throw "Inno Setup SHA256 mismatch: expected $sha256, got $actual"
}

$p = Start-Process -FilePath $installer -Wait -PassThru -ArgumentList @(
    "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-", "/DIR=$target"
)
if ($p.ExitCode -ne 0) { throw "Inno Setup install failed (exit $($p.ExitCode))" }
if (-not (Test-Path (Join-Path $target "ISCC.exe"))) { throw "ISCC.exe not found in $target" }

# NOTE: tests/test_installer_script.py looks for ISCC here (MEDIAGRAB_ISCC).
"MEDIAGRAB_ISCC=$(Join-Path $target 'ISCC.exe')" >> $env:GITHUB_ENV
$target >> $env:GITHUB_PATH
Write-Host "Inno Setup $version installed in $target"
