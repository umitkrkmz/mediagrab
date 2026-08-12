# The yt_dlp import must appear ONLY in this file. Other modules call this
# file's functions instead of touching the yt-dlp API directly.
import base64
import os
import subprocess
import sys
from typing import Callable, Optional

from mutagen import File as MutagenFile
from mutagen.flac import Picture
from yt_dlp import YoutubeDL

from .paths import app_dir


class ProbeError(Exception):
    pass


DOWNLOAD_DIR = os.path.join(app_dir(), "indirilenler")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# NOTE: the video ID is deliberately left out of the filename - removed at the
# user's request. The cost: re-downloading the same video at a different
# quality reuses the same filename and overwrites it (intentional, see
# "overwrites" below).
OUTTMPL = os.path.join(DOWNLOAD_DIR, "%(title).120B.%(ext)s")


def human_size(num_bytes: Optional[float]) -> str:
    if not num_bytes:
        return "?"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.0f} {unit}"
        size /= 1024
    return "?"


def _dedupe_video_formats(formats: list[dict]) -> list[dict]:
    # NOTE: keep only the highest-tbr variant per height.
    best_by_height: dict[int, dict] = {}
    for f in formats:
        if f.get("vcodec") in (None, "none"):
            continue
        height = f.get("height")
        if not height:
            continue
        tbr = f.get("tbr") or 0
        current = best_by_height.get(height)
        if current is None or tbr > (current.get("tbr") or 0):
            best_by_height[height] = f

    result = []
    for height in sorted(best_by_height.keys(), reverse=True):
        f = best_by_height[height]
        size = f.get("filesize") or f.get("filesize_approx")
        vcodec = (f.get("vcodec") or "?").split(".")[0]
        result.append(
            {
                "format_id": f["format_id"],
                "label": f"{height}p",
                "ext": f.get("ext", "?"),
                "vcodec": vcodec,
                "size": human_size(size),
            }
        )
    return result


def _subtitle_list(info: dict) -> list[dict]:
    # NOTE: only manually-provided subtitles are listed. Automatic captions
    # (automatic_captions) can show up in dozens of languages because of
    # YouTube's auto-translate feature, which would bloat the list pointlessly.
    subs = info.get("subtitles") or {}
    result = [{"code": code, "label": code} for code, tracks in subs.items() if tracks]
    result.sort(key=lambda s: s["label"])
    return result


def _best_thumbnail(entry: dict) -> Optional[str]:
    thumb = entry.get("thumbnail")
    if thumb:
        return thumb
    thumbs = entry.get("thumbnails") or []
    if not thumbs:
        return None
    best = max(thumbs, key=lambda t: (t.get("height") or 0) * (t.get("width") or 0))
    return best.get("url")


def _normalize_channel_url(url: str) -> str:
    # NOTE: a bare channel URL (e.g. "youtube.com/@TED") resolves to the
    # channel's TAB LIST (Videos/Live/Shorts) under extract_flat, not actual
    # videos. Appending "/videos" points straight at the uploads feed.
    url = url.strip().rstrip("/")
    if url.endswith(("/videos", "/streams", "/shorts", "/playlists")):
        return url
    return url + "/videos"


def resolve_channel(url: str) -> dict:
    # NOTE: used when a channel is first followed - only establishes the
    # current newest video as a baseline. Older uploads are NOT treated as
    # "new" (matches normal subscribe-from-now-on expectations, and avoids
    # notifying/auto-downloading a channel's entire back catalog on add).
    norm_url = _normalize_channel_url(url)
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "playlistend": 1,
    }
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(norm_url, download=False)
    except Exception as exc:
        raise ProbeError(str(exc)) from exc

    if info.get("_type") != "playlist":
        raise ProbeError("Bu bir kanal linki gibi gorunmuyor")

    entries = [e for e in (info.get("entries") or []) if e and e.get("id")]
    latest = entries[0] if entries else None

    return {
        "url": norm_url,
        "name": info.get("channel") or info.get("title") or norm_url,
        "thumbnail": _best_thumbnail(info) or (latest and _best_thumbnail(latest)),
        "last_video_id": latest["id"] if latest else None,
    }


def check_channel_new_videos(url: str, last_video_id: Optional[str], limit: int = 15) -> list[dict]:
    # NOTE: relies on the channel's uploads feed being newest-first (it is,
    # by default). Stops at the first entry matching last_video_id, so
    # everything before it in the list is "new". Capped at `limit` per check
    # so a channel that uploaded 200 videos since the last check doesn't
    # flood a single check.
    if not last_video_id:
        return []
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "playlistend": limit,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = [e for e in (info.get("entries") or []) if e and e.get("id")]
    new_entries = []
    for e in entries:
        if e["id"] == last_video_id:
            break
        new_entries.append(e)

    return [
        {
            "id": e["id"],
            "title": e.get("title") or "?",
            "url": e.get("url") or f"https://www.youtube.com/watch?v={e['id']}",
            "thumbnail": _best_thumbnail(e),
            "duration": int(e.get("duration") or 0),
        }
        for e in new_entries
    ]


