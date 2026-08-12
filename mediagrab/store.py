import json
import os
import threading
import uuid
from datetime import datetime
from typing import Optional

from .paths import app_dir

# NOTE: same "no real database" philosophy as the rest of the app - followed
# channels and their pending-notification queue live in one small JSON file
# next to indirilenler/, not in a DB.
STORE_PATH = os.path.join(app_dir(), "channels.json")
_lock = threading.Lock()


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
