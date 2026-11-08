# Packs the already-staged Windows build (python packaging/build_windows.py
# -> build/windows/MediaGrab) into an unsigned MSIX at
# build/msix/MediaGrab.msix, for the Microsoft Store (the Store signs it).
# AppxManifest.xml carries the Store identity from Partner Center.
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
$msix = Join-Path $out 'MediaGrab.msix'

if (-not (Test-Path (Join-Path $stage 'python\MediaGrab.exe'))) { throw "No staged build at $stage - run packaging/build_windows.py first" }
$makeappx = Get-ChildItem 'C:\Program Files (x86)\Windows Kits\10\bin\*\x64\makeappx.exe' | Sort-Object FullName | Select-Object -Last 1
if (-not $makeappx) { throw 'makeappx.exe (Windows SDK) not found' }

if (Test-Path $layout) { Remove-Item $layout -Recurse -Force }
New-Item -ItemType Directory -Force $layout | Out-Null
Copy-Item (Join-Path $stage '*') $layout -Recurse
Copy-Item (Join-Path $PSScriptRoot 'AppxManifest.xml') $layout

# Logos from the app's own .ico (the Store needs PNGs at fixed sizes).
# NOTE: every frame in mediagrab.ico is PNG-compressed, which
# System.Drawing.Icon can't decode (ToBitmap() returned random-colored noise,
# shipped as the Start menu icon once) - so the frames are cut out of the .ico
# by hand and read as plain PNGs.
Add-Type -AssemblyName System.Drawing
$assets = Join-Path $layout 'Assets'
New-Item -ItemType Directory -Force $assets | Out-Null
$icoBytes = [IO.File]::ReadAllBytes((Join-Path $root 'packaging\mediagrab.ico'))
$frames = @{}
for ($i = 0; $i -lt [BitConverter]::ToUInt16($icoBytes, 4); $i++) {
    $entry = 6 + 16 * $i
    $size = if ($icoBytes[$entry] -eq 0) { 256 } else { [int]$icoBytes[$entry] }
    $len = [BitConverter]::ToUInt32($icoBytes, $entry + 8)
    $offset = [BitConverter]::ToUInt32($icoBytes, $entry + 12)
    $frames[$size] = [System.Drawing.Image]::FromStream((New-Object IO.MemoryStream(, $icoBytes[$offset..($offset + $len - 1)])))
}
if (-not $frames[256]) { throw 'mediagrab.ico has no 256px frame' }

function Save-Logo([string]$name, [int]$w, [int]$h) {
    # The .ico's own frame when it has one at this exact size (hand-tuned for
    # small sizes), else the 256px frame scaled, centred in a w x h canvas.
    $side = [Math]::Min($w, $h)
    $src = if ($frames[$side]) { $frames[$side] } else { $frames[256] }
    $bmp = New-Object System.Drawing.Bitmap($w, $h)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.DrawImage($src, [int](($w - $side) / 2), [int](($h - $side) / 2), $side, $side)
    $bmp.Save((Join-Path $assets $name), [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
}
Save-Logo 'Square150x150Logo.png' 150 150
Save-Logo 'Square44x44Logo.png' 44 44
Save-Logo 'StoreLogo.png' 50 50
Save-Logo 'Wide310x150Logo.png' 310 150
# Start menu, taskbar and Settings ask for an exact pixel size; "unplated" =
# drawn as-is, without the tile background square behind it. Windows only
# finds these variants through resources.pri (built below).
foreach ($t in 16, 24, 32, 48, 256) {
    Save-Logo "Square44x44Logo.targetsize-$t.png" $t $t
    Save-Logo "Square44x44Logo.targetsize-${t}_altform-unplated.png" $t $t
    Save-Logo "Square44x44Logo.targetsize-${t}_altform-lightunplated.png" $t $t
}
foreach ($f in $frames.Values) { $f.Dispose() }

# resources.pri: the index of those size variants. Built from a copy holding
# only the manifest and Assets - indexing the whole layout would list every
# Python file as a resource.
$makepri = Get-ChildItem 'C:\Program Files (x86)\Windows Kits\10\bin\*\x64\makepri.exe' | Sort-Object FullName | Select-Object -Last 1
if (-not $makepri) { throw 'makepri.exe (Windows SDK) not found' }
$priRoot = Join-Path $out 'pri'
if (Test-Path $priRoot) { Remove-Item $priRoot -Recurse -Force }
New-Item -ItemType Directory -Force $priRoot | Out-Null
Copy-Item (Join-Path $layout 'AppxManifest.xml') $priRoot
Copy-Item $assets $priRoot -Recurse
$priConfig = Join-Path $out 'priconfig.xml'
& $makepri.FullName createconfig /cf $priConfig /dq en-US /pv 10.0.0 /o | Out-Null
if ($LASTEXITCODE -ne 0) { throw "makepri createconfig failed ($LASTEXITCODE)" }
& $makepri.FullName new /pr $priRoot /cf $priConfig /mn (Join-Path $priRoot 'AppxManifest.xml') /of (Join-Path $layout 'resources.pri') /o | Out-Null
if ($LASTEXITCODE -ne 0) { throw "makepri new failed ($LASTEXITCODE)" }

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
