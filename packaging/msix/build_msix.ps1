# Packs the already-staged Windows build (python packaging/build_windows.py
# -> build/windows/MediaGrab) into an unsigned MSIX at
# build/msix/MediaGrab-spike.msix, for the Microsoft Store (the Store signs it).
# Still a first version: AppxManifest.xml's identity is a placeholder until
# Partner Center gives the real one.
#
#   powershell -ExecutionPolicy Bypass -File packaging\msix\build_msix.ps1
#
# The staged folder is COPIED to build/msix/layout - build/windows/MediaGrab,
# which Inno Setup packs, is left untouched.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$stage = Join-Path $root 'build\windows\MediaGrab'
$out = Join-Path $root 'build\msix'
$layout = Join-Path $out 'layout'
$msix = Join-Path $out 'MediaGrab-spike.msix'

if (-not (Test-Path (Join-Path $stage 'python\MediaGrab.exe'))) { throw "No staged build at $stage - run packaging/build_windows.py first" }
$makeappx = Get-ChildItem 'C:\Program Files (x86)\Windows Kits\10\bin\*\x64\makeappx.exe' | Sort-Object FullName | Select-Object -Last 1
if (-not $makeappx) { throw 'makeappx.exe (Windows SDK) not found' }

if (Test-Path $layout) { Remove-Item $layout -Recurse -Force }
New-Item -ItemType Directory -Force $layout | Out-Null
Copy-Item (Join-Path $stage '*') $layout -Recurse
Copy-Item (Join-Path $PSScriptRoot 'AppxManifest.xml') $layout

# Logos from the app's own .ico (the Store needs PNGs at fixed sizes).
Add-Type -AssemblyName System.Drawing
$assets = Join-Path $layout 'Assets'
New-Item -ItemType Directory -Force $assets | Out-Null
$ico = Join-Path $root 'packaging\mediagrab.ico'
foreach ($a in @(@('Square150x150Logo.png', 150), @('Square44x44Logo.png', 44), @('StoreLogo.png', 50))) {
    $icon = New-Object System.Drawing.Icon($ico, 256, 256)
    $src = $icon.ToBitmap()
    $bmp = New-Object System.Drawing.Bitmap($a[1], $a[1])
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.DrawImage($src, 0, 0, $a[1], $a[1])
    $bmp.Save((Join-Path $assets $a[0]), [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose(); $src.Dispose(); $icon.Dispose()
}

# pip only serves the in-app updates, which the Store build doesn't have (its
# packages change only with a Store update; app.py refuses the update
# routes) - and Settings lists packages with importlib.metadata, not pip.
Get-ChildItem (Join-Path $layout 'python\Lib\site-packages') -Directory |
    Where-Object { $_.Name -eq 'pip' -or $_.Name -like 'pip-*.dist-info' } | Remove-Item -Recurse -Force

# Bytecode compiled HERE, by the package's own interpreter: the installed
# package folder is read-only, so Python can't write __pycache__ there and
# would recompile every module on every start. "unchecked-hash": the .pyc is
# used without comparing the .py's timestamp, which packaging may not keep -
# safe because nothing in a package ever changes.
Get-ChildItem $layout -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force
& (Join-Path $layout 'python\python.exe') -m compileall -q -j 0 --invalidation-mode unchecked-hash `
    (Join-Path $layout 'app') (Join-Path $layout 'python\Lib\site-packages')
if ($LASTEXITCODE -ne 0) { throw "compileall failed ($LASTEXITCODE)" }

if (Test-Path $msix) { Remove-Item $msix -Force }
& $makeappx.FullName pack /d $layout /p $msix /o
if ($LASTEXITCODE -ne 0) { throw "makeappx failed ($LASTEXITCODE)" }
Get-Item $msix | Select-Object FullName, @{n = 'MB'; e = { [math]::Round($_.Length / 1MB, 1) } }
