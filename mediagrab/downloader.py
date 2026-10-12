# The yt_dlp import must appear ONLY in this file. Other modules call this
# file's functions instead of touching the yt-dlp API directly.
import glob
import io
import json
import os
import re
import subprocess
import sys
import threading
import urllib.request
from datetime import datetime, timezone
from typing import Callable, Optional

from yt_dlp import YoutubeDL as _YtDlpYoutubeDL
from yt_dlp.cookies import YoutubeDLCookieJar
from yt_dlp.version import __version__ as YT_DLP_VERSION

from .paths import data_dir, default_download_dir, is_docker

# NOTE: guards every write to a cookies.txt - a yt-dlp run writing refreshed
# cookies back (YoutubeDL.save_cookies below) and an upload replacing the file
# (save_uploaded_cookies) - so one can't land in the middle of the other.
_cookie_file_lock = threading.Lock()


def _file_signature(path: Optional[str]):
    """(mtime_ns, size) of a file, or None if it doesn't exist."""
    if not path:
        return None
    try:
        st = os.stat(path)
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size)


class YoutubeDL(_YtDlpYoutubeDL):
    """yt-dlp's YoutubeDL, except it never overwrites a cookies.txt that changed under it.

    NOTE: yt-dlp writes its cookie jar back to `cookiefile` when it closes
    (that's how refreshed YouTube cookies get kept). But a download can run
    for minutes - if the user uploads a NEW cookies.txt meanwhile, the old
    run's close would write its stale jar straight over the new upload. So
    each run notes the file's signature when it starts, and only writes back
    if the file is still exactly what it started from. Anything else - a new
    upload, the file being deleted, another run having written first - wins.
    Every call site in this module uses this class simply by name.
    """

    def __init__(self, params=None, *args, **kwargs):
        self._cookie_file_signature = _file_signature((params or {}).get("cookiefile"))
        super().__init__(params, *args, **kwargs)

    def save_cookies(self):
        path = self.params.get("cookiefile")
        if path is None:
            return
        with _cookie_file_lock:
            current = _file_signature(path)
            # NOTE: "None" (no file now) is never written either - deleted
            # cookies stay deleted, a run can't quietly bring them back.
            if current is None or current != self._cookie_file_signature:
                return
            super().save_cookies()


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


# NOTE: the DEFAULT downloads folder; Settings -> Download folder can point
# elsewhere, so everything that reads or writes downloads asks
# download_dir() instead of using this directly.
DOWNLOAD_DIR = default_download_dir()
try:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
except OSError:
    pass


def download_dir() -> str:
    """The downloads folder in effect right now (the setting, else DOWNLOAD_DIR)."""
    # NOTE: imported here, not at the top - see cookie_opts() for why
    # store.py and this module only depend one way.
    from . import store

    folder = DOWNLOAD_DIR
    if not is_docker():
        # NOTE: in Docker the compose file's volume decides; a path that
        # arrived some other way (an old settings file) can't apply there.
        folder = store.get_settings().get("download_dir") or DOWNLOAD_DIR
    try:
        os.makedirs(folder, exist_ok=True)
    except OSError:
        # NOTE: e.g. an unplugged USB drive - the download itself then fails
        # with a clear "path not found" instead of this crashing every page.
        pass
    return folder

# NOTE: where an UPLOADED cookies.txt lives (Settings -> Cookies). Never
# inside DOWNLOAD_DIR - that folder is listed by History and served to
# remote devices. In Docker it's its own volume-mounted folder (see
# docker-compose.yml) so it survives the container being recreated; from
# source it sits next to settings.json (and is gitignored, like it).
COOKIES_PATH = (
    "/data/cookies/cookies.txt" if is_docker() else os.path.join(data_dir(), "cookies.txt")
)

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
OUTTMPL_TAIL = os.path.join("%(uploader,channel,extractor)s", "%(title).120B.%(ext)s")


def outtmpl() -> str:
    # NOTE: built per download, not once at import - the folder can change in
    # Settings while the app runs.
    return os.path.join(download_dir(), OUTTMPL_TAIL)


def _console_attached() -> bool:
    """True when stdout is a real terminal someone is watching.

    NOTE: yt-dlp draws its own "[download] 45%" line even with quiet=True,
    redrawn in place with \\r. Fine in a console window; but from the Windows
    installer (pythonw: stdout is mediagrab.log) and in Docker (docker logs)
    every redraw piles up - one download left a single ~300 KB line in the
    log. MediaGrab's own progress bar comes from progress_hooks, which keep
    working with noprogress; errors and warnings are unaffected.
    """
    try:
        return bool(sys.stdout and sys.stdout.isatty())
    except (AttributeError, ValueError):
        return False


# NOTE: the browsers yt-dlp can read cookies from at all. Firefox is listed
# first and is the default on purpose - see usable_cookie_browsers().
SUPPORTED_COOKIE_BROWSERS = ("firefox", "chrome", "chromium", "edge", "brave", "opera", "vivaldi", "safari")


