import json
import os
import threading
import uuid
from datetime import datetime
from typing import Optional

from .paths import data_dir, is_docker

# NOTE: same "no real database" philosophy as the rest of the app - followed
# channels and their pending-notification queue live in one small JSON file,
# not in a DB. All of this module's files sit in paths.data_dir(): next to
# the app for source/Docker installs (as always), %LOCALAPPDATA%\MediaGrab
# for the Windows installer.
STORE_PATH = os.path.join(data_dir(), "channels.json")
_lock = threading.Lock()

# NOTE: kept in its own file rather than inside channels.json - these are
# unrelated concerns, and a corrupt settings file shouldn't take the followed
# channel list down with it. Neither file is committed (see .gitignore).
SETTINGS_PATH = os.path.join(data_dir(), "settings.json")
_settings_lock = threading.Lock()

# NOTE: only the cookie SOURCE is stored - a browser name or a path to a
# cookies.txt the user exported themselves. The cookies never pass through
# MediaGrab and are never written here; yt-dlp reads them directly.
DEFAULT_SETTINGS = {
    "cookie_mode": "off",  # "off" | "browser" | "file"
    "cookie_browser": "firefox",
    "cookie_file": "",
    # NOTE: when a cookies.txt was last UPLOADED (UTC, ISO 8601) - kept apart
    # from the file's own mtime, which yt-dlp bumps on every download as it
    # writes refreshed cookies back. Empty for a typed-in path.
    "cookie_uploaded_at": "",
    # NOTE: empty means "no preference" - the video's own original audio
    # plays, same as before this setting existed. Not validated against a
    # known language list on purpose: which codes are valid depends on the
    # video being downloaded, not on anything MediaGrab can check up front.
    "default_audio_lang": "",
    # NOTE: only a PBKDF2 salt+hash is ever stored, never the password itself
    # (see mediagrab/auth.py). "enabled" is a separate flag from "a password
    # is set" on purpose - remote_access_active() below requires both, so
    # flipping this on before setting a password can never expose the app.
    "remote_access_enabled": False,
    "remote_access_password_salt": "",
    "remote_access_password_hash": "",
    # NOTE: "keep" - a personal computer with plenty of disk, downloads stay
    # in indirilenler/ permanently, same as every non-remote download always
    # has. "relay" - a storage-constrained host (e.g. a Raspberry Pi acting
    # purely as a fetch-and-forward box): once a REMOTE device's download
    # finishes sending, the host's own copy is deleted right after (see
    # app.py's download routes). Only ever applies to a remote device's
    # transfer - the host's own downloads (reveal-in-explorer) are never
    # auto-deleted in either mode, since there's no "other device" it was
    # relayed to.
    "remote_download_mode": "keep",  # "keep" | "relay"
    # NOTE: 0 means unlimited (yt-dlp's own default). Stored in MB/s rather
    # than yt-dlp's native bytes/sec so a hand-edited settings.json stays
    # human-readable; downloader.py converts at the point of use.
    "download_speed_limit_mbps": 0,
    # NOTE: off by default (matches the app's original "you open it, it
    # runs" design). When on, followed channels are checked periodically
    # (see app.py's _periodic_channel_check_loop) instead of only once at
    # launch - meant for a device left running continuously (a Raspberry
    # Pi/mini PC, or a desktop someone chooses to keep open). Independent of
    # remote_access_enabled: either can be on without the other.
    "home_server_mode": False,
    # NOTE: empty = the default (downloader.DOWNLOAD_DIR). A path on THIS
    # machine, so it's never part of a settings backup (see app.py's
    # _SETTINGS_BACKUP_EXCLUDED_KEYS) and is ignored in Docker, where the
    # compose file's volume decides where downloads go.
    "download_dir": "",
}


def remote_access_active(settings: dict) -> bool:
    """True only when LAN access is both turned on AND a password is set.

    Used by BOTH the auth middleware (app.py) and the startup bind-host
    decision (run.py) - the same predicate for "should logins be required"
    and "should the server listen beyond localhost", so the two facts can
    never drift apart (e.g. listening on 0.0.0.0 while enforcing no login).
    """
    return bool(settings.get("remote_access_enabled")) and bool(settings.get("remote_access_password_hash"))


def get_settings() -> dict:
    with _settings_lock:
        settings = dict(DEFAULT_SETTINGS)
        if not os.path.isfile(SETTINGS_PATH):
            return settings
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                stored = json.load(f)
        except Exception:
            # NOTE: a hand-edited or truncated file falls back to defaults
            # rather than breaking every download.
            return settings
        if isinstance(stored, dict):
            settings.update({k: v for k, v in stored.items() if k in DEFAULT_SETTINGS})
        return settings


def save_settings(**fields) -> dict:
    with _settings_lock:
        current = dict(DEFAULT_SETTINGS)
        if os.path.isfile(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                if isinstance(stored, dict):
                    current.update({k: v for k, v in stored.items() if k in DEFAULT_SETTINGS})
            except Exception:
                pass
        current.update({k: v for k, v in fields.items() if k in DEFAULT_SETTINGS})
        # NOTE: the Windows installer's data folder doesn't exist until the
        # first thing is saved into it.
        os.makedirs(os.path.dirname(SETTINGS_PATH) or ".", exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        return current


def _load() -> dict:
    if not os.path.isfile(STORE_PATH):
        return {"channels": [], "pending": []}
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"channels": [], "pending": []}
    data.setdefault("channels", [])
    data.setdefault("pending", [])
    return data


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(STORE_PATH) or ".", exist_ok=True)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_channels() -> list[dict]:
    with _lock:
        return _load()["channels"]