def probe(url: str) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        # NOTE: without extract_flat, a playlist link tries to fetch full info
        # (including formats) for EVERY video before it even knows it's a
        # playlist (very slow). "in_playlist" gives a fast listing (id/title/
        # duration/thumbnail); format resolution happens once the user picks a video.
        "extract_flat": "in_playlist",
    }
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        raise ProbeError(str(exc)) from exc

    if info.get("_type") == "playlist":
        entries = []
        for e in info.get("entries") or []:
            if not e or not e.get("id"):
                continue
            entries.append(
                {
                    "id": e["id"],
                    "title": e.get("title") or "?",
                    "url": e.get("url") or f"https://www.youtube.com/watch?v={e['id']}",
                    "duration": int(e.get("duration") or 0),
                    "uploader": e.get("uploader") or e.get("channel"),
                    "thumbnail": _best_thumbnail(e),
                }
            )
        return {
            "type": "playlist",
            "title": info.get("title") or "?",
            "entries": entries,
        }

    formats = info.get("formats") or []
    return {
        "type": "video",
        "title": info.get("title") or "?",
        "uploader": info.get("uploader") or "?",
        "duration": int(info.get("duration") or 0),
        "thumbnail": info.get("thumbnail"),
        "video": _dedupe_video_formats(formats),
        "subtitles": _subtitle_list(info),
    }


def _audio_opts(choice: str) -> dict:
    # NOTE: "remux_video" only works as the --remux-video CLI argument; when
    # using yt-dlp as a library the postprocessor must be added manually,
    # otherwise it silently does nothing and the file stays in its original
    # container (e.g. webm).
    opts: dict = {"postprocessors": []}
    if choice == "opus":
        # NOTE: YouTube's audio is already Opus; remuxing only changes the
        # container, no re-encoding. Do NOT use
        # FFmpegExtractAudio(preferredcodec="opus").
        opts["format"] = "bestaudio[acodec=opus]/bestaudio[ext=webm]/bestaudio"
        opts["postprocessors"].append({"key": "FFmpegVideoRemuxer", "preferedformat": "opus"})
    elif choice == "m4a":
        opts["format"] = "bestaudio[ext=m4a]/bestaudio[acodec^=mp4a]/bestaudio"
        opts["postprocessors"].append({"key": "FFmpegVideoRemuxer", "preferedformat": "m4a"})
    elif choice == "mp3":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"].append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",
            }
        )
    else:
        raise ProbeError(f"Bilinmeyen ses secenegi: {choice}")

    opts["writethumbnail"] = True
    # NOTE: order matters - metadata/thumbnail must be added AFTER the container
    # conversion (remux/extract), otherwise EmbedThumbnail hits an unsupported
    # container like webm.
    opts["postprocessors"].append({"key": "FFmpegMetadata"})
    opts["postprocessors"].append({"key": "EmbedThumbnail"})
    return opts


def _subtitle_opts(lang_code: str) -> dict:
    return {
        "skip_download": True,
        "writesubtitles": True,
        "subtitleslangs": [lang_code],
        # NOTE: "when": "before_dl" is required - otherwise the converter runs
        # AFTER the main download stage and the subtitle file stays in its
        # original format (e.g. .vtt), never converting to .srt.
        "postprocessors": [{"key": "FFmpegSubtitlesConvertor", "format": "srt", "when": "before_dl"}],
    }


def _video_opts(format_id: str, subtitle_langs: Optional[list[str]] = None) -> dict:
    # NOTE: "best" is a sentinel (not a real yt-dlp format_id) used by channel
    # auto-download, where we can't probe a specific format_id per-video ahead
    # of time - it maps to a generic, always-valid selector instead.
    fmt = "bestvideo+bestaudio/best" if format_id == "best" else f"{format_id}+bestaudio/{format_id}"
    opts = {
        "format": fmt,
        "merge_output_format": "mp4",
        # NOTE: we embed a cover into video downloads too, so the history
        # list can show a thumbnail (mp4 supports EmbedThumbnail).
        "writethumbnail": True,
        "postprocessors": [
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail"},
        ],
    }
    if subtitle_langs:
        # NOTE: subtitles are deliberately NOT embedded into the mp4 - they
        # become separate .srt files sharing the same base name as the mp4
        # (e.g. "video.mp4" + "video.tr.srt"). Media players (VLC, mpv...)
        # auto-match this naming convention.
        opts["writesubtitles"] = True
        opts["subtitleslangs"] = subtitle_langs
        opts["postprocessors"].append({"key": "FFmpegSubtitlesConvertor", "format": "srt", "when": "before_dl"})
    return opts