def usable_cookie_browsers(platform: Optional[str] = None) -> tuple:
    """The browsers whose cookies can actually be read on this OS."""
    # NOTE: on Windows, Chromium-based browsers (Chrome 127+, Edge, Brave...)
    # protect cookies with App-Bound Encryption, which only the browser itself
    # can undo - yt-dlp fails with "Could not copy Chrome cookie database" or a
    # DPAPI error. And it fails on EVERY download, not just the ones that need
    # a login, so offering these there only ever breaks things (confirmed on a
    # real machine). Firefox stores its cookies unencrypted and just works.
    # Elsewhere Chromium works (Keychain / keyring); Safari exists only on macOS.
    platform = platform or sys.platform
    if platform == "win32":
        return ("firefox",)
    if platform == "darwin":
        return SUPPORTED_COOKIE_BROWSERS
    return tuple(b for b in SUPPORTED_COOKIE_BROWSERS if b != "safari")


def cookie_opts() -> dict:
    """yt-dlp options for the configured cookie source (empty when off)."""
    # NOTE: imported here rather than at module scope to keep the dependency
    # one-directional - store.py has no business importing the downloader.
    from . import store

    settings = store.get_settings()
    mode = settings.get("cookie_mode", "off")

    if mode == "browser":
        browser = settings.get("cookie_browser") or "firefox"
        # NOTE: a browser saved before it was filtered out on this OS (e.g.
        # "chrome" on Windows) means "no cookies" rather than a hard failure
        # of every single download - Settings shows why.
        if browser not in usable_cookie_browsers():
            return {}
        # NOTE: the tuple is (browser, profile, keyring, container) - only the
        # browser name is set, letting yt-dlp find the default profile.
        return {"cookiesfrombrowser": (browser, None, None, None)}

    if mode == "file":
        path = settings.get("cookie_file") or ""
        # NOTE: a missing file makes yt-dlp fail the whole download with a
        # confusing error, so a bad path simply means "no cookies" instead.
        # The Settings page validates and reports it properly.
        if path and os.path.isfile(path):
            return {"cookiefile": path}
        return {}

    return {}


def speed_limit_opts() -> dict:
    """yt-dlp options for the configured download speed cap (empty when unlimited)."""
    # NOTE: same one-directional import as cookie_opts() above.
    from . import store

    settings = store.get_settings()
    mbps = settings.get("download_speed_limit_mbps", 0)
    if not mbps or mbps <= 0:
        return {}
    # NOTE: yt-dlp's own option is bytes/sec; settings.json stores MB/s for
    # human readability (see store.py's DEFAULT_SETTINGS).
    return {"ratelimit": mbps * 1024 * 1024}


def test_cookie_source() -> dict:
    """Check the configured cookie source actually loads, without downloading."""
    # NOTE: worth its own endpoint because a broken cookie source otherwise
    # only shows up as a failed download much later, with a message that
    # doesn't obviously point at cookies.
    from . import store

    settings = store.get_settings()
    if settings.get("cookie_mode") == "browser":
        browser = settings.get("cookie_browser") or "firefox"
        if browser not in usable_cookie_browsers():
            return {"ok": False, "reason": "unsupported_browser", "browser": browser}
    opts = cookie_opts()
    if not opts:
        return {"ok": False, "reason": "not_configured"}
    try:
        with YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True, **opts}) as ydl:
            jar = ydl.cookiejar
        return {"ok": True, "count": len(jar)}
    except Exception as exc:
        return {"ok": False, "reason": "error", "detail": strip_ansi_codes(str(exc))[:300]}


# --- uploaded cookies.txt -----------------------------------------------------

# NOTE: a youtube.com-only export is a few KB and even "Export All Cookies"
# from a busy browser stays well under 1 MB - anything bigger isn't a cookie
# file, and the whole thing is held in memory while parsing.
COOKIES_MAX_BYTES = 5 * 1024 * 1024

# NOTE: sites pre-ticked when an upload is reviewed - YouTube's own session
# cookies live on youtube.com, and the Google account login it depends on on
# google.com (or a country domain such as google.com.tr). Everything else in
# the file starts unticked, so an "Export All Cookies" file doesn't quietly
# store the user's bank/mail/social sessions next to MediaGrab.
_DEFAULT_COOKIE_SITES = ("youtube.com", "google.")

# NOTE: the same rule yt-dlp's YouTube extractor uses to decide it's signed
# in (YoutubeBaseInfoExtractor._has_auth_cookies): LOGIN_INFO plus at least
# one SAPISID variant. LOGIN_INFO matters because YouTube clears it when it
# rotates/rejects a session but leaves __Secure-3PAPISID behind - a SAPISID
# alone is what a dead session looks like (seen live after a write-back).
_YOUTUBE_SAPISID_COOKIES = {"SAPISID", "__Secure-1PAPISID", "__Secure-3PAPISID"}

# NOTE: second-level labels under which a country code is the real suffix
# ("bbc.co.uk", "google.com.tr") - a small stand-in for the full Public
# Suffix List, which is only used here to group cookies for display, never
# for any security decision.
_SECOND_LEVEL_LABELS = {"co", "com", "net", "org", "gov", "edu", "ac", "or", "ne", "go"}


class CookieFileError(ValueError):
    """An uploaded cookies.txt was rejected; str(exc) is a short reason code."""


