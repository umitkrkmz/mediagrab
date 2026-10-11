"""Stage a self-contained Windows build of MediaGrab for the Inno Setup installer.

    python packaging/build_windows.py            # stage into build/windows/MediaGrab
    ISCC packaging/mediagrab.iss                  # then compile the installer

What ends up in the staging folder (and so on the user's machine):

    python/   the official embeddable Python, with every package from
              requirements.txt (and pip) installed into Lib/site-packages
    app/      MediaGrab's own code (mediagrab/, run.py, licences)
    ffmpeg/   ffmpeg.exe + ffprobe.exe and their shared DLLs

NOTE: everything is downloaded at a PINNED version and checked against a
PINNED SHA256 (taken from python.org's release page and yt-dlp's own
checksums.sha256) - a release is reproducible from this file, and a swapped
or corrupted download stops the build instead of shipping. The user's
machine never runs git or pip during install; pip is still bundled so the
app's own "update yt-dlp" button keeps working (the embedded Python lives in
the user's own, writable folder).
"""

import hashlib
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
CACHE = os.path.join(BUILD, "cache")
STAGE = os.path.join(BUILD, "windows", "MediaGrab")

PYTHON_VERSION = "3.14.8"
PYTHON_TAG = "314"  # python314._pth, cp314 wheels
PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
PYTHON_SHA256 = "a93abe456ab01bd96d7a085b3cdb6566b3063f4241360d114142fbdb07f0a310"

# NOTE: yt-dlp's own FFmpeg builds (patched for yt-dlp's needs). The dated
# "autobuild" releases are kept for a long time; "latest" is not pinnable.
# "gpl-shared" rather than the static "gpl" zip: ffmpeg and ffprobe share
# one set of DLLs instead of each carrying its own (~89 MB vs ~200 MB).
FFMPEG_TAG = "autobuild-2026-10-10-18-21"
FFMPEG_ASSET = "ffmpeg-N-127276-g8e9db1f152-win64-gpl-shared.zip"
FFMPEG_URL = f"https://github.com/yt-dlp/FFmpeg-Builds/releases/download/{FFMPEG_TAG}/{FFMPEG_ASSET}"
FFMPEG_SHA256 = "974866fd96bd439398398d9fd7e2bdb1d639f3d00a2a83f504b388416ab1e2c2"

APP_FILES = ("run.py", "requirements.txt", "LICENSE", "LICENSE-MIT", "README.md")


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, expected_sha256: str) -> str:
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, url.rsplit("/", 1)[-1])
    if not os.path.isfile(path) or sha256_of(path) != expected_sha256:
        print(f"download {url}")
        tmp = path + ".part"
        urllib.request.urlretrieve(url, tmp)
        os.replace(tmp, path)
    actual = sha256_of(path)
    if actual != expected_sha256:
        raise SystemExit(f"SHA256 mismatch for {url}\n  expected {expected_sha256}\n  got      {actual}")
    return path


def stage_python() -> str:
    target = os.path.join(STAGE, "python")
    with zipfile.ZipFile(fetch(PYTHON_URL, PYTHON_SHA256)) as z:
        z.extractall(target)
    # NOTE: the embeddable Python ignores PYTHONPATH and builds sys.path only
    # from this file. "import site" turns on site-packages (where pip and
    # the requirements go); "..\app" makes `import mediagrab` work.
    pth = os.path.join(target, f"python{PYTHON_TAG}._pth")
    with open(pth, "w", encoding="utf-8") as f:
        f.write(f"python{PYTHON_TAG}.zip\n.\nLib\\site-packages\n..\\app\nimport site\n")
    return target