def download(
    url: str,
    kind: str,
    choice: str,
    progress_hook: Callable[[dict], None],
    postprocessor_hook: Callable[[dict], None],
    subtitle_langs: Optional[list[str]] = None,
) -> str:
    if kind == "audio":
        opts = _audio_opts(choice)
    elif kind == "video":
        opts = _video_opts(choice, subtitle_langs)
    elif kind == "subtitle":
        opts = _subtitle_opts(choice)
    else:
        raise ProbeError(f"Bilinmeyen tur: {kind}")

    opts.update(
        {
            "outtmpl": OUTTMPL,
            "quiet": True,
            "no_warnings": True,
            "retries": 10,
            "fragment_retries": 10,
            "concurrent_fragment_downloads": 4,
            "progress_hooks": [progress_hook],
            "postprocessor_hooks": [postprocessor_hook],
            # NOTE: since the filename has no ID, re-requesting the same video
            # at a different quality lands on the same name; always re-download
            # and overwrite instead of silently returning the old file as
            # "already downloaded".
            "overwrites": True,
        }
    )

    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    if kind == "subtitle":
        entry = (info.get("requested_subtitles") or {}).get(choice)
        if entry and entry.get("filepath"):
            return entry["filepath"]
        raise ProbeError("Altyazi indirilemedi")

    for d in info.get("requested_downloads") or []:
        path = d.get("filepath") or d.get("_filename")
        if path:
            return path

    raise ProbeError("Indirilen dosya yolu bulunamadi")


def extract_thumbnail(path: str) -> Optional[bytes]:
    # NOTE: we don't keep a separate cover-art file; EmbedThumbnail already
    # embeds the cover into the file, so the history list's thumbnail is read
    # from here.
    try:
        audio = MutagenFile(path)
    except Exception:
        return None
    if audio is None:
        return None

    tags = getattr(audio, "tags", None)
    if tags:
        for key in tags.keys():
            if str(key).startswith("APIC"):
                return tags[key].data

    try:
        covers = audio["covr"]
        if covers:
            return bytes(covers[0])
    except Exception:
        pass

    try:
        raw = audio.get("metadata_block_picture") if hasattr(audio, "get") else None
        if raw:
            return Picture(base64.b64decode(raw[0])).data
    except Exception:
        pass

    return None


def _first_tag(tags, keys: tuple[str, ...]) -> Optional[str]:
    for key in keys:
        try:
            if key not in tags:
                continue
            val = tags[key]
            if hasattr(val, "text"):
                return str(val.text[0])
            if isinstance(val, list) and val:
                return str(val[0])
            return str(val)
        except Exception:
            continue
    return None


def _ffprobe_duration(path: str) -> Optional[int]:
    # NOTE: ffprobe is used instead of mutagen for duration. mutagen ESTIMATES
    # duration from bitrate for some MP3 files (especially ones missing a
    # Xing/VBR header), and that estimate can be wrong by hours (e.g. showing
    # "18 hours" for a 3-minute song). ffprobe actually reads the stream and
    # returns the real duration, so it's reliable.
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return int(float(result.stdout.strip()))
    except Exception:
        return None


def get_metadata(path: str) -> dict:
    # NOTE: for the history detail page - title/artist were already written
    # into the file by FFmpegMetadata, and are read back here via mutagen.
    try:
        audio = MutagenFile(path)
    except Exception:
        audio = None

    title = artist = None
    if audio is not None:
        tags = getattr(audio, "tags", None)
        if tags:
            title = _first_tag(tags, ("TIT2", "\xa9nam", "title", "TITLE"))
            artist = _first_tag(tags, ("TPE1", "\xa9ART", "artist", "ARTIST"))

    return {"title": title, "artist": artist, "duration": _ffprobe_duration(path)}


def reveal_in_explorer(path: str) -> None:
    # NOTE: since this is a locally-run tool, the request was to open the file
    # selected in the OS file explorer at the moment "Download file" is
    # clicked (not when the download job finishes - that used to pop open
    # explorer at "This PC"/Quick Access with nothing selected). If there's no
    # desktop environment, fail silently rather than failing the download.
    try:
        if sys.platform == "win32":
            # NOTE: passing ["explorer", "/select,X"] as a list makes Windows'
            # automatic quoting wrap "/select,X" into a SINGLE quoted token,
            # which explorer.exe fails to parse - it opened an empty window
            # instead of the selected file. Quoting the path directly inside a
            # single command-line string works correctly.
            subprocess.Popen(f'explorer /select,"{path}"')
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(path)])
    except Exception:
        pass