def cookie_site(domain: str) -> str:
    """Group a cookie domain under its site: ".m.youtube.com" -> "youtube.com"."""
    labels = [part for part in domain.lower().lstrip(".").split(".") if part]
    if len(labels) <= 2:
        return ".".join(labels)
    if len(labels[-1]) == 2 and labels[-2] in _SECOND_LEVEL_LABELS:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def parse_cookie_text(text: str) -> YoutubeDLCookieJar:
    """Parse cookies.txt content with yt-dlp's OWN reader, or raise CookieFileError."""
    # NOTE: yt-dlp's reader rather than our own parser on purpose - a file
    # that passes here is, by construction, a file yt-dlp will accept when it
    # later downloads with it (#HttpOnly_ lines, session cookies and all).
    if len(text.encode("utf-8")) > COOKIES_MAX_BYTES:
        raise CookieFileError("too_large")
    stripped = text.lstrip("﻿").strip()
    if not stripped:
        raise CookieFileError("empty")
    if stripped[0] in "[{":
        raise CookieFileError("json")
    # NOTE: browsers hand FileReader text over with the file's own line
    # endings, and yt-dlp's reader only strips "\n" - a Windows "\r\n" file
    # would otherwise leave "\r" glued to the end of every cookie VALUE.
    normalized = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    jar = YoutubeDLCookieJar()
    try:
        jar.load(io.StringIO(normalized))
    except Exception:
        raise CookieFileError("not_netscape") from None
    if not len(jar):
        raise CookieFileError("no_cookies")
    return jar


def summarize_cookie_jar(jar) -> dict:
    """Per-site counts - names and values never leave this function."""
    counts: dict[str, int] = {}
    youtube_names = set()
    for cookie in jar:
        site = cookie_site(cookie.domain)
        counts[site] = counts.get(site, 0) + 1
        if site == "youtube.com":
            youtube_names.add(cookie.name)
    youtube_signed_in = "LOGIN_INFO" in youtube_names and bool(youtube_names & _YOUTUBE_SAPISID_COOKIES)
    sites = [{"site": site, "count": n} for site, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]
    return {"sites": sites, "total": sum(counts.values()), "youtube_signed_in": youtube_signed_in}


def inspect_cookie_text(text: str) -> dict:
    """What an upload contains, plus which sites to pre-tick - nothing is saved."""
    summary = summarize_cookie_jar(parse_cookie_text(text))
    summary["suggested"] = [
        s["site"] for s in summary["sites"] if s["site"].startswith(_DEFAULT_COOKIE_SITES)
    ]
    return summary


def save_uploaded_cookies(text: str, sites: list[str]) -> dict:
    """Keep only the chosen sites' cookies and write them to COOKIES_PATH."""
    jar = parse_cookie_text(text)
    wanted = {s.lower() for s in sites}
    kept = YoutubeDLCookieJar()
    for cookie in jar:
        if cookie_site(cookie.domain) in wanted:
            kept.set_cookie(cookie)
    if not len(kept):
        raise CookieFileError("nothing_selected")

    folder = os.path.dirname(COOKIES_PATH)
    os.makedirs(folder, exist_ok=True)
    # NOTE: written beside the target and swapped in with os.replace, so a
    # crash mid-write can never leave a half-written file where yt-dlp would
    # read it - the previous upload simply stays in place. Written by yt-dlp's
    # own save() for the same reason the reader is yt-dlp's (see above).
    tmp_path = COOKIES_PATH + ".tmp"
    with _cookie_file_lock:
        try:
            kept.save(tmp_path)
            if os.name == "posix":
                # NOTE: these are live login sessions - owner-only, like an SSH key.
                os.chmod(tmp_path, 0o600)
            os.replace(tmp_path, COOKIES_PATH)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    return summarize_cookie_jar(kept)


def cookie_file_summary(path: str) -> Optional[dict]:
    """Summary of a cookies.txt already on disk, or None if it can't be read."""
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            summary = summarize_cookie_jar(parse_cookie_text(f.read()))
    except (OSError, CookieFileError):
        return None
    # NOTE: timezone-aware on purpose - a container runs in UTC, and a naive
    # timestamp would be read by the browser as the viewer's LOCAL time
    # (showing an upload as hours old). With the offset, the browser converts.
    mtime = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
    summary["updated_at"] = mtime.isoformat(timespec="seconds")
    return summary


def delete_uploaded_cookies() -> bool:
    """Remove the uploaded file. Only ever COOKIES_PATH - never a user's own file."""
    with _cookie_file_lock:
        try:
            os.remove(COOKIES_PATH)
            return True
        except FileNotFoundError:
            return False


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


