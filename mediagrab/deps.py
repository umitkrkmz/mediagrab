"""Version checks for things MediaGrab depends on but doesn't bundle.

NOTE: yt-dlp's own check lives in downloader.py instead, because it reads the
version straight from the imported module - and that file is the only one
allowed to touch yt_dlp. Everything here is about the *environment*: the
ffmpeg binaries on PATH, and the Python packages in the active venv.
"""

import json
import re
import subprocess
import sys
import urllib.request
from importlib.metadata import PackageNotFoundError, version as installed_version
from typing import Optional

from .paths import app_dir

# NOTE: matches "ffmpeg version 7.1-full_build-www.gyan.dev ..." and the
# distro variants ("ffmpeg version n7.1", "ffmpeg version 6.1.1-3ubuntu5").
_FFMPEG_VERSION_RE = re.compile(r"^\w+ version n?([0-9][^\s,]*)")

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

# NOTE: all three are shown in the UI, not just the detected platform - the
# same MediaGrab install gets used from different machines (and people read
# these docs for a machine they're setting up, not the one they're on).
FFMPEG_INSTALL_COMMANDS = [
    {"key": "windows", "label": "Windows", "command": "winget install --id Gyan.FFmpeg -e"},
    {"key": "macos", "label": "macOS", "command": "brew install ffmpeg"},
    {"key": "linux", "label": "Linux (Debian/Ubuntu)", "command": "sudo apt install ffmpeg"},
]


def _tool_version(tool: str) -> Optional[str]:
    try:
        result = subprocess.run(
            [tool, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    first_line = (result.stdout or "").strip().splitlines()
    if not first_line:
        return None
    match = _FFMPEG_VERSION_RE.match(first_line[0])
    return match.group(1) if match else first_line[0]


def check_ffmpeg() -> dict:
    # NOTE: ffmpeg has no canonical "latest version" API the way PyPI does -
    # every platform ships its own build and numbering (gyan.dev, Homebrew,
    # distro packages), so claiming "an update is available" would be a guess.
    # We report what's installed and hand over the right install/update command
    # instead, and deliberately do NOT run a system package manager ourselves:
    # that reaches outside the venv and often needs elevation.
    ffmpeg = _tool_version("ffmpeg")
    ffprobe = _tool_version("ffprobe")
    if sys.platform == "win32":
        platform_key = "windows"
    elif sys.platform == "darwin":
        platform_key = "macos"
    else:
        platform_key = "linux"
    return {
        "ffmpeg": ffmpeg,
        "ffprobe": ffprobe,
        "ok": bool(ffmpeg and ffprobe),
        "platform": platform_key,
        "install_commands": FFMPEG_INSTALL_COMMANDS,
    }


def _requirement_names() -> list[str]:
    # NOTE: read from requirements.txt so this list can't drift from what the
    # project actually declares. Strips version specifiers and any extras
    # ("uvicorn[standard]>=0.30" -> "uvicorn").
    path = f"{app_dir()}/requirements.txt"
    names = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                name = re.split(r"[<>=!~\[;]", line, maxsplit=1)[0].strip()
                if name:
                    names.append(name)
    except OSError:
        return []
    return names


def _pypi_latest(package: str) -> Optional[str]:
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{package}/json", timeout=5) as resp:
            return json.loads(resp.read())["info"]["version"]
    except Exception:
        return None


def _parse_version(v: str) -> tuple:
    # NOTE: same numeric comparison as downloader._parse_version - a plain
    # string compare gets "0.10" < "0.9" wrong. Non-numeric suffixes (rc, b1)
    # are dropped rather than guessed at.
    parts = []
    for part in v.split("."):
        match = re.match(r"^(\d+)", part)
        if not match:
            break
        parts.append(int(match.group(1)))
    return tuple(parts)


def check_dependencies() -> dict:
    packages = []
    checked_any = False
    for name in _requirement_names():
        try:
            current = installed_version(name)
        except PackageNotFoundError:
            packages.append({"name": name, "installed": None, "latest": None, "update_available": None})
            continue
        latest = _pypi_latest(name)
        if latest is not None:
            checked_any = True
        update_available = None
        if latest:
            update_available = _parse_version(latest) > _parse_version(current)
        packages.append(
            {"name": name, "installed": current, "latest": latest, "update_available": update_available}
        )
    return {
        # NOTE: distinguishes "everything is current" from "we couldn't reach
        # PyPI at all" - both would otherwise look like an empty update list.
        "reachable": checked_any,
        "packages": packages,
        "update_count": sum(1 for p in packages if p["update_available"]),
    }


def update_dependencies() -> dict:
    # NOTE: same reasoning as downloader.update_ytdlp() - sys.executable is
    # this process's own interpreter, already inside the user's venv, so pip
    # installs land in the right place without activating anything.
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "-r", f"{app_dir()}/requirements.txt"],
            capture_output=True,
            text=True,
            timeout=300,
            creationflags=_NO_WINDOW,
        )
        return {
            "ok": result.returncode == 0,
            "output": ((result.stdout or "") + (result.stderr or "")).strip(),
        }
    except Exception as exc:
        return {"ok": False, "output": str(exc)}
