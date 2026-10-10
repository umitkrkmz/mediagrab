"""Download statistics: what gets counted, and how it's summarized.

NOTE: persistence lives in store.py (record_downloads / get_stats /
reset_stats), like every other piece of saved state; this module only turns
a finished file into a counted entry and turns the stored hours into the
day/week/month view History -> Statistics shows. Nothing here imports
yt-dlp - the file itself (ffprobe, via downloader.get_stream_info) and the
metadata sidecar written next to it are the only sources.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import downloader, store

AUDIO_EXTS = ("opus", "m4a", "mp3")
VIDEO_EXTS = ("mp4", "mkv")

# NOTE: yt-dlp's extractor_key -> the name people know. Several extractors
# share a site (YoutubeTab, TwitchVod, TwitchClips...), so matching is by
# prefix; anything unknown keeps its own key, which is already readable
# ("Vimeo", "Dailymotion"). "Generic" (a direct link to a file) and a missing
# sidecar are stored as-is and named in the UI.
_SITE_PREFIXES = (
    ("youtube", "YouTube"),
    ("soundcloud", "SoundCloud"),
    ("twitter", "X (Twitter)"),
    ("twitch", "Twitch"),
    ("instagram", "Instagram"),
    ("tiktok", "TikTok"),
    ("facebook", "Facebook"),
    ("reddit", "Reddit"),
    ("vimeo", "Vimeo"),
    ("dailymotion", "Dailymotion"),
    ("bandcamp", "Bandcamp"),
    ("bilibili", "Bilibili"),
    ("kick", "Kick"),
    ("mixcloud", "Mixcloud"),
)


def site_name(extractor: Optional[str]) -> str:
    if not extractor:
        return ""
    key = extractor.lower()
    for prefix, name in _SITE_PREFIXES:
        if key.startswith(prefix):
            return name
    return extractor


def _sidecar_extractor(path: str) -> Optional[str]:
    try:
        with open(downloader.metadata_sidecar_path(path), "r", encoding="utf-8") as f:
            return json.load(f).get("extractor")
    except Exception:
        return None


def classify(path: str) -> Optional[dict]:
    """A finished file -> {site, kind, format, bytes}, or None if it isn't counted.

    Only audio and video are counted - subtitles and transcripts are extras
    that ride along with a download, not downloads of their own.
    """
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if ext in AUDIO_EXTS:
        kind, fmt = "audio", ext
    elif ext in VIDEO_EXTS:
        # NOTE: the resolution actually in the file, not the button that was
        # pressed ("best" says nothing) - the same reading as the item page.
        video = downloader.get_stream_info(path).get("video") or {}
        kind, fmt = "video", video.get("quality") or ""
    else:
        return None
    try:
        size = os.path.getsize(path)
    except OSError:
        return None
    return {"site": site_name(_sidecar_extractor(path)), "kind": kind, "format": fmt, "bytes": size}


def utc_hour(timestamp: Optional[float] = None) -> str:
    moment = datetime.fromtimestamp(timestamp, timezone.utc) if timestamp is not None else datetime.now(timezone.utc)
    return moment.strftime("%Y-%m-%dT%H")


def record_finished(path: str) -> None:
    # NOTE: best-effort - a statistics hiccup must never turn a finished
    # download into a failed one.
    try:
        entry = classify(path)
        if entry:
            store.record_downloads([(utc_hour(), entry)])
    except Exception:
        pass


def backfill(cutoff: float) -> int:
    """Count the files already in the downloads folder, once.

    Only files older than `cutoff` (when this run started) - anything newer
    was finished while this ran and is recorded by record_finished already.
    Files deleted before this feature existed (e.g. in relay mode) can't be
    recovered; the UI says so.
    """
    items = []
    for root, _dirs, files in os.walk(downloader.DOWNLOAD_DIR):
        for name in files:
            path = os.path.join(root, name)
            try:
                mtime = os.path.getmtime(path)
            except OSError:
                continue
            if mtime >= cutoff:
                continue
            entry = classify(path)
            if entry:
                items.append((utc_hour(mtime), entry))
    store.record_downloads(items, mark_backfilled=True)
    return len(items)


# --- summary ------------------------------------------------------------------

PERIODS = {"day": 14, "week": 12, "month": 12}


def _bucket_start(moment: datetime, period: str) -> datetime:
    day = moment.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        # NOTE: weeks start on Monday (ISO 8601), as in Turkey and most of Europe.
        return day - timedelta(days=day.weekday())
    if period == "month":
        return day.replace(day=1)
    return day


def _previous_start(start: datetime, period: str) -> datetime:
    if period == "week":
        return start - timedelta(days=7)
    if period == "month":
        return (start - timedelta(days=1)).replace(day=1)
    return start - timedelta(days=1)


def _ranked(counter: dict) -> list[dict]:
    return sorted(
        ({"name": name, "count": c, "bytes": b} for name, (c, b) in counter.items()),
        key=lambda row: (-row["count"], -row["bytes"], row["name"]),
    )


def summarize(data: dict, period: str, tz_offset_minutes: int, now: Optional[datetime] = None) -> dict:
    """Group the stored UTC hours into the viewer's local days/weeks/months.

    tz_offset_minutes is local minus UTC (Turkey: +180).
    """
    if period not in PERIODS:
        period = "day"
    offset = timedelta(minutes=tz_offset_minutes)
    local_now = (now or datetime.now(timezone.utc)).replace(tzinfo=None) + offset

    starts = [_bucket_start(local_now, period)]
    for _ in range(PERIODS[period] - 1):
        starts.append(_previous_start(starts[-1], period))
    starts.reverse()
    window_start = starts[0]
    buckets = {start: [0, 0] for start in starts}

    sites: dict = {}
    audio: dict = {}
    video: dict = {}
    total_count = total_bytes = 0
    first: Optional[datetime] = None

    for hour, rows in data.get("hours", {}).items():
        try:
            local = datetime.strptime(hour, "%Y-%m-%dT%H") + offset
        except ValueError:
            continue
        for row in rows:
            count, size = int(row.get("count", 0)), int(row.get("bytes", 0))
            total_count += count
            total_bytes += size
            first = local if first is None or local < first else first
            if local < window_start:
                continue
            bucket = buckets.get(_bucket_start(local, period))
            if bucket is None:
                # NOTE: later than "now" (the clock moved backwards) - left
                # out of the window so the bars and breakdowns always agree.
                continue
            bucket[0] += count
            bucket[1] += size
            for counter, key in (
                (sites, row.get("site", "")),
                (audio if row.get("kind") == "audio" else video, row.get("format", "")),
            ):
                entry = counter.setdefault(key, [0, 0])
                entry[0] += count
                entry[1] += size

    return {
        "period": period,
        "buckets": [{"start": s.date().isoformat(), "count": c, "bytes": b} for s, (c, b) in buckets.items()],
        "window": {
            "count": sum(c for c, _ in buckets.values()),
            "bytes": sum(b for _, b in buckets.values()),
            "sites": _ranked(sites),
            "audio_formats": _ranked(audio),
            "video_formats": _ranked(video),
        },
        "total": {
            "count": total_count,
            "bytes": total_bytes,
            "since": first.date().isoformat() if first else None,
        },
    }
