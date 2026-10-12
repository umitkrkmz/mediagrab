# Windows counterpart of smoke-docker.sh: installs the built MediaGrabSetup.exe
# silently, starts MediaGrab the way its shortcut does, checks it really runs
# from the package (its own Python, FFmpeg and data folder), then uninstalls
# it silently and checks what's left.
#
#   pwsh .github/scripts/smoke-windows.ps1 dist/MediaGrabSetup.exe 2.4.0
#
# NOTE: a CI runner has no person at the screen - "silent" is exactly what a
# user never does, so the wizard's pages are covered by tests and by hand
# (CONTRIBUTING's release checklist), and this covers everything after them.

param(
    [Parameter(Mandatory = $true)] [string] $Installer,
    [Parameter(Mandatory = $true)] [string] $Version
)
$ErrorActionPreference = "Stop"

$app = Join-Path $env:LOCALAPPDATA "Programs\MediaGrab"
$data = Join-Path $env:LOCALAPPDATA "MediaGrab"
$base = "http://127.0.0.1:8420"

function Get-Json($path) {
    return Invoke-RestMethod -Uri "$base$path" -TimeoutSec 10
}

Write-Host "== install"
$p = Start-Process -FilePath $Installer -Wait -PassThru -ArgumentList @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-")
if ($p.ExitCode -ne 0) { throw "setup failed (exit $($p.ExitCode))" }
foreach ($file in @("python\MediaGrab.exe", "python\pythonw.exe", "app\run.py", "ffmpeg\ffmpeg.exe", "ffmpeg\ffprobe.exe", "mediagrab.ico", "THIRD-PARTY-NOTICES.txt", "unins000.exe")) {
    if (-not (Test-Path (Join-Path $app $file))) { throw "missing after install: $file" }
}
$description = (Get-Item (Join-Path $app "python\MediaGrab.exe")).VersionInfo.FileDescription
if ($description -ne "MediaGrab") { throw "MediaGrab.exe's description is '$description'" }

Write-Host "== start (as the Start-menu shortcut does)"
$proc = Start-Process -FilePath (Join-Path $app "python\MediaGrab.exe") -ArgumentList "`"$app\app\run.py`"" -WorkingDirectory (Join-Path $app "app") -PassThru
$up = $false
for ($i = 0; $i -lt 90; $i++) {
    try { Get-Json "/api/locale" | Out-Null; $up = $true; break } catch { Start-Sleep -Seconds 1 }
}
if (-not $up) {
    if (Test-Path "$data\mediagrab.log") { Get-Content "$data\mediagrab.log" -Tail 40 }
    throw "MediaGrab didn't answer on 8420"
}

$ffmpeg = Get-Json "/api/ffmpeg-version"
# NOTE: the package's own build - not some ffmpeg the runner happens to have:
# its "N-<number>" id, read from the pin in build_windows.py.
$pin = Select-String -Path (Join-Path $PSScriptRoot "..\..\packaging\build_windows.py") -Pattern 'FFMPEG_ASSET = "ffmpeg-(N-\d+)'
$buildId = $pin.Matches[0].Groups[1].Value
if (-not $ffmpeg.ok -or -not $ffmpeg.bundled -or $ffmpeg.ffmpeg -notmatch [regex]::Escape($buildId)) {
    throw "bundled FFmpeg not in use: $($ffmpeg | ConvertTo-Json -Compress)"
}
$mg = Get-Json "/api/mediagrab-version"
if ($mg.install_type -ne "windows") { throw "install_type is '$($mg.install_type)'" }
if ($mg.installed -ne $Version) { throw "installed version is '$($mg.installed)', expected $Version" }
$notices = Invoke-WebRequest -Uri "$base/third-party-notices" -UseBasicParsing
if ($notices.StatusCode -ne 200 -or $notices.Content -notmatch "FFmpeg") { throw "third-party notices not served" }
if (-not (Test-Path (Join-Path $data "settings.json")) -and -not (Test-Path (Join-Path $data "mediagrab.log"))) {
    throw "nothing written to the data folder $data"
}
Write-Host "MediaGrab $($mg.installed) runs from the package (FFmpeg $($ffmpeg.ffmpeg))"

Write-Host "== stop"
Stop-Process -Id $proc.Id -Force
Start-Sleep -Seconds 2

Write-Host "== uninstall"
$u = Start-Process -FilePath (Join-Path $app "unins000.exe") -Wait -PassThru -ArgumentList @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART")
if ($u.ExitCode -ne 0) { throw "uninstall failed (exit $($u.ExitCode))" }
# NOTE: the uninstaller re-launches itself from a temp copy and returns at
# once - wait for the program folder to actually go.
for ($i = 0; $i -lt 60 -and (Test-Path $app); $i++) { Start-Sleep -Seconds 1 }
if (Test-Path $app) { Get-ChildItem -Recurse $app | Select-Object -First 20 FullName; throw "program folder left behind" }
# NOTE: a silent uninstall keeps the user's data (the default choice).
if (-not (Test-Path $data)) { throw "the data folder was deleted by a silent uninstall" }
Write-Host "== all good"