def add_channel(
    url: str,
    name: str,
    thumbnail: Optional[str],
    mode: str,
    choice_kind: str,
    choice: str,
    last_video_id: Optional[str],
) -> dict:
    with _lock:
        data = _load()
        channel = {
            "id": uuid.uuid4().hex,
            "url": url,
            "name": name,
            "thumbnail": thumbnail,
            "mode": mode,  # "notify" | "auto"
            "choice_kind": choice_kind,  # "audio" | "video"
            "choice": choice,  # "opus"/"m4a"/"mp3" for audio, "best" for video
            "last_video_id": last_video_id,
            "added_at": datetime.now().isoformat(timespec="seconds"),
            "last_checked_at": None,
        }
        data["channels"].append(channel)
        _save(data)
        return channel


def remove_channel(channel_id: str) -> None:
    with _lock:
        data = _load()
        data["channels"] = [c for c in data["channels"] if c["id"] != channel_id]
        _save(data)


def update_channel(channel_id: str, **fields) -> None:
    with _lock:
        data = _load()
        for c in data["channels"]:
            if c["id"] == channel_id:
                c.update(fields)
                break
        _save(data)


def get_pending() -> list[dict]:
    with _lock:
        return _load()["pending"]


def add_pending(entries: list[dict]) -> None:
    if not entries:
        return
    with _lock:
        data = _load()
        data["pending"].extend(entries)
        _save(data)


def clear_pending() -> None:
    with _lock:
        data = _load()
        data["pending"] = []
        _save(data)


def replace_channels(channels: list[dict], pending: list[dict]) -> None:
    # NOTE: a full replace, not a merge - used by the settings import route,
    # where the whole point is "make this device match the backup file"
    # (moving to a new device, or restoring after a reinstall). A merge would
    # need to resolve id collisions and doesn't match either use case.
    with _lock:
        _save({"channels": channels, "pending": pending})


# --- download statistics (History -> Statistics) -------------------------------

# NOTE: its own file, like settings.json vs channels.json - a corrupt stats
# file must never take settings or followed channels down with it. In Docker
# it's a FOLDER mount (see docker-compose.yml, same reasoning as cookies), so
# no placeholder file has to exist before the container first starts.
STATS_PATH = "/data/stats/stats.json" if is_docker() else os.path.join(data_dir(), "stats.json")
_stats_lock = threading.Lock()

# NOTE: what's stored is deliberately coarse - per UTC hour, how many files
# and bytes of each (site, kind, format), nothing else: no titles, URLs,
# channel names or file names. UTC hours (not local days) because the
# server's clock can't know the viewer's day boundaries - a Docker container
# runs on UTC - so the browser sends its offset and the grouping into
# days/weeks/months happens at read time (see stats.summarize).
_EMPTY_STATS = {"version": 1, "backfilled": False, "hours": {}}


def _load_stats() -> dict:
    data = {**_EMPTY_STATS, "hours": {}}
    if not os.path.isfile(STATS_PATH):
        return data
    try:
        with open(STATS_PATH, "r", encoding="utf-8") as f:
            stored = json.load(f)
    except Exception:
        # NOTE: unreadable -> start over rather than break every download.
        return data
    if isinstance(stored, dict) and isinstance(stored.get("hours"), dict):
        data["hours"] = stored["hours"]
        data["backfilled"] = bool(stored.get("backfilled"))
    return data


def _save_stats(data: dict) -> None:
    # NOTE: write-then-rename, so a crash mid-write leaves the previous file
    # intact instead of a truncated one (which _load_stats would discard).
    os.makedirs(os.path.dirname(STATS_PATH) or ".", exist_ok=True)
    tmp = STATS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, STATS_PATH)


def _add_stat(hours: dict, hour: str, entry: dict) -> None:
    rows = hours.setdefault(hour, [])
    for row in rows:
        if row["site"] == entry["site"] and row["kind"] == entry["kind"] and row["format"] == entry["format"]:
            row["count"] += 1
            row["bytes"] += entry["bytes"]
            return
    rows.append({"site": entry["site"], "kind": entry["kind"], "format": entry["format"], "count": 1, "bytes": entry["bytes"]})


def record_downloads(items: list[tuple[str, dict]], mark_backfilled: bool = False) -> None:
    """Add finished downloads: (UTC hour "YYYY-MM-DDTHH", {site, kind, format, bytes})."""
    with _stats_lock:
        data = _load_stats()
        for hour, entry in items:
            _add_stat(data["hours"], hour, entry)
        if mark_backfilled:
            data["backfilled"] = True
        _save_stats(data)


def get_stats() -> dict:
    with _stats_lock:
        return _load_stats()


def reset_stats() -> None:
    # NOTE: stays marked as backfilled - "reset" means start counting from
    # now, not "re-import every file still on disk" on the next start.
    with _stats_lock:
        _save_stats({**_EMPTY_STATS, "hours": {}, "backfilled": True})