def _dedupe_video_formats(formats: list[dict], duration: int = 0) -> list[dict]:
    # NOTE: keep only the highest-tbr variant per height. Only "none" (the
    # explicit "no video track" marker YouTube uses for audio-only formats)
    # is excluded - many non-YouTube extractors just leave vcodec unset
    # (None) on real video formats instead of populating it, so treating
    # None the same as "none" was wrongly hiding every video quality option
    # on those sites (e.g. archive.org).
    best_by_height: dict[int, dict] = {}
    # NOTE: some manifest-only formats (no filesize/filesize_approx at all)
    # report a tbr wildly higher than any sibling at the same height that DOES
    # have a confirmed size - on a real video, one 1080p entry's tbr was
    # ~3x every other 1080p format's, despite none of them having a real
    # reason to differ that much (same codec family, same fps). That tbr
    # looks like a rough ceiling YouTube hasn't refined yet, not a usable
    # average - so it's tracked separately as a sanity cap for the estimate.
    max_known_size_by_height: dict[int, int] = {}
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
        known_size = f.get("filesize") or f.get("filesize_approx")
        if known_size:
            max_known_size_by_height[height] = max(known_size, max_known_size_by_height.get(height, 0))

    result = []
    for height in sorted(best_by_height.keys(), reverse=True):
        f = best_by_height[height]
        size = f.get("filesize") or f.get("filesize_approx")
        size_bytes = int(size) if size else None
        size_label = human_size(size)
        if not size:
            # NOTE: tbr (average kbps) times the video's duration gives a
            # rough total when nothing better is available. Prefixed with "~"
            # so it reads as an estimate, not a reported fact.
            tbr = f.get("tbr")
            if tbr and duration:
                estimate = tbr * 1000 / 8 * duration
                known_ceiling = max_known_size_by_height.get(height)
                if known_ceiling:
                    estimate = min(estimate, known_ceiling)
                size_label = f"~{human_size(estimate)}"
                size_bytes = int(estimate)
        vcodec = (f.get("vcodec") or "?").split(".")[0]
        result.append(
            {
                "format_id": f["format_id"],
                "label": f"{height}p",
                "ext": f.get("ext", "?"),
                "vcodec": vcodec,
                "size": size_label,
                # NOTE: the raw byte count behind `size` above (real or
                # estimated) - kept separately so app.py's disk-space check
                # (see /api/download) can compare against actual free space
                # without re-deriving it from the human-readable string.
                "size_bytes": size_bytes,
            }
        )
    return result


def _audio_track_list(formats: list[dict]) -> list[dict]:
    # NOTE: only meaningful when a video ships more than one language dub
    # (YouTube exposes each as a separate audio-only format sharing a
    # "language" code). yt-dlp marks the original with a higher
    # language_preference than any dub - confirmed on a real 18-language
    # video, where English (the original) carried pref=10 and every dub -1.
    langs: dict[str, float] = {}
    for f in formats:
        if f.get("vcodec") != "none" or f.get("format_note") == "storyboard":
            continue
        lang = f.get("language")
        if not lang:
            continue
        pref = f.get("language_preference") or -1
        langs[lang] = max(pref, langs.get(lang, pref))

    if len(langs) < 2:
        return []
    default_lang = max(langs, key=langs.get)
    return sorted(
        [{"code": code, "is_default": code == default_lang} for code in langs],
        key=lambda t: t["code"],
    )


def _subtitle_list(info: dict) -> list[dict]:
    # NOTE: manually-provided subtitles are listed first when present.
    # Automatic captions (automatic_captions) are deliberately NOT listed
    # alongside them - YouTube's auto-translate feature means that dict can
    # hold dozens of languages, which would bloat the list pointlessly.
    subs = info.get("subtitles") or {}
    if subs:
        result = [{"code": code, "source": "manual"} for code, tracks in subs.items() if tracks]
        result.sort(key=lambda s: s["code"])
        return result

    # NOTE: falls back to a single auto-generated caption (the video's own
    # spoken language, same selection as _transcript_language()) when there's
    # no manual subtitle at all - many videos (podcasts, talk shows) only
    # have auto captions, and previously those users had no downloadable
    # subtitle option at all, only the plain-text transcript.
    auto = info.get("automatic_captions") or {}
    if auto:
        lang = info.get("language")
        code = lang if lang in auto else next(iter(auto), None)
        if code:
            return [{"code": code, "source": "auto"}]
    return []


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
        **cookie_opts(),
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
        **cookie_opts(),
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


class _CookieHintLogger:
    """Collects the yt-dlp messages that explain WHY a sign-in-gated video failed.

    NOTE: yt-dlp states the two most useful reasons only as side messages -
    the exception itself just says "Sign in to confirm your age" either way:
      - its cookies were sent but YouTube rejected them (rotated/expired),
      - the cookies are fine but YouTube wants the ACCOUNT age-verified
        (something only the user can do, on YouTube - no new cookies.txt
        will ever fix it).
    With a logger set, yt-dlp routes both screen messages and warnings here
    regardless of "quiet" (see YoutubeDL.to_screen/report_warning), so this
    sees them without any console output coming back.
    """

    _PATTERNS = ("account cookies are no longer valid", "requiring account age-verification")

    def __init__(self):
        self.hints: list[str] = []

    def _check(self, message: str) -> None:
        clean = strip_ansi_codes(str(message)).strip()
        if any(p in clean.lower() for p in self._PATTERNS) and clean not in self.hints:
            self.hints.append(clean)

    debug = info = warning = _check

    def error(self, message: str) -> None:
        # NOTE: the error itself arrives as the raised exception anyway.
        pass


