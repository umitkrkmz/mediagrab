# The yt_dlp import must appear ONLY in this file. Other modules call this
# file's functions instead of touching the yt-dlp API directly.
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime
from typing import Callable, Optional

from yt_dlp import YoutubeDL
from yt_dlp.version import __version__ as YT_DLP_VERSION

from .paths import app_dir


class ProbeError(Exception):
    pass


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi_codes(text: str) -> str:
    # NOTE: yt-dlp colors its own error messages for terminal output (e.g.
    # "\x1b[0;31mERROR:\x1b[0m ..."). Those escape codes are meaningless
    # outside a terminal, so shown raw in the UI they just look like garbled
    # text - this strips them before an error message ever reaches the
    # frontend.
    return _ANSI_RE.sub("", text)


DOWNLOAD_DIR = os.path.join(app_dir(), "indirilenler")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# NOTE: the video ID is deliberately left out of the filename - removed at the
# user's request. The cost: re-downloading the same video at a different
# quality reuses the same filename and overwrites it (intentional, see
# "overwrites" below).
# NOTE: files are auto-organized into a per-channel/uploader subfolder.
# "%(uploader,channel,extractor)s" falls back through the field list (yt-dlp
# outtmpl syntax) so sites without a populated uploader/channel field still
# get a stable folder name (extractor is always present) instead of "NA".
# yt-dlp sanitizes each templated field for the filesystem automatically, the
# same way it already does for %(title)s.
OUTTMPL = os.path.join(DOWNLOAD_DIR, "%(uploader,channel,extractor)s", "%(title).120B.%(ext)s")


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
    # NOTE: keep only the highest-tbr variant per height. Only "none" (the
    # explicit "no video track" marker YouTube uses for audio-only formats)
    # is excluded - many non-YouTube extractors just leave vcodec unset
    # (None) on real video formats instead of populating it, so treating
    # None the same as "none" was wrongly hiding every video quality option
    # on those sites (e.g. archive.org).
    best_by_height: dict[int, dict] = {}
    for f in formats:
        if f.get("vcodec") == "none":
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


def _transcript_language(info: dict) -> Optional[dict]:
    # NOTE: unlike _subtitle_list (manual-only, for the timed .srt bundled
    # with a video download), a transcript is a plain-text read - it's most
    # useful precisely on videos that only have auto-generated captions, so
    # this falls back to automatic_captions when no manual track exists.
    # Only ONE language is offered (not the whole auto-translate list): the
    # video's own detected spoken language, since every other automatic_captions
    # entry is a machine-translated copy of that same original track.
    subs = info.get("subtitles") or {}
    if subs:
        lang = info.get("language")
        code = lang if lang in subs else next(iter(subs), None)
        if code:
            return {"code": code, "source": "manual"}

    auto = info.get("automatic_captions") or {}
    if auto:
        lang = info.get("language")
        code = lang if lang in auto else next(iter(auto), None)
        if code:
            return {"code": code, "source": "auto"}

    return None


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
        raise ProbeError(strip_ansi_codes(str(exc))) from exc

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
        raise ProbeError(strip_ansi_codes(str(exc))) from exc

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
        "transcript": _transcript_language(info),
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


def _transcript_opts(lang_code: str, source: str) -> dict:
    opts = {
        "skip_download": True,
        "subtitleslangs": [lang_code],
        "subtitlesformat": "vtt",
    }
    if source == "auto":
        opts["writeautomaticsub"] = True
    else:
        opts["writesubtitles"] = True
    return opts


_VTT_TAG_RE = re.compile(r"<[^>]+>")
_VTT_TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->")


def _vtt_to_text(vtt_path: str) -> str:
    # NOTE: YouTube's auto-generated captions are "rolling": each real cue
    # holds TWO physical lines - the previous cue's final line repeated
    # verbatim, then a second line with the words added so far - and is
    # followed by a near-zero-duration "transition" cue that repeats just
    # that second line again on its own. So at the LINE level (not cue
    # level), a line only ever gets fully repeated verbatim, never
    # partially - dropping consecutive exact-duplicate lines removes all of
    # that redundancy while keeping every new line of speech. Plain
    # (non-rolling) manual subtitles pass through unchanged since their
    # lines essentially never repeat like this.
    with open(vtt_path, "r", encoding="utf-8", errors="replace") as f:
        raw_lines = f.readlines()

    lines: list[str] = []
    for raw_line in raw_lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.upper().startswith(("WEBVTT", "KIND:", "LANGUAGE:", "NOTE", "STYLE")):
            continue
        if _VTT_TIME_RE.match(stripped) or stripped.isdigit():
            continue
        text = _VTT_TAG_RE.sub("", stripped).strip()
        if text:
            lines.append(text)

    output_lines: list[str] = []
    prev = None
    for line in lines:
        if line != prev:
            output_lines.append(line)
        prev = line

    return re.sub(r"\s+", " ", " ".join(output_lines)).strip()


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


def metadata_sidecar_path(media_path: str) -> str:
    base, _ext = os.path.splitext(media_path)
    return base + ".json"


def _format_upload_date(raw: Optional[str]) -> Optional[str]:
    # NOTE: yt-dlp gives upload_date as a raw "YYYYMMDD" string; reformat to
    # "YYYY-MM-DD" for readability in the exported sidecar.
    if not raw or len(raw) != 8:
        return raw
    return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"