def stage_packages(python_dir: str) -> None:
    site_packages = os.path.join(python_dir, "Lib", "site-packages")
    # NOTE: installed by THIS (host) Python into the embedded one's folder,
    # binary wheels only, for exactly the embedded interpreter's ABI - so
    # nothing compiles and nothing depends on what the build machine has.
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--no-compile",
            "--target", site_packages,
            "--only-binary=:all:", "--platform", "win_amd64",
            "--python-version", PYTHON_VERSION, "--implementation", "cp", "--abi", f"cp{PYTHON_TAG}",
            "-r", os.path.join(ROOT, "requirements.txt"), "pip",
        ],
        check=True,
    )
    # NOTE: with --target, pip puts executables in site-packages\bin, but the
    # app (downloader.js_runtime_status) and pip itself, when the user later
    # updates yt-dlp from Settings, use python\Scripts. Only Deno is a real
    # program there; the rest are pip's console-script launchers, which point
    # at the BUILD machine's Python (their shebang reads e.g.
    # "#!E:\...\.venv\Scripts\python.exe") and would be broken on every user's
    # machine. The app never uses them (it always runs `python -m ...`), and
    # pip writes correct ones on the first in-app update.
    bin_dir = os.path.join(site_packages, "bin")
    scripts = os.path.join(python_dir, "Scripts")
    os.makedirs(scripts, exist_ok=True)
    os.replace(os.path.join(bin_dir, "deno.exe"), os.path.join(scripts, "deno.exe"))
    shutil.rmtree(bin_dir)

    frozen = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--path", site_packages, "--format", "freeze"],
        check=True, capture_output=True, text=True,
    ).stdout
    # NOTE: the exact versions this release ships, for bug reports and for
    # reproducing a build.
    with open(os.path.join(STAGE, "app", "requirements-lock.txt"), "w", encoding="utf-8") as f:
        f.write(frozen)


def stage_app() -> None:
    target = os.path.join(STAGE, "app")
    shutil.copytree(
        os.path.join(ROOT, "mediagrab"), os.path.join(target, "mediagrab"),
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    for name in APP_FILES:
        shutil.copy2(os.path.join(ROOT, name), target)
    # NOTE: next to python\ and app\ - the shortcuts, "Installed apps" and
    # the tray icon (run.py _icon_path) all use it from there.
    shutil.copy2(os.path.join(ROOT, "packaging", "mediagrab.ico"), STAGE)


def stage_launcher(python_dir: str) -> None:
    # NOTE: MediaGrab.exe = pythonw.exe under MediaGrab's name and icon, so
    # Task Manager doesn't list MediaGrab as "Python" - see exe_branding.py
    # (and why its signature is removed rather than left broken).
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import exe_branding

    with open(os.path.join(ROOT, "mediagrab", "__init__.py"), encoding="utf-8") as f:
        version = re.search(r'__version__ = "([^"]+)"', f.read()).group(1)
    exe_branding.brand(
        os.path.join(python_dir, "pythonw.exe"),
        os.path.join(python_dir, "MediaGrab.exe"),
        os.path.join(ROOT, "packaging", "mediagrab.ico"),
        version,
    )


def stage_ffmpeg() -> None:
    target = os.path.join(STAGE, "ffmpeg")
    os.makedirs(target)
    with zipfile.ZipFile(fetch(FFMPEG_URL, FFMPEG_SHA256)) as z:
        for member in z.namelist():
            name = member.rsplit("/", 1)[-1]
            wanted = (
                (member.split("/")[-2:-1] == ["bin"] and (name.endswith(".dll") or name in ("ffmpeg.exe", "ffprobe.exe")))
                or name == "LICENSE.txt"
            )
            if wanted:
                with z.open(member) as src, open(os.path.join(target, name), "wb") as dst:
                    shutil.copyfileobj(src, dst)


def folder_size(path: str) -> int:
    return sum(os.path.getsize(os.path.join(r, f)) for r, _d, files in os.walk(path) for f in files)


def main() -> None:
    if sys.version_info[:2] != (3, int(PYTHON_TAG[1:])):
        raise SystemExit(f"run this with Python 3.{PYTHON_TAG[1:]} (the embedded version), not {sys.version.split()[0]}")
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)
    stage_app()
    python_dir = stage_python()
    stage_packages(python_dir)
    stage_launcher(python_dir)
    stage_ffmpeg()
    for part in ("python", "app", "ffmpeg"):
        print(f"{part:7} {folder_size(os.path.join(STAGE, part)) / 2**20:7.1f} MB")
    total = folder_size(STAGE)
    print(f"total   {total / 2**20:7.1f} MB  ->  {STAGE}")
    # NOTE: read by mediagrab.iss (ExtraDiskSpaceRequired) - those files are
    # installed only for a normal install (a Check), and Inno leaves such
    # files out of the "at least ... MB" it shows, which said 4.3 MB.
    with open(os.path.join(os.path.dirname(STAGE), "payload-bytes.txt"), "w", encoding="ascii") as f:
        f.write(str(total))


if __name__ == "__main__":
    main()