def probe(url: str) -> dict:
    hint_logger = _CookieHintLogger()
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        # NOTE: without extract_flat, a playlist link tries to fetch full info
        # (including formats) for EVERY video before it even knows it's a
        # playlist (very slow). "in_playlist" gives a fast listing (id/title/
        # duration/thumbnail); format resolution happens once the user picks a video.
        "extract_flat": "in_playlist",
        "logger": hint_logger,
        **cookie_opts(),
    }
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        message = strip_ansi_codes(str(exc))
        # NOTE: appended as yt-dlp's own English lines - the page matches them
        # to a specific explanation (app.js ERROR_PATTERNS) and still shows
        # them verbatim under "technical details".
        if hint_logger.hints:
            message = "\n".join([message, *hint_logger.hints])
        raise ProbeError(message) from exc

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
    # NOTE: a probe can SUCCEED and still be badly degraded - seen live with
    # an age-restricted video and an account YouTube wanted age-verified:
    # only format 18 (360p, audio+video muxed) came back, so Opus/M4A (which
    # need a separate audio stream) failed with yt-dlp's raw "Requested
    # format is not available", and MP3 was quietly re-encoded from 360p
    # video audio. "audio_only" lets the page grey those choices out up
    # front, "notices" lets it say why.
    audio_only = any(
        f.get("vcodec") == "none" and f.get("acodec") not in (None, "none") for f in formats
    )
    notices = []
    if any("requiring account age-verification" in h.lower() for h in hint_logger.hints):
        notices.append("account_age_verification")
    return {
        "type": "video",
        "title": info.get("title") or "?",
        "uploader": info.get("uploader") or "?",
        "duration": int(info.get("duration") or 0),
        "thumbnail": info.get("thumbnail"),
        "description": info.get("description") or "",
        "video": _dedupe_video_formats(formats, int(info.get("duration") or 0)),
        "subtitles": _subtitle_list(info),
        "transcript": _transcript_language(info),
        "audio_tracks": _audio_track_list(formats),
        "audio_only": audio_only,
        "notices": notices,
    }


def _audio_opts(choice: str, audio_lang: str = "") -> dict:
    # NOTE: "remux_video" only works as the --remux-video CLI argument; when
    # using yt-dlp as a library the postprocessor must be added manually,
    # otherwise it silently does nothing and the file stays in its original
    # container (e.g. webm).
    opts: dict = {"postprocessors": []}
    # NOTE: when a language is requested, it's tried WITH the preferred codec
    # first, then alone (any codec), before falling back to the original,
    # language-agnostic chain - so an unavailable dub degrades to "best audio
    # in some language" rather than failing the whole download. Left out
    # entirely when audio_lang is empty, so the selector string here is
    # byte-for-byte the same as before this feature existed.
    lang = f"[language={audio_lang}]" if audio_lang else ""
    if choice == "opus":
        # NOTE: YouTube's audio is already Opus; remuxing only changes the
        # container, no re-encoding. Do NOT use
        # FFmpegExtractAudio(preferredcodec="opus").
        opts["format"] = (
            f"bestaudio[acodec=opus]{lang}/bestaudio{lang}/bestaudio[acodec=opus]/bestaudio[ext=webm]/bestaudio"
            if lang
            else "bestaudio[acodec=opus]/bestaudio[ext=webm]/bestaudio"
        )
        opts["postprocessors"].append({"key": "FFmpegVideoRemuxer", "preferedformat": "opus"})
    elif choice == "m4a":
        opts["format"] = (
            f"bestaudio[ext=m4a]{lang}/bestaudio{lang}/bestaudio[ext=m4a]/bestaudio[acodec^=mp4a]/bestaudio"
            if lang
            else "bestaudio[ext=m4a]/bestaudio[acodec^=mp4a]/bestaudio"
        )
        opts["postprocessors"].append({"key": "FFmpegVideoRemuxer", "preferedformat": "m4a"})
    elif choice == "mp3":
        opts["format"] = f"bestaudio{lang}/bestaudio/best" if lang else "bestaudio/best"
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


def _subtitle_opts(choice: str) -> dict:
    # NOTE: choice is "<lang_code>:<manual|auto>", matching _subtitle_list()'s output.
    lang_code, _, source = choice.partition(":")
    opts = {
        "skip_download": True,
        "subtitleslangs": [lang_code],
        # NOTE: "when": "before_dl" is required - otherwise the converter runs
        # AFTER the main download stage and the subtitle file stays in its
        # original format (e.g. .vtt), never converting to .srt.
        "postprocessors": [{"key": "FFmpegSubtitlesConvertor", "format": "srt", "when": "before_dl"}],
    }
    if source == "auto":
        opts["writeautomaticsub"] = True
    else:
        opts["writesubtitles"] = True
    return opts


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
_VTT_TIME_RE = re.compile(r"^(\d{2}:\d{2}:\d{2})[.,]\d{3}\s*-->")


def _vtt_to_text(vtt_path: str, timestamps: bool = False) -> str:
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

    entries: list[tuple[str, str]] = []
    current_ts = "00:00:00"
    for raw_line in raw_lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.upper().startswith(("WEBVTT", "KIND:", "LANGUAGE:", "NOTE", "STYLE")):
            continue
        time_match = _VTT_TIME_RE.match(stripped)
        if time_match:
            current_ts = time_match.group(1)
            continue
        if stripped.isdigit():
            continue
        text = _VTT_TAG_RE.sub("", stripped).strip()
        if text:
            entries.append((current_ts, text))

    deduped: list[tuple[str, str]] = []
    prev = None
    for ts, text in entries:
        if text != prev:
            deduped.append((ts, text))
        prev = text

    if not timestamps:
        return re.sub(r"\s+", " ", " ".join(text for _, text in deduped)).strip()

    return "\n".join(f"[{ts}] {text}" for ts, text in deduped)