def _write_metadata_sidecar(media_path: str, info: dict, kind: str, choice: str) -> None:
    # NOTE: a metadata export failure should never fail the download itself -
    # this is a best-effort archival extra, not the main deliverable.
    try:
        data = {
            "title": info.get("title"),
            "uploader": info.get("uploader") or info.get("channel"),
            "uploader_url": info.get("uploader_url") or info.get("channel_url"),
            "upload_date": _format_upload_date(info.get("upload_date")),
            "duration": info.get("duration"),
            "description": info.get("description"),
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
            "tags": info.get("tags") or [],
            "source_url": info.get("webpage_url") or info.get("original_url"),
            "extractor": info.get("extractor_key") or info.get("extractor"),
            "video_id": info.get("id"),
            "kind": kind,
            "format": choice,
            "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        }
        with open(metadata_sidecar_path(media_path), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


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
    elif kind == "transcript":
        # NOTE: choice is "<lang_code>:<manual|auto>", matching _transcript_language()'s output.
        lang_code, _, source = choice.partition(":")
        opts = _transcript_opts(lang_code, source)
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

    if kind == "transcript":
        lang_code, _, _source = choice.partition(":")
        entry = (info.get("requested_subtitles") or {}).get(lang_code)
        if not entry or not entry.get("filepath"):
            raise ProbeError("Transkript indirilemedi")
        vtt_path = entry["filepath"]
        text = _vtt_to_text(vtt_path)
        txt_path = os.path.splitext(vtt_path)[0] + ".txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        try:
            os.remove(vtt_path)
        except OSError:
            pass
        return txt_path

    for d in info.get("requested_downloads") or []:
        path = d.get("filepath") or d.get("_filename")
        if path:
            _write_metadata_sidecar(path, info, kind, choice)
            return path

    raise ProbeError("Indirilen dosya yolu bulunamadi")


def _ffprobe_json(path: str, entries: str) -> dict:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", entries, "-of", "json", path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return json.loads(result.stdout or "{}")
    except Exception:
        return {}


def extract_thumbnail(path: str) -> Optional[bytes]:
    # NOTE: we don't keep a separate cover-art file; EmbedThumbnail already
    # embeds the cover into the file as an "attached_pic" stream, so the
    # history list's thumbnail is read straight from there via
    # ffprobe/ffmpeg - no tag-parsing library (and its license) needed.
    data = _ffprobe_json(path, "stream=index:stream_disposition=attached_pic")
    stream_index = None
    for s in data.get("streams", []):
        if s.get("disposition", {}).get("attached_pic") == 1:
            stream_index = s["index"]
            break
    if stream_index is None:
        return None
    try:
        result = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", path, "-map", f"0:{stream_index}", "-c", "copy", "-f", "image2pipe", "-"],
            capture_output=True,
            timeout=15,
        )
        return result.stdout or None
    except Exception:
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
    # into the file by FFmpegMetadata, and are read back here via ffprobe
    # (container tag keys are case-insensitive in practice but ffprobe's
    # casing varies by container, so keys are lowercased before lookup).
    data = _ffprobe_json(path, "format_tags=title,artist")
    tags = {k.lower(): v for k, v in (data.get("format", {}).get("tags") or {}).items()}
    return {"title": tags.get("title"), "artist": tags.get("artist"), "duration": _ffprobe_duration(path)}


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


def _parse_version(v: str) -> tuple:
    try:
        return tuple(int(part) for part in v.split("."))
    except ValueError:
        return ()


def check_ytdlp_update() -> dict:
    # NOTE: yt-dlp versions are dates ("2026.07.04"), but yt_dlp.version's
    # copy keeps the zero-padding while PyPI's JSON API normalizes it
    # per PEP 440 ("2026.7.4") - a plain string compare treats those as
    # DIFFERENT versions (since "7" > "07" as text), falsely flagging every
    # up-to-date install as outdated. Parsing into int tuples compares them
    # numerically instead, where 2026.07.04 == 2026.7.4 as expected.
    result = {"installed": YT_DLP_VERSION, "latest": None, "update_available": None}
    try:
        with urllib.request.urlopen("https://pypi.org/pypi/yt-dlp/json", timeout=5) as resp:
            data = json.loads(resp.read())
        latest = data["info"]["version"]
        result["latest"] = latest
        result["update_available"] = _parse_version(latest) > _parse_version(YT_DLP_VERSION)
    except Exception:
        # NOTE: no internet / PyPI unreachable - the caller shows a neutral
        # "couldn't check" message rather than failing the whole page.
        pass
    return result


def update_ytdlp() -> dict:
    # NOTE: sys.executable is THIS process's own Python interpreter, which is
    # already inside the user's active venv - no need to spawn a shell,
    # activate anything, or guess a path. Installing "in place" like this is
    # safe because pip only replaces files on disk; the already-imported
    # yt_dlp module in memory is untouched until the process restarts.
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "ok": result.returncode == 0,
            "output": ((result.stdout or "") + (result.stderr or "")).strip(),
        }
    except Exception as exc:
        return {"ok": False, "output": str(exc)}