def _video_opts(
    format_id: str, subtitle_langs: Optional[list[str]] = None, audio_langs: Optional[list[str]] = None
) -> dict:
    # NOTE: "best" is a sentinel (not a real yt-dlp format_id) used by channel
    # auto-download, where we can't probe a specific format_id per-video ahead
    # of time - it maps to a generic, always-valid selector instead. Channel
    # auto-download never passes more than one language here (multi-track is
    # manual-download only), so the "best" sentinel never has to deal with it.
    langs = [lang for lang in (audio_langs or []) if lang]
    multi_track = len(langs) >= 2

    if multi_track:
        # NOTE: yt-dlp collapses a "+"-joined multi-audio selector down to a
        # single stream unless allow_multiple_audio_streams is set (below) -
        # and even then, the merge step itself writes no language tags at
        # all; every downloaded audio-only fragment carries whatever generic
        # tag YouTube baked into it, regardless of actual dub language. Only
        # FFmpegMetadata (already in postprocessors) corrects each stream's
        # tag afterwards from yt-dlp's own per-format language data -
        # verified on a real video: without it, two genuinely different-
        # language tracks both showed up tagged "eng".
        audio_sel = "+".join(f"bestaudio[language={lang}]" for lang in langs)
        fmt = f"{format_id}+{audio_sel}/{format_id}+bestaudio"
    else:
        # NOTE: falls back to plain "bestaudio" if the requested dub isn't
        # there, rather than failing the download over a missing language.
        audio_sel = f"bestaudio[language={langs[0]}]/bestaudio" if langs else "bestaudio"
        # NOTE: the final fallback used to be bare "{format_id}" - which
        # ALWAYS resolves (it's just the video format matching itself) even
        # when neither audio_sel alternative found anything to merge with, so
        # it could silently ship a video with no sound at all. This has been
        # observed for real: probe() and download() each re-extract formats
        # independently (download() re-fetches fresh, well after the user
        # picked a quality), so a transient hiccup that drops every audio-only
        # format between the two calls previously produced a silent MP4
        # instead of an error. "best" still requires an actual audio track
        # (falling back to a combined format, or failing loudly if the video
        # truly has none) - see the "best" sentinel branch just above, which
        # already used this safer pattern.
        fmt = f"bestvideo+{audio_sel}/best" if format_id == "best" else f"{format_id}+{audio_sel}/best"

    opts = {
        "format": fmt,
        # NOTE: MKV only when multiple audio tracks are actually requested -
        # MP4 can technically hold more than one audio track too, but MKV is
        # the format multi-track players and other multi-dub releases expect,
        # and it keeps the single-track path's output exactly as before.
        "merge_output_format": "mkv" if multi_track else "mp4",
        # NOTE: we embed a cover into video downloads too, so the history
        # list can show a thumbnail (mp4/mkv both support EmbedThumbnail).
        "writethumbnail": True,
        "postprocessors": [
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail"},
        ],
    }
    if multi_track:
        opts["allow_multiple_audio_streams"] = True
    if subtitle_langs:
        # NOTE: subtitles are deliberately NOT embedded into the mp4 - they
        # become separate .srt files sharing the same base name as the mp4
        # (e.g. "video.mp4" + "video.tr.srt"). Media players (VLC, mpv...)
        # auto-match this naming convention.
        #
        # Each entry is "<lang_code>:<manual|auto>" (matching _subtitle_list()'s
        # output). A video only ever offers one source type at a time (auto is
        # only listed when there's no manual track at all), so it's safe to
        # decide writesubtitles vs writeautomaticsub from whether ANY selected
        # entry is auto, rather than needing a separate list per source.
        codes = []
        use_auto = False
        for entry in subtitle_langs:
            code, _, source = entry.partition(":")
            codes.append(code)
            if source == "auto":
                use_auto = True
        opts["subtitleslangs"] = codes
        if use_auto:
            opts["writeautomaticsub"] = True
        else:
            opts["writesubtitles"] = True
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


# NOTE: also read by app.py's startup sweep, which restores backups left
# behind when the process died before it could put them back itself.
BACKUP_SUFFIX = ".mediagrab-bak"


def _backup_existing_outputs(ydl, url: str) -> list[tuple[str, str]]:
    """Move files this download is about to replace out of the way.

    Returns (backup_path, original_path) pairs. Failing to work out the name
    is never fatal - we just lose the safety net and behave as before.
    """
    try:
        # NOTE: a metadata-only resolve (no download) purely to learn the
        # output path. It costs one extra request, which is small next to the
        # download itself and buys protection against losing an existing file.
        pre = ydl.extract_info(url, download=False)
        if not pre or pre.get("_type") == "playlist":
            return []
        stem = os.path.splitext(ydl.prepare_filename(pre))[0]
    except Exception:
        return []

    backups: list[tuple[str, str]] = []
    # NOTE: globbing the stem rather than one exact filename on purpose - the
    # real extension isn't known yet (merge_output_format and the audio
    # postprocessors change it), and one download can own several files:
    # video.mp4, video.tr.srt, video.json, video.webp.
    for path in glob.glob(glob.escape(stem) + ".*"):
        name = os.path.basename(path)
        if not os.path.isfile(path) or name.endswith(BACKUP_SUFFIX):
            continue
        if ".part" in name or name.endswith(".ytdl"):
            continue
        backup = path + BACKUP_SUFFIX
        try:
            if os.path.exists(backup):
                os.remove(backup)
            os.replace(path, backup)
            backups.append((backup, path))
        except OSError:
            # NOTE: couldn't move it aside (locked?) - leave it be rather than
            # blocking the download the user asked for.
            pass
    return backups


def _restore_backups(backups: list[tuple[str, str]]) -> None:
    for backup, original in backups:
        if not os.path.isfile(backup):
            continue
        try:
            # NOTE: whatever the failed attempt left at the target is worthless
            # - the backup is the file the user actually still has.
            os.replace(backup, original)
        except OSError:
            pass


def _discard_backups(backups: list[tuple[str, str]]) -> None:
    for backup, _original in backups:
        if not os.path.isfile(backup):
            continue
        try:
            os.remove(backup)
        except OSError:
            pass


def download(
    url: str,
    kind: str,
    choice: str,
    progress_hook: Callable[[dict], None],
    postprocessor_hook: Callable[[dict], None],
    subtitle_langs: Optional[list[str]] = None,
    audio_langs: Optional[list[str]] = None,
) -> str:
    audio_langs = [lang for lang in (audio_langs or []) if lang]
    if kind == "audio":
        # NOTE: multi-track only makes sense embedded in a video - a plain
        # audio file (mp3/m4a/opus) can't meaningfully hold more than one
        # selectable track, so only the first requested language applies here.
        opts = _audio_opts(choice, audio_langs[0] if audio_langs else "")
    elif kind == "video":
        opts = _video_opts(choice, subtitle_langs, audio_langs)
    elif kind == "subtitle":
        opts = _subtitle_opts(choice)
    elif kind == "transcript":
        # NOTE: choice is "<lang_code>:<manual|auto>:<ts|plain>" - the first
        # two segments match _transcript_language()'s output, the third is
        # the timestamp toggle from the UI checkbox.
        lang_code, _, rest = choice.partition(":")
        source, _, _fmt = rest.partition(":")
        opts = _transcript_opts(lang_code, source)
    else:
        raise ProbeError(f"Bilinmeyen tur: {kind}")

    opts.update(
        {
            "outtmpl": outtmpl(),
            "quiet": True,
            "no_warnings": True,
            "noprogress": not _console_attached(),
            "retries": 10,
            "fragment_retries": 10,
            "concurrent_fragment_downloads": 4,
            # NOTE: cookies apply to the download too, not just the probe -
            # age-gated or members-only media needs them at both stages.
            **cookie_opts(),
            **speed_limit_opts(),
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
        # NOTE: "overwrites" makes yt-dlp delete an existing output file at the
        # START of the download, not at the end (verified). So any failure
        # afterwards - a cancel, an HTTP 403, a dropped connection, closing the
        # app - used to leave the user with neither the new file nor the old
        # one. Resolving the output name up front lets us move anything already
        # there aside and put it back if this attempt doesn't finish.
        backups = _backup_existing_outputs(ydl, url)
        try:
            info = ydl.extract_info(url, download=True)
        except Exception:
            _restore_backups(backups)
            raise

    _discard_backups(backups)

    if kind == "subtitle":
        lang_code, _, _source = choice.partition(":")
        entry = (info.get("requested_subtitles") or {}).get(lang_code)
        if entry and entry.get("filepath"):
            return entry["filepath"]
        raise ProbeError("Altyazi indirilemedi")

    if kind == "transcript":
        lang_code, _, rest = choice.partition(":")
        _source, _, fmt = rest.partition(":")
        entry = (info.get("requested_subtitles") or {}).get(lang_code)
        if not entry or not entry.get("filepath"):
            raise ProbeError("Transkript indirilemedi")
        vtt_path = entry["filepath"]
        text = _vtt_to_text(vtt_path, timestamps=(fmt == "ts"))
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
            # NOTE: ffprobe always prints UTF-8. Plain text=True decoded it
            # with the Windows ANSI code page instead (cp1254 on Turkish
            # Windows): "Yaş Altına" came back as "YaÅŸ AltÄ±na", and a title
            # with a character outside that code page failed to decode at
            # all, leaving the detail page with no title.
            encoding="utf-8",
            errors="replace",
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
            encoding="utf-8",
            errors="replace",
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

    # NOTE: mp4/mp3 keep tags at container level, but Ogg-based formats (.opus)
    # keep them per STREAM instead - reading only format_tags left every Opus
    # download with no title or artist on its detail page.
    if not tags.get("title") and not tags.get("artist"):
        stream_data = _ffprobe_json(path, "stream_tags=title,artist")
        for stream in stream_data.get("streams", []):
            stream_tags = {k.lower(): v for k, v in (stream.get("tags") or {}).items()}
            if stream_tags.get("title") or stream_tags.get("artist"):
                tags = stream_tags
                break

    return {"title": tags.get("title"), "artist": tags.get("artist"), "duration": _ffprobe_duration(path)}


# NOTE: ffprobe's codec_name -> the name people know. Anything missing here
# is simply shown upper-cased.
_CODEC_NAMES = {
    "h264": "H.264",
    "hevc": "H.265",
    "vp9": "VP9",
    "vp8": "VP8",
    "av1": "AV1",
    "aac": "AAC",
    "opus": "Opus",
    "mp3": "MP3",
    "vorbis": "Vorbis",
    "flac": "FLAC",
}

# NOTE: (long side, label) - the same ladder YouTube's quality menu uses. The
# LONG side decides, so a 1920x800 cinema-ratio upload is "1080p" (as it was
# offered before downloading), and a 1080x1920 vertical video is too.
_QUALITY_LADDER = (
    (7680, "4320p"),
    (3840, "2160p"),
    (2560, "1440p"),
    (1920, "1080p"),
    (1280, "720p"),
    (854, "480p"),
    (640, "360p"),
    (426, "240p"),
    (256, "144p"),
)


def quality_label(width: int, height: int) -> Optional[str]:
    long_side = max(width, height)
    for threshold, label in _QUALITY_LADDER:
        # NOTE: a few pixels of slack - encoders round odd sizes (e.g. 1918).
        if long_side >= threshold - 16:
            return label
    return None


def _parse_fps(rate: str) -> Optional[float]:
    try:
        num, _, den = (rate or "").partition("/")
        value = float(num) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        return None
    return round(value, 2) if value > 0 else None


def get_stream_info(path: str) -> dict:
    """What's actually inside a downloaded file - for the detail page.

    Returns {"video": {...} or None, "audio": {...} or None}.
    """
    # NOTE: answers "which quality did I actually get?" - the file only ever
    # holds one, so this is read from the file itself rather than trusted
    # from whatever was picked before downloading.
    data = _ffprobe_json(
        path,
        "stream=codec_type,codec_name,width,height,avg_frame_rate,sample_rate,channels,bit_rate"
        ":stream_disposition=attached_pic",
    )
    video = audio = None
    for stream in data.get("streams", []):
        kind = stream.get("codec_type")
        codec = stream.get("codec_name") or ""
        name = _CODEC_NAMES.get(codec, codec.upper() or None)
        if kind == "video" and video is None:
            # NOTE: embedded cover art is a "video" stream too (attached_pic)
            # - an MP3's thumbnail must not show up as a 1280x720 video.
            if (stream.get("disposition") or {}).get("attached_pic") == 1:
                continue
            width, height = stream.get("width"), stream.get("height")
            if not width or not height:
                continue
            video = {
                "width": width,
                "height": height,
                "quality": quality_label(width, height),
                "fps": _parse_fps(stream.get("avg_frame_rate")),
                "codec": name,
            }
        elif kind == "audio" and audio is None:
            try:
                bitrate = int(stream.get("bit_rate")) // 1000
            except (TypeError, ValueError):
                bitrate = None
            try:
                sample_rate = int(stream.get("sample_rate"))
            except (TypeError, ValueError):
                sample_rate = None
            audio = {
                "codec": name,
                "sample_rate": sample_rate,
                "channels": stream.get("channels"),
                "bitrate_kbps": bitrate or None,
            }
    return {"video": video, "audio": audio}


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


# NOTE: must match the yt-dlp line in requirements.txt (test_downloader
# checks this). Updating plain "yt-dlp" would leave yt-dlp-ejs at the old
# pinned version, and a solver script that doesn't match yt-dlp's expected
# version is ignored - YouTube challenge solving would silently stop working
# right after a "successful" update.
YTDLP_PIP_SPEC = "yt-dlp[default,deno]"


def js_runtime_status() -> dict:
    """The JavaScript runtime + challenge solver yt-dlp will use for YouTube."""
    # NOTE: asks yt-dlp itself (with the same default runtime config every
    # download uses) instead of guessing with shutil.which - yt-dlp also
    # looks in the venv's Scripts/bin folder, which is exactly where the
    # pip-installed Deno lands and which is NOT on PATH. _js_runtimes is a
    # private attribute, hence the broad except: if a future yt-dlp renames
    # it, this reports "unknown" instead of breaking the Settings page.
    result = {"js_runtime": None, "js_runtime_version": None, "js_solver": None}
    try:
        from yt_dlp.dependencies import yt_dlp_ejs

        if yt_dlp_ejs is not None:
            result["js_solver"] = str(getattr(yt_dlp_ejs, "version", "") or "?")
    except Exception:
        pass
    try:
        with YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            for name, runtime in ydl._js_runtimes.items():
                info = runtime.info if runtime else None
                if info and info.supported:
                    result["js_runtime"] = name
                    result["js_runtime_version"] = info.version
                    break
    except Exception:
        pass
    return result


def check_ytdlp_update() -> dict:
    # NOTE: yt-dlp versions are dates ("2026.07.04"), but yt_dlp.version's
    # copy keeps the zero-padding while PyPI's JSON API normalizes it
    # per PEP 440 ("2026.7.4") - a plain string compare treats those as
    # DIFFERENT versions (since "7" > "07" as text), falsely flagging every
    # up-to-date install as outdated. Parsing into int tuples compares them
    # numerically instead, where 2026.07.04 == 2026.7.4 as expected.
    result = {"installed": YT_DLP_VERSION, "latest": None, "update_available": None, **js_runtime_status()}
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
    #
    # In Docker, "in place" would mean the container's own (ephemeral)
    # filesystem - gone the next time the image is updated/recreated. --user
    # instead installs into PYTHONUSERBASE (set in the Dockerfile to a
    # volume-mounted path), which survives that. Python's own site.py gives
    # user-site packages import priority over the regular site-packages
    # automatically (see V2_PLANNING.md), so no other code needs to know this
    # override exists - outside Docker, --user is simply not used, matching
    # the exact command that already worked before this existed.
    pip_args = ["--user"] if is_docker() else []
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", *pip_args, "--upgrade", YTDLP_PIP_SPEC],
            capture_output=True,
            text=True,
            # NOTE: pip's output is only shown, never parsed - an odd byte
            # must not turn a successful update into a crash.
            errors="replace",
            timeout=120,
        )
        return {
            "ok": result.returncode == 0,
            "output": ((result.stdout or "") + (result.stderr or "")).strip(),
        }
    except Exception as exc:
        return {"ok": False, "output": str(exc)}
