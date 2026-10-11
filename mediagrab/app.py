import asyncio
import glob
import json
import re
import locale
import os
import platform
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask

from . import __version__, auth, deps, downloader, mover, stats, store
from .i18n import ui_text
from .models import (
    ChannelAddRequest,
    ChannelItem,
    ClientInfoResponse,
    CookieInspectRequest,
    CookieUploadRequest,
    DownloadDirRequest,
    DownloadRequest,
    DownloadStartResponse,
    HistoryItem,
    LocaleResponse,
    LoginRequest,
    PendingVideo,
    ProbeRequest,
    RemoteAccessStatus,
    RemoteAccessUpdateRequest,
    SessionInfo,
    SessionListResponse,
    SetPasswordRequest,
    SettingsImportRequest,
    SettingsResponse,
    SettingsUpdateRequest,
    StatusResponse,
    YtdlpVersionResponse,
)
from .paths import (
    bundled_ffmpeg_dir,
    cloud_service_in_path,
    install_type,
    is_docker,
    resource_dir,
    windows_install_dir,
)


# NOTE: the running event loop, captured once at startup by `lifespan` below -
# needed so `_broadcast_job_event` (called from arbitrary download WORKER
# THREADS, see `_run_job`) can safely hand a value to an asyncio.Queue that
# only the main event loop thread is allowed to touch directly.
_event_loop: Optional[asyncio.AbstractEventLoop] = None


def _ensure_docker_has_a_password() -> None:
    # NOTE: a container always binds to 0.0.0.0 (see run.py) - unlike a
    # desktop install, there's no "just runs on localhost until you opt in"
    # default to fall back on. Without this check, a freshly-started
    # container (no password ever set yet) would be reachable from the whole
    # network with NO login required at all. Refusing to start is
    # deliberate: a silent "works but wide open" default is worse than a
    # loud one-time setup step. Only fires when NO password has EVER been
    # set - if one exists but remote access was later turned off on
    # purpose, that's a real choice, not a missing setup step, so it's left
    # alone.
    settings = store.get_settings()
    if settings.get("remote_access_password_hash"):
        return
    initial_password = os.environ.get("MEDIAGRAB_INITIAL_PASSWORD")
    if not initial_password:
        raise RuntimeError(
            "Docker'da ilk calistirmada MEDIAGRAB_INITIAL_PASSWORD ortam degiskeni "
            "gerekli - bkz. docker-compose.yml. "
            "(A MEDIAGRAB_INITIAL_PASSWORD environment variable is required the "
            "first time MediaGrab runs in Docker - see docker-compose.yml.)"
        )
    salt, password_hash = auth.hash_password(initial_password)
    store.save_settings(
        remote_access_enabled=True,
        remote_access_password_salt=salt,
        remote_access_password_hash=password_hash,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # NOTE: replaces the deprecated @app.on_event("startup") hook.
    # Checking followed channels once here (not on a timer) is the original,
    # default design - the app only runs while opened, so this is normally
    # the only check a session ever gets. See README for why.
    #
    # home_server_mode (Ayarlar -> Uzaktan Erişim) additionally starts a
    # periodic loop for a device meant to stay running continuously (a
    # Raspberry Pi/mini PC, or a desktop someone chooses to keep open) - see
    # _periodic_channel_check_loop. The one-time check below still always
    # runs either way.
    if is_docker():
        _ensure_docker_has_a_password()
    global _event_loop
    _event_loop = asyncio.get_running_loop()
    _sweep_orphaned_parts()
    threading.Thread(target=_check_all_channels, daemon=True).start()
    _start_stats_backfill()
    _apply_installer_download_dir()
    settings = store.get_settings()
    if settings.get("home_server_mode"):
        threading.Thread(target=_periodic_channel_check_loop, daemon=True).start()
    if store.remote_access_active(settings):
        ip = lan_ip()
        if ip:
            port = int(os.environ.get("MEDIAGRAB_PORT", "8420"))
            # NOTE: on a background thread, NOT awaited/blocking here -
            # reproduced live: Zeroconf()/register_service can take several
            # seconds (or hang) probing for a name collision, and running it
            # synchronously in lifespan meant the ENTIRE app never finished
            # starting up until it returned. mDNS is a best-effort convenience
            # (see V2_PLANNING.md) - it must never be able to delay the app
            # itself being reachable, since lan_url (unaffected by this) is
            # already usable immediately.
            threading.Thread(target=_register_mdns, args=(ip, port), daemon=True).start()
    yield
    _close_mdns()


_stats_backfill_running = threading.Event()


def _run_stats_backfill(cutoff: float) -> None:
    try:
        stats.backfill(cutoff)
    except Exception:
        pass
    finally:
        _stats_backfill_running.clear()


def _start_stats_backfill() -> None:
    # NOTE: once per installation - counts what's already in indirilenler/
    # the first time a version with statistics starts, so the panel doesn't
    # open empty. On a thread: it runs ffprobe on every video, which can take
    # a while for a big library and must never delay startup.
    if store.get_stats()["backfilled"] or _stats_backfill_running.is_set():
        return
    _stats_backfill_running.set()
    threading.Thread(target=_run_stats_backfill, args=(time.time(),), daemon=True).start()


app = FastAPI(lifespan=lifespan)

# NOTE: paths reachable with NO session, even while remote access is active -
# the login page and its own API (or nobody could ever log in), plus a
# handful of static/locale bits the login page itself needs to render at all.
# Everything under /static/ is allowed separately below (see the middleware).
_PUBLIC_PATHS = {"/login", "/api/login", "/api/locale", "/sw.js"}


class _RequireLoginForRemoteAccess:
    """Raw ASGI middleware gating every route behind a session cookie once
    remote access is active - registered via `app.add_middleware()`, NOT the
    `@app.middleware("http")` decorator.

    That decorator wraps Starlette's `BaseHTTPMiddleware`, which buffers an
    ENTIRE response before it's allowed to reach the client - fine for normal
    JSON responses, fatal for `/api/events`'s infinite SSE stream (reproduced
    live: the connection just hung forever, since "the whole response" never
    arrives). Implementing `__call__(self, scope, receive, send)` directly
    forwards each chunk the instant the underlying route produces it.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        settings = store.get_settings()
        if not store.remote_access_active(settings):
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        if path in _PUBLIC_PATHS or path.startswith("/static/"):
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        token = request.cookies.get(auth.SESSION_COOKIE_NAME)
        if auth.is_valid_session(token):
            await self.app(scope, receive, send)
            return

        if path.startswith("/api/"):
            response = Response(status_code=401, content="Unauthorized")
        else:
            next_path = request.url.path
            if request.url.query:
                next_path += f"?{request.url.query}"
            response = RedirectResponse(url=f"/login?next={quote(next_path)}", status_code=307)
        await response(scope, receive, send)


app.add_middleware(_RequireLoginForRemoteAccess)

STATIC_DIR = resource_dir("static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/sw.js")
def service_worker() -> FileResponse:
    # NOTE: served from the site ROOT (not /static/sw.js) so its default
    # scope covers the whole app ("/") - a service worker's scope defaults
    # to the directory containing its script, so /static/sw.js could only
    # ever control pages under /static/ without a Service-Worker-Allowed
    # response header. Serving from "/" sidesteps that entirely.
    return FileResponse(os.path.join(STATIC_DIR, "sw.js"), media_type="application/javascript")

# NOTE: every page is rendered via Jinja2 (base.html gives them a shared
# header/nav/footer); in-page interaction (probe/download/history) is still
# plain vanilla JS.
TEMPLATES_DIR = resource_dir("templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def _asset_version(filename: str) -> int:
    # NOTE: browsers were caching app.js/style.css across updates - restarting
    # the server changes nothing for a tab that never re-fetches them, so a
    # shipped feature could look entirely missing until a hard refresh. The
    # file's own mtime as a query string forces a fresh fetch exactly when the
    # file actually changed, and lets the browser cache it normally otherwise.
    try:
        return int(os.path.getmtime(os.path.join(STATIC_DIR, filename)))
    except OSError:
        return 0


templates.env.globals["asset_version"] = _asset_version

# NOTE: job records live in memory only and are lost on server restart.
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()
_job_counter = 0

# NOTE: at most 3 concurrent downloads; the rest queue up.
executor = ThreadPoolExecutor(max_workers=3)

# NOTE: we don't keep a separate DB for download history; the indirilenler/
# folder already holds the actual files, so the history list is built by
# reading that folder.
HISTORY_EXTS = {"mp3", "m4a", "opus", "mp4", "mkv", "srt", "txt"}


def _detect_system_lang() -> str:
    # NOTE: since the app only runs locally, the language is read from the OS
    # locale rather than the browser. If anything other than Turkish is
    # detected (or nothing is), it defaults to Turkish.
    try:
        lang = locale.getlocale()[0]
        if not lang:
            locale.setlocale(locale.LC_ALL, "")
            lang = locale.getlocale()[0]
    except Exception:
        lang = None
    if lang and "turk" not in lang.lower() and not lang.lower().startswith("tr"):
        return "en"
    return "tr"


LANG_COOKIE = "mediagrab_lang"


def _resolve_lang(lang: Optional[str], request: Optional[Request] = None) -> str:
    # NOTE: ?lang= wins (JS appends it to links so the language stays
    # consistent across navigations), then the cookie set by setLang(), then
    # the system locale. The cookie matters for a *fresh* visit to a bare URL
    # (bookmark, PWA launch): without it the server would render its own
    # default language and the user's real choice would only be applied later
    # by JS - which is exactly the flash of wrong-language text this avoids.
    if lang in ("tr", "en"):
        return lang
    if request is not None:
        cookie_lang = request.cookies.get(LANG_COOKIE)
        if cookie_lang in ("tr", "en"):
            return cookie_lang
    return _detect_system_lang()


def _page_context(request: Request, lang: Optional[str], active: str) -> dict:
    resolved = _resolve_lang(lang, request)
    return {"lang": resolved, "active": active, "ui": ui_text(resolved), "app_version": __version__}


def lan_ip() -> Optional[str]:
    # NOTE: shared with run.py's own startup print AND the Settings ->
    # Remote Access address panel - both must always agree on what "the LAN
    # address" is, so there's exactly one implementation of it.
    #
    # Inside a bridge-networked Docker container (Docker Desktop on
    # Windows/Mac - see docker-compose.yml), gethostbyname(gethostname())
    # resolves to the container's OWN internal bridge IP (e.g. 172.19.0.2) -
    # unreachable from any other device, and even from the host's own
    # browser (Docker Desktop's VM sits in between). MEDIAGRAB_HOST_LAN_IP is
    # set by setup_mediagrab.py's Docker install flow (computed on the HOST,
    # before the container even exists, where this same socket call is
    # correct) to work around exactly that; a manual docker-compose install
    # can set the same variable by hand - see that file's own comment.
    override = os.environ.get("MEDIAGRAB_HOST_LAN_IP")
    if override:
        return override
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return None


# NOTE: the LAN IP above is always the primary, always-shown address - mDNS
# is purely a convenience alongside it (Android Chrome's ".local" resolution
# is historically unreliable, see V2_PLANNING.md's mDNS section). Registered
# once at startup, matching the existing restart-on-toggle flow for remote
# access - never dynamically re-registered while running.
_zeroconf_instance = None
_mdns_hostname: Optional[str] = None


def _register_mdns(ip: str, port: int) -> None:
    global _zeroconf_instance, _mdns_hostname
    # NOTE: imported here, not at module scope - keeps the dependency optional
    # in spirit even though it's declared in requirements.txt, and mirrors
    # cookie_opts()/speed_limit_opts()'s own local-import pattern elsewhere in
    # this codebase for something only needed in one place.
    from zeroconf import ServiceInfo, Zeroconf

    try:
        zc = Zeroconf()
        info = ServiceInfo(
            "_http._tcp.local.",
            "mediagrab._http._tcp.local.",
            addresses=[socket.inet_aton(ip)],
            port=port,
            server="mediagrab.local.",
        )
        # NOTE: allow_name_change lets the library resolve a collision (a
        # second MediaGrab instance already on the same network) by trying
        # "mediagrab-2", "mediagrab-3", etc. instead of just failing outright.
        # Whatever it actually ends up registering is read back from `info`
        # below - the address shown in Settings must be the address that was
        # genuinely claimed, never a hardcoded assumption of "mediagrab.local".
        zc.register_service(info, allow_name_change=True)
        _zeroconf_instance = zc
        _mdns_hostname = info.server.rstrip(".")
    except Exception:
        # NOTE: best-effort, deliberately broad - any failure here (a
        # collision the library couldn't resolve, no multicast support on
        # this network interface, etc.) must never take the whole app down.
        # The LAN IP address always still works regardless.
        _zeroconf_instance = None
        _mdns_hostname = None


def _close_mdns() -> None:
    global _zeroconf_instance
    if _zeroconf_instance is not None:
        try:
            _zeroconf_instance.close()
        except Exception:
            pass
        _zeroconf_instance = None


def _is_local_request(request: Request) -> bool:
    # NOTE: request.client can be None on some ASGI transports (e.g. certain
    # test harnesses) - treated as "local" to match this app's pre-existing,
    # loopback-only behaviour rather than accidentally locking the host out.
    client = request.client
    return client is None or client.host in ("127.0.0.1", "::1")


_LOOPBACK_HOSTNAMES = ("localhost", "127.0.0.1", "::1")


def _is_same_machine(request: Request) -> bool:
    # NOTE: a wider question than _is_local_request - "is this browser on the
    # computer MediaGrab's files live on?" rather than "can the server open a
    # file explorer on this browser's screen?". The two only differ in Docker:
    # there every request (the host's own browser AND a phone on the LAN)
    # arrives from the bridge gateway (e.g. 172.18.0.1), so the client address
    # can't tell them apart. The Host header can - the host's browser reaches
    # the published port as localhost:8420, a LAN device has to use the
    # machine's LAN IP. A LAN device could send a forged Host header, but this
    # only ever decides "don't auto-delete the server's copy" (see
    # _relay_delete_background), never anything security-relevant - the login
    # gate doesn't look at either function.
    if _is_local_request(request):
        return True
    return is_docker() and request.url.hostname in _LOOPBACK_HOSTNAMES


@app.get("/api/client-info", response_model=ClientInfoResponse)
def client_info(request: Request) -> dict:
    return {"is_local": _is_local_request(request), "same_machine": _is_same_machine(request)}


def _history_path(rel_path: str) -> str:
    # NOTE: rel_path may include a channel subfolder (e.g. "Kanal Adi/Video.mp4")
    # now that downloads are auto-organized - os.path.commonpath guards against
    # ".." escaping DOWNLOAD_DIR while still allowing that one nesting level.
    download_dir = os.path.abspath(downloader.download_dir())
    path = os.path.abspath(os.path.join(download_dir, rel_path))
    if os.path.commonpath([path, download_dir]) != download_dir or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Dosya bulunamadi")
    return path


def _url_path_quote(rel_path: str) -> str:
    # NOTE: quotes each path segment individually so "/" stays a literal
    # separator (matches the {..:path} route converters below) instead of
    # becoming "%2F", which a plain urlencode of the whole string would do.
    return "/".join(quote(seg) for seg in rel_path.split("/"))


# NOTE: one asyncio.Queue per connected /api/events tab, replacing the old
# per-job 800ms poll from the browser. `_broadcast_job_event` fans a single
# update out to all of them; a queue is discarded (see job_events) the moment
# its own connection disconnects, so this never accumulates dead entries.
_event_queues: set[asyncio.Queue] = set()
_event_queues_lock = threading.Lock()


def _job_filename(job: dict) -> Optional[str]:
    # NOTE: just the file's own name - the "Save to folder" picker in app.js
    # offers it as the suggested name.
    return os.path.basename(job["filepath"]) if job.get("filepath") else None


def _broadcast_job_event(job_id: str, job: dict) -> None:
    with _event_queues_lock:
        queues = list(_event_queues)
    if not queues or _event_loop is None:
        return
    payload = json.dumps({"job_id": job_id, **job, "filename": _job_filename(job)})
    for queue in queues:
        # NOTE: this can run on a download WORKER THREAD (yt-dlp progress
        # hooks call _set_job synchronously from there) - call_soon_threadsafe
        # is the only safe way to hand something to an asyncio.Queue that
        # belongs to a different thread's event loop.
        _event_loop.call_soon_threadsafe(queue.put_nowait, payload)


def _set_job(job_id: str, **fields) -> None:
    with jobs_lock:
        jobs[job_id].update(fields)
        job = dict(jobs[job_id])
        job["queue_position"] = _queue_position(job)
    _broadcast_job_event(job_id, job)


def _format_speed(bytes_per_sec) -> Optional[str]:
    if not bytes_per_sec:
        return None
    speed = float(bytes_per_sec)
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if speed < 1024 or unit == "GB/s":
            return f"{speed:.1f} {unit}"
        speed /= 1024
    return None


def _format_eta(seconds) -> Optional[str]:
    # NOTE: yt-dlp gives this for free in the same progress dict as speed -
    # None while it hasn't estimated one yet (e.g. right at the start).
    if seconds is None:
        return None
    seconds = int(seconds)
    if seconds < 0:
        return None
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


class JobCancelled(Exception):
    """Raised inside a download's progress hook to abort it on request."""


def _job_cancelled(job_id: str) -> bool:
    with jobs_lock:
        job = jobs.get(job_id)
        return bool(job and job.get("cancel_requested"))


# NOTE: 1 GB is the fallback floor when there's no size estimate to compare
# against (audio/subtitle/transcript downloads, and anything queued without a
# prior probe - e.g. a channel's auto-download or a playlist bulk download).
# Not meant to guarantee the download itself fits, just to catch the "disk is
# already basically full" case before yt-dlp/ffmpeg fail confusingly mid-write.
_MIN_FREE_DISK_BYTES = 1024**3
# NOTE: require some headroom over the estimate rather than an exact fit - the
# estimate can be a bit low (tbr-based, see _dedupe_video_formats), and other
# things on the same disk (the OS, other apps) still need room to breathe.
_DISK_SPACE_SAFETY_MARGIN = 1.1


def _has_enough_disk_space(estimated_size_bytes: Optional[int]) -> bool:
    free = shutil.disk_usage(downloader.download_dir()).free
    if estimated_size_bytes:
        return free >= estimated_size_bytes * _DISK_SPACE_SAFETY_MARGIN
    return free >= _MIN_FREE_DISK_BYTES


# NOTE: a move of the downloads folder (Settings -> "Move here") and
# downloads never run at the same time: a download landing mid-move could
# collide with a file being moved, and the move's free-space check would be
# stale. Downloads submitted meanwhile simply wait here, shown as queued.
_move_cond = threading.Condition()
_running_downloads = 0
_move_state: dict = {"running": False, "path": None, "done": 0, "total": 0, "result": None, "error": None}


@contextmanager
def _download_slot():
    global _running_downloads
    with _move_cond:
        while _move_state["running"]:
            _move_cond.wait()
        _running_downloads += 1
    try:
        yield
    finally:
        with _move_cond:
            _running_downloads -= 1
            _move_cond.notify_all()


def _run_gated_job(*args) -> None:
    with _download_slot():
        _run_job(*args)


def _run_job(
    job_id: str,
    url: str,
    kind: str,
    choice: str,
    subtitle_langs: list[str],
    audio_langs: Optional[list[str]] = None,
    estimated_size_bytes: Optional[int] = None,
) -> None:
    def on_progress(d: dict) -> None:
        # NOTE: this hook is the only place we get to interrupt yt-dlp - it
        # runs between chunks, and an exception raised here aborts the
        # download. Remember the temp file it was writing so a cancel doesn't
        # leave a stray .part behind.
        tmp = d.get("tmpfilename") or d.get("filename")
        if tmp:
            _set_job(job_id, tmpfile=tmp)
        if _job_cancelled(job_id):
            raise JobCancelled()

        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes") or 0
            percent = (downloaded / total * 100) if total else 0.0
            _set_job(
                job_id,
                state="indiriliyor",
                percent=round(percent, 1),
                speed=_format_speed(d.get("speed")),
                eta=_format_eta(d.get("eta")),
            )
        elif status == "finished":
            # NOTE: yt-dlp says "finished" here, but ffmpeg (merge/remux/encode)
            # may not have run yet; we don't count the job as "done" here.
            _set_job(job_id, state="isleniyor", percent=100.0, speed=None, eta=None)

    def on_postprocess(d: dict) -> None:
        if d.get("status") == "started":
            _set_job(job_id, state="isleniyor")

    # NOTE: a job can be cancelled while it's still queued behind the
    # executor's 3 worker slots, so check once more before starting any work.
    if _job_cancelled(job_id):
        _set_job(job_id, state="iptal", speed=None, eta=None)
        return

    # NOTE: re-checked here (not just in the /api/download route that queued
    # this job) because disk space can change while a job waits behind the
    # executor's 3 worker slots - a playlist bulk download is exactly the
    # case where an earlier file in the same batch can fill the disk before
    # this one's turn comes up.
    if not _has_enough_disk_space(estimated_size_bytes):
        _set_job(job_id, state="hata", error="Yetersiz disk alani")
        return

    try:
        _set_job(job_id, state="indiriliyor")
        filepath = downloader.download(
            url, kind, choice, on_progress, on_postprocess, subtitle_langs=subtitle_langs, audio_langs=audio_langs
        )
        _set_job(job_id, state="bitti", percent=100.0, ready=True, filepath=filepath)
        # NOTE: counted the moment it's finished, not by looking at the disk
        # later - relay mode deletes files once they're sent, and History's
        # own delete button exists too.
        if kind in ("audio", "video"):
            stats.record_finished(filepath)
    except JobCancelled:
        # NOTE: mark it cancelled BEFORE cleaning up - the cleanup waits for
        # the download's file handles to close, and the UI shouldn't sit on
        # "downloading" for those extra seconds.
        _set_job(job_id, state="iptal", speed=None, eta=None)
        _cleanup_partial_download(job_id)
    except Exception as exc:
        # NOTE: yt-dlp wraps hook exceptions, so a cancel can surface here as a
        # generic DownloadError instead of JobCancelled - trust the flag, not
        # the exception type, or a cancelled job would be reported as failed.
        if _job_cancelled(job_id):
            _set_job(job_id, state="iptal", speed=None, eta=None)
            _cleanup_partial_download(job_id)
        else:
            _set_job(job_id, state="hata", error=downloader.strip_ansi_codes(str(exc)))


# NOTE: reserves at least 1 of the executor's 3 worker slots for a manual
# download (the /api/download route always submits straight to `executor`,
# uncapped) - channel auto-downloads go through this instead of submitting
# directly, so they can never occupy every slot. Without this, someone
# pasting an urgent link while a channel's periodic check (see
# _periodic_channel_check_loop) just queued several auto-downloads would have
# to wait behind all of them.
_MAX_CONCURRENT_AUTO_DOWNLOADS = 2
_auto_download_lock = threading.Lock()
_active_auto_downloads = 0
_pending_auto_downloads: list[tuple] = []  # (job_id, url, kind, choice, audio_langs)


def _submit_auto_download(job_id: str, url: str, kind: str, choice: str, audio_langs: list[str]) -> None:
    global _active_auto_downloads
    with _auto_download_lock:
        if _active_auto_downloads < _MAX_CONCURRENT_AUTO_DOWNLOADS:
            _active_auto_downloads += 1
            start_now = True
        else:
            # NOTE: NOT submitted to the executor yet - the job record (state
            # "basliyor") already exists, so it still shows up as queued in
            # the UI via _queue_position, exactly like a job waiting on a full
            # executor normally would.
            _pending_auto_downloads.append((job_id, url, kind, choice, audio_langs))
            start_now = False
    if start_now:
        executor.submit(_run_auto_download_job, job_id, url, kind, choice, audio_langs)


def _run_auto_download_job(job_id: str, url: str, kind: str, choice: str, audio_langs: list[str]) -> None:
    try:
        _run_gated_job(job_id, url, kind, choice, [], audio_langs)
    finally:
        _finish_auto_download()


def _finish_auto_download() -> None:
    global _active_auto_downloads
    next_job = None
    with _auto_download_lock:
        _active_auto_downloads -= 1
        if _pending_auto_downloads:
            next_job = _pending_auto_downloads.pop(0)
            _active_auto_downloads += 1
    if next_job:
        job_id, url, kind, choice, audio_langs = next_job
        executor.submit(_run_auto_download_job, job_id, url, kind, choice, audio_langs)


# NOTE: yt-dlp downloads video and audio as separate streams named
# "<stem>.f<format_id>.<ext>" and deletes them once ffmpeg has merged the two.
# If the merge never runs - cancelled, ffmpeg failed, process killed - they
# survive, and the ".part"/".ytdl" sweep below never sees them because a
# finished stream carries neither marker. They are large (a 1080p video stream
# runs to hundreds of MB), so they are worth deleting rather than hiding.
# downloader.OUTTMPL_TAIL has no %(format_id)s in it, so a file MediaGrab finished writing can
# never carry this infix.
_FORMAT_STREAM_RE = re.compile(r"^(?P<stem>.+)\.f\d+\.[^.]+$")


def _cleanup_partial_download(job_id: str) -> None:
    with jobs_lock:
        tmp = (jobs.get(job_id) or {}).get("tmpfile")
    if not tmp:
        return
    download_dir = os.path.abspath(downloader.download_dir())
    # NOTE: a fragmented (DASH) download leaves far more than one file behind:
    # "<name>.part" plus a "<name>.part-FragNN[.part]" per in-flight fragment.
    # They all start with the tmpfilename yt-dlp reported, so one glob catches
    # the lot; "<name>.ytdl" is the separate resume journal. Matching on
    # ".part"/".ytdl" only is deliberate - those markers never appear on a
    # finished file, so this can't touch a real download.
    candidates = set(glob.glob(glob.escape(tmp) + "*"))
    base = tmp[: -len(".part")] if tmp.endswith(".part") else tmp
    candidates.add(base + ".ytdl")
    # NOTE: a stream that finished downloading has already lost its ".part"
    # suffix, so nothing above would ever name it. This is not guesswork - the
    # name comes from the tmpfilename yt-dlp reported for THIS job.
    if _FORMAT_STREAM_RE.match(os.path.basename(base)):
        candidates.add(base)

    stale = []
    for candidate in candidates:
        path = os.path.abspath(candidate)
        name = os.path.basename(path)
        if not path.startswith(download_dir + os.sep):
            continue
        if (
            ".part" not in name
            and not name.endswith(".ytdl")
            and not _FORMAT_STREAM_RE.match(name)
        ):
            continue
        stale.append(path)

    # NOTE: Windows won't delete a file that's still open, and the fragment
    # worker threads let go at different moments - a short retry catches most
    # of them. The MAIN ".part" of a fragmented download is a known exception:
    # a worker thread keeps it open for the life of the process (measured:
    # still locked 40s after the abort), so it can't be removed here at all.
    # _sweep_orphaned_parts() at startup is what finally clears those.
    deadline = time.monotonic() + 2.0
    while True:
        stale = [p for p in stale if os.path.isfile(p)]
        if not stale:
            return
        for path in list(stale):
            try:
                os.remove(path)
            except OSError:
                pass
        if time.monotonic() >= deadline:
            return
        time.sleep(0.3)


def _sweep_orphaned_parts() -> None:
    # NOTE: runs once at startup, when nothing can possibly be downloading, so
    # every ".part"/".ytdl" left in indirilenler/ is debris from a cancelled or
    # crashed run of a previous session. Neither marker ever appears on a
    # finished file, so this can't touch a real download.
    removed = 0
    restored = 0
    for root, _dirs, files in os.walk(downloader.download_dir()):
        # NOTE: worked out per directory - an unmerged stream is only provably
        # debris once the merged output is sitting right there beside it, and
        # then it is redundant by definition. This is also what protects the
        # one title that could otherwise be mistaken for a stream (a video
        # genuinely called "something.f616"): its own sidecars carry the same
        # infix, so no plain sibling exists and the file is left alone.
        merged_stems = {
            os.path.splitext(name)[0] for name in files if not _FORMAT_STREAM_RE.match(name)
        }

        for name in files:
            path = os.path.join(root, name)

            # NOTE: a leftover backup means the process died mid-download,
            # before downloader could put the file back itself. If the real
            # name is free, that backup IS the user's file - restore it.
            # If something is already there, the download did finish and only
            # the cleanup was missed, so the backup is redundant.
            if name.endswith(downloader.BACKUP_SUFFIX):
                original = path[: -len(downloader.BACKUP_SUFFIX)]
                try:
                    if os.path.exists(original):
                        os.remove(path)
                        removed += 1
                    else:
                        os.replace(path, original)
                        restored += 1
                except OSError:
                    pass
                continue

            stream = _FORMAT_STREAM_RE.match(name)
            if stream and stream.group("stem") in merged_stems:
                try:
                    os.remove(path)
                    removed += 1
                except OSError:
                    pass
                continue

            if ".part" not in name and not name.endswith(".ytdl"):
                continue
            try:
                os.remove(path)
                removed += 1
            except OSError:
                pass
    if removed:
        print(f"[MediaGrab] {removed} yarim kalmis indirme dosyasi temizlendi.", flush=True)
    if restored:
        print(f"[MediaGrab] {restored} dosya yarim kalan indirmeden geri yuklendi.", flush=True)


def _check_channel(channel: dict) -> None:
    checked_at = datetime.now().isoformat(timespec="seconds")
    try:
        new_videos = downloader.check_channel_new_videos(channel["url"], channel.get("last_video_id"))
    except Exception as exc:
        # NOTE: one unreachable channel must not stop the others from being
        # checked, so this still swallows the exception - but it no longer
        # returns before recording the attempt. It used to, which meant a
        # channel that had started failing kept showing its old "last checked"
        # time forever, looking exactly like a channel with no new uploads.
        store.update_channel(
            channel["id"],
            last_checked_at=checked_at,
            last_error=downloader.strip_ansi_codes(str(exc))[:300],
        )
        return

    if new_videos:
        newest_id = new_videos[0]["id"]
        if channel["mode"] == "auto":
            # NOTE: read fresh rather than once per batch - a setting changed
            # mid-run should apply to the next channel checked, not wait for
            # the next full sweep.
            # NOTE: multi-track download is manual-only (see downloader.py) -
            # auto-download always gets at most this one saved language.
            audio_lang = store.get_settings()["default_audio_lang"]
            audio_langs = [audio_lang] if audio_lang else []
            for v in new_videos:
                job_id = uuid.uuid4().hex
                with jobs_lock:
                    jobs[job_id] = _new_job_record()
                _submit_auto_download(job_id, v["url"], channel["choice_kind"], channel["choice"], audio_langs)
        else:
            store.add_pending(
                [
                    {
                        "channel_id": channel["id"],
                        "channel_name": channel["name"],
                        **v,
                    }
                    for v in new_videos
                ]
            )
        store.update_channel(channel["id"], last_video_id=newest_id)

    # NOTE: last_error is cleared here, so a channel that recovers stops
    # showing the warning without the user having to do anything.
    store.update_channel(channel["id"], last_checked_at=checked_at, last_error=None)


def _check_all_channels() -> None:
    for channel in store.list_channels():
        _check_channel(channel)


# NOTE: 3 hours - frequent enough that a new upload doesn't sit undetected
# for most of a day, infrequent enough not to hammer every followed channel's
# page constantly. Only relevant when home_server_mode is on; the one-time
# check-at-launch in lifespan() always runs regardless of this setting.
_HOME_SERVER_CHANNEL_CHECK_INTERVAL_SECONDS = 3 * 3600


def _periodic_channel_check_loop() -> None:
    # NOTE: plain threading + time.sleep, not asyncio - matches the launch-
    # time check's own thread (see lifespan) and, more importantly, keeps
    # _check_channel's blocking network/yt-dlp calls off the asyncio event
    # loop that SSE and every other request depend on.
    while True:
        time.sleep(_HOME_SERVER_CHANNEL_CHECK_INTERVAL_SECONDS)
        _check_all_channels()


@app.get("/")
def index(request: Request, lang: Optional[str] = None):
    return templates.TemplateResponse(request, "index.html", _page_context(request, lang, "home"))


@app.get("/settings")
def settings_page(request: Request, lang: Optional[str] = None):
    return templates.TemplateResponse(request, "settings.html", _page_context(request, lang, "settings"))


@app.get("/history")
def history_page(request: Request, lang: Optional[str] = None):
    return templates.TemplateResponse(request, "history.html", _page_context(request, lang, "history"))


@app.get("/channels")
def channels_page(request: Request, lang: Optional[str] = None):
    return templates.TemplateResponse(request, "channels.html", _page_context(request, lang, "channels"))


@app.get("/supported-sites")
def supported_sites_page(request: Request, lang: Optional[str] = None):
    return templates.TemplateResponse(request, "supported_sites.html", _page_context(request, lang, "sites"))


@app.get("/about")
def about_page(request: Request, lang: Optional[str] = None):
    return templates.TemplateResponse(request, "about.html", _page_context(request, lang, "about"))


# --- login gate for optional LAN/remote access --------------------------------


@app.get("/login")
def login_page(request: Request, lang: Optional[str] = None, next: str = "/"):
    return templates.TemplateResponse(
        request, "login.html", {**_page_context(request, lang, "login"), "next": next}
    )


@app.post("/api/login")
def login(req: LoginRequest, request: Request) -> Response:
    settings = store.get_settings()
    if not auth.verify_password(
        req.password, settings["remote_access_password_salt"], settings["remote_access_password_hash"]
    ):
        raise HTTPException(status_code=401, detail="Sifre yanlis")
    token = auth.create_session(request.headers.get("user-agent", ""))
    response = Response(content=json.dumps({"ok": True}), media_type="application/json")
    response.set_cookie(
        auth.SESSION_COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        max_age=30 * 24 * 3600,
    )
    return response


@app.post("/api/logout")
def logout(request: Request) -> Response:
    token = request.cookies.get(auth.SESSION_COOKIE_NAME)
    auth.destroy_session(token)
    response = Response(content=json.dumps({"ok": True}), media_type="application/json")
    response.delete_cookie(auth.SESSION_COOKIE_NAME)
    return response


def _remote_access_status(settings: dict, request: Request) -> dict:
    active = store.remote_access_active(settings)
    lan_url = None
    mdns_url = None
    if active:
        ip = lan_ip()
        if ip:
            port = request.url.port or 8420
            lan_url = f"http://{ip}:{port}"
        # NOTE: _mdns_hostname is None if registration never ran (not
        # active), failed (collision, no multicast support, ...), or hasn't
        # happened yet this process - lan_url above is always the one
        # guaranteed-correct address either way.
        if _mdns_hostname:
            mdns_url = f"http://{_mdns_hostname}:{port}"
    return {
        "enabled": bool(settings.get("remote_access_enabled")),
        "has_password": bool(settings.get("remote_access_password_hash")),
        "lan_url": lan_url,
        "mdns_url": mdns_url,
        "download_mode": settings.get("remote_download_mode", "keep"),
    }


@app.get("/api/remote-access", response_model=RemoteAccessStatus)
def remote_access_status(request: Request) -> dict:
    return _remote_access_status(store.get_settings(), request)


@app.post("/api/remote-access", response_model=RemoteAccessStatus)
def update_remote_access(req: RemoteAccessUpdateRequest, request: Request) -> dict:
    settings = store.get_settings()
    was_active = store.remote_access_active(settings)
    if req.enabled and not settings.get("remote_access_password_hash"):
        raise HTTPException(status_code=400, detail="Once bir sifre belirleyin")
    settings = store.save_settings(remote_access_enabled=req.enabled, remote_download_mode=req.download_mode)
    if was_active != store.remote_access_active(settings):
        # NOTE: which network interface uvicorn listens on is only decided at
        # process startup (see run.py) - the only way to change it live is to
        # restart the whole process, same restart dance as the yt-dlp/deps
        # updaters.
        threading.Thread(target=_delayed_restart, daemon=True).start()
    return _remote_access_status(settings, request)


@app.post("/api/remote-access/password", response_model=RemoteAccessStatus)
def set_remote_access_password(req: SetPasswordRequest, request: Request) -> dict:
    settings = store.get_settings()
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Sifre en az 8 karakter olmali")
    existing_hash = settings.get("remote_access_password_hash")
    if existing_hash:
        # NOTE: nothing to confirm against on the very first password - only
        # required once a real one already exists.
        if not auth.verify_password(
            req.current_password, settings.get("remote_access_password_salt", ""), existing_hash
        ):
            raise HTTPException(status_code=401, detail="Mevcut sifre yanlis")
    salt, password_hash = auth.hash_password(req.password)
    settings = store.save_settings(remote_access_password_salt=salt, remote_access_password_hash=password_hash)
    # NOTE: a real security property, not just plumbing - anyone already
    # logged in (possibly not the account holder any more) must be signed out
    # immediately rather than staying trusted until their session expires.
    auth.clear_all_sessions()
    return _remote_access_status(settings, request)


@app.get("/api/remote-access/sessions", response_model=SessionListResponse)
def remote_access_sessions(request: Request) -> dict:
    current_token = request.cookies.get(auth.SESSION_COOKIE_NAME)
    return {"sessions": auth.list_sessions(current_token)}


@app.delete("/api/remote-access/sessions/{session_id}")
def revoke_remote_access_session(session_id: str) -> dict:
    auth.destroy_session_by_id(session_id)
    return {"ok": True}


@app.post("/api/probe")
def probe(req: ProbeRequest) -> dict:
    # NOTE: response_model is deliberately omitted - single-video and
    # playlist responses have different shapes (a video list vs. an entries
    # list), so we return a plain dict instead of one Union model; the client
    # distinguishes them via the "type" field.
    try:
        return downloader.probe(req.url)
    except downloader.ProbeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _new_job_record() -> dict:
    global _job_counter
    # NOTE: a submission order is needed to work out queue position later -
    # the executor's own queue isn't introspectable, and dict order alone
    # breaks once finished jobs are interleaved.
    _job_counter += 1
    return {
        "state": "basliyor",
        "percent": 0.0,
        "speed": None,
        "eta": None,
        "ready": False,
        "error": None,
        "filepath": None,
        "cancel_requested": False,
        "tmpfile": None,
        "seq": _job_counter,
    }


def _queue_position(job: dict) -> Optional[int]:
    """1-based place in the waiting queue, or None if it isn't waiting."""
    # NOTE: only 3 downloads run at once; the rest sat at "Starting..."
    # indefinitely, which was indistinguishable from a stuck download. This
    # turns that into "3rd in queue".
    if job["state"] != "basliyor":
        return None
    ahead = sum(1 for other in jobs.values() if other["state"] == "basliyor" and other["seq"] < job["seq"])
    return ahead + 1


@app.post("/api/download", response_model=DownloadStartResponse)
def start_download(req: DownloadRequest) -> dict:
    # NOTE: checked again inside _run_job right before the download actually
    # starts (see its own comment) - this check here is just so a request
    # that's already doomed never even gets a job_id / queue slot.
    if not _has_enough_disk_space(req.estimated_size_bytes):
        raise HTTPException(status_code=507, detail="Yetersiz disk alani")
    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = _new_job_record()
    executor.submit(
        _run_gated_job, job_id, req.url, req.kind, req.choice, req.subtitle_langs, req.audio_langs, req.estimated_size_bytes
    )
    return {"job_id": job_id}


@app.post("/api/cancel/{job_id}")
def cancel_download(job_id: str) -> dict:
    # NOTE: only flags the job - the actual abort happens in the download's
    # progress hook (see _run_job), because yt-dlp runs synchronously inside a
    # worker thread and there's no way to interrupt it from the outside.
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Is bulunamadi")
        if job["state"] in ("bitti", "hata", "iptal"):
            return {"ok": False, "state": job["state"]}
        job["cancel_requested"] = True
    return {"ok": True}


@app.get("/api/status/{job_id}", response_model=StatusResponse)
def status(job_id: str) -> dict:
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Is bulunamadi")
        return {**job, "queue_position": _queue_position(job), "filename": _job_filename(job)}


@app.get("/api/events")
async def job_events(request: Request) -> StreamingResponse:
    # NOTE: replaces the download dock's old per-job 800ms poll with one
    # shared SSE connection - see _broadcast_job_event/_set_job for the
    # producer side. ": ..." lines are SSE comments (ignored by
    # EventSource.onmessage) used here purely as keep-alives, so an idle
    # proxy/browser doesn't time the connection out.
    queue: asyncio.Queue = asyncio.Queue()
    with _event_queues_lock:
        _event_queues.add(queue)

    async def stream():
        try:
            yield ": connected\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            with _event_queues_lock:
                _event_queues.discard(queue)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/api/file/{job_id}")
def file(job_id: str) -> dict:
    # NOTE: this used to also stream the file back as a FileResponse, which
    # made the browser save a SECOND copy (into its own default downloads
    # folder) on top of the one yt-dlp already wrote to DOWNLOAD_DIR. The file
    # is already permanently on disk once the job is "bitti" - clicking this
    # only needs to reveal it, not duplicate it.
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None or not job.get("ready"):
            raise HTTPException(status_code=404, detail="Dosya henuz hazir degil")
        filepath = job["filepath"]
    downloader.reveal_in_explorer(filepath)
    return {"ok": True}


def _delete_relayed_file(path: str) -> None:
    # NOTE: runs as a FileResponse `background` task - Starlette only starts
    # it once the response has been FULLY sent, so a connection that drops
    # partway through a transfer never triggers this (the file is only ever
    # deleted after a genuinely complete hand-off to the requesting device).
    # Reuses the exact same three steps as the manual "delete from History"
    # action (_remove_sidecar_json / _cleanup_empty_dir, defined below) -
    # this isn't a separate deletion path, just an automatic trigger for the
    # same one.
    try:
        os.remove(path)
    except OSError:
        return
    _remove_sidecar_json(path)
    _cleanup_empty_dir(path)


def _relay_delete_background(path: str, same_machine: bool) -> Optional[BackgroundTask]:
    # NOTE: "relay" mode only ever applies to a REMOTE device's own transfer.
    # The host's own downloads are never auto-deleted here in either mode - a
    # fully sent response only proves the BROWSER received the bytes, not
    # that the user kept them: with "ask where to save" on, Chrome/Edge fetch
    # the whole file in the background while the Save As dialog is still
    # open, so cancelling that dialog used to delete the only copy (found in
    # Docker, where the host's browser counted as remote - see
    # _is_same_machine). On the host, deletion instead waits for the
    # browser's own confirmation that the file was written (/saved below).
    if same_machine or store.get_settings().get("remote_download_mode") != "relay":
        return None
    return BackgroundTask(_delete_relayed_file, path)


def _confirm_saved(path: str) -> dict:
    # NOTE: called by the "Save to folder" flow in app.js only AFTER the
    # browser's File System Access API reports the file fully written to the
    # folder the user picked - cancelling the picker never reaches this. Same
    # keep/relay rule as a remote device's transfer, just triggered by a
    # confirmed save instead of a sent response.
    if store.get_settings().get("remote_download_mode") != "relay":
        return {"deleted": False}
    _delete_relayed_file(path)
    return {"deleted": not os.path.exists(path)}


@app.get("/api/file/{job_id}/download")
def download_file(job_id: str, request: Request) -> FileResponse:
    # NOTE: the counterpart to /api/file/{job_id} - a remote device (phone,
    # laptop on the LAN) has no use for "reveal in folder" (that would open
    # an OS file explorer on the HOST's screen, not the device asking), so
    # the client picks this one instead once /api/client-info says it isn't
    # local. FileResponse's `filename=` sets Content-Disposition: attachment,
    # which is what makes the browser actually save it instead of navigating
    # to it inline.
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None or not job.get("ready"):
            raise HTTPException(status_code=404, detail="Dosya henuz hazir degil")
        filepath = job["filepath"]
    background = _relay_delete_background(filepath, _is_same_machine(request))
    return FileResponse(filepath, filename=os.path.basename(filepath), background=background)


@app.post("/api/file/{job_id}/saved")
def file_saved(job_id: str) -> dict:
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None or not job.get("ready"):
            raise HTTPException(status_code=404, detail="Dosya henuz hazir degil")
        filepath = job["filepath"]
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Dosya bulunamadi")
    return _confirm_saved(filepath)


@app.get("/api/locale", response_model=LocaleResponse)
def locale_info() -> dict:
    return {"lang": _detect_system_lang()}


def diagnostics_text() -> str:
    """A plain-text environment summary to paste into a bug report."""
    # NOTE: what's left out matters as much as what's in - this text is meant
    # to be pasted into a PUBLIC GitHub issue, so: no file paths (they carry
    # the user's name on most systems), no IP addresses, no hostname
    # (platform.node), no cookie names/values/paths. Only versions and
    # on/off states. Nothing here makes a network request either.
    settings = store.get_settings()
    js = downloader.js_runtime_status()
    ffmpeg = deps.check_ffmpeg()
    cookie_mode = settings.get("cookie_mode", "off")
    if cookie_mode == "browser":
        browser = settings.get("cookie_browser") or "firefox"
        usable = browser in downloader.usable_cookie_browsers()
        cookies = f"browser ({browser}{'' if usable else ', not usable on this OS'})"
    elif cookie_mode == "file":
        summary = downloader.cookie_file_summary(settings.get("cookie_file") or "")
        if summary is None:
            cookies = "file (unreadable)"
        else:
            source = "uploaded" if _is_uploaded_cookie_file(settings.get("cookie_file") or "") else "path"
            session = "yes" if summary["youtube_signed_in"] else "no"
            cookies = f"file ({source}, {summary['total']} cookies, YouTube session: {session})"
    else:
        cookies = "off"
    js_line = (
        f"{js['js_runtime']} {js['js_runtime_version']}" if js["js_runtime"] else "missing"
    ) + f" (solver: {js['js_solver'] or 'missing'})"
    lines = [
        f"MediaGrab: {__version__} ({install_type()})",
        f"OS: {platform.system()} {platform.release()} ({platform.machine()})",
        f"Python: {platform.python_version()}",
        f"yt-dlp: {downloader.YT_DLP_VERSION}",
        f"JS runtime: {js_line}",
        f"ffmpeg: {ffmpeg.get('ffmpeg') or 'missing'} / ffprobe: {ffmpeg.get('ffprobe') or 'missing'}",
        f"Cookies: {cookies}",
        f"Remote access: {'on' if store.remote_access_active(settings) else 'off'}"
        f" / home server mode: {'on' if settings.get('home_server_mode') else 'off'}",
    ]
    return "\n".join(lines)


def _folder_size(folder: str) -> int:
    total = 0
    for root, _dirs, files in os.walk(folder):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def _disk_status() -> Optional[dict]:
    # NOTE: the disk the downloads folder is on. In Docker that's the host's
    # own drive (the folder is a bind mount), not the container's - checked
    # live on Docker Desktop: the numbers match the Windows drive.
    # NOTE: before the first download the folder may not exist yet - the
    # nearest existing parent is on the same drive.
    downloads = downloader.download_dir()
    folder = os.path.abspath(downloads)
    while not os.path.isdir(folder) and os.path.dirname(folder) != folder:
        folder = os.path.dirname(folder)
    try:
        usage = shutil.disk_usage(folder)
    except OSError:
        return None
    return {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
        "downloads": _folder_size(downloads),
    }


@app.get("/api/stats")
def stats_summary(period: str = "day", tz: int = 0) -> dict:
    # NOTE: tz is the viewer's offset from UTC in minutes (Turkey: 180) -
    # the stored hours are UTC, the days/weeks/months shown are the viewer's.
    if period not in stats.PERIODS:
        raise HTTPException(status_code=400, detail="Gecersiz donem")
    tz = max(-14 * 60, min(14 * 60, tz))
    data = store.get_stats()
    return {
        **stats.summarize(data, period, tz),
        "backfilling": _stats_backfill_running.is_set(),
        "disk": _disk_status(),
    }


@app.post("/api/stats/reset")
def stats_reset() -> dict:
    store.reset_stats()
    return {"ok": True}


# --- download folder (Settings -> Downloads) ------------------------------------


def _download_dir_editable(request: Request) -> bool:
    # NOTE: only from the computer MediaGrab runs on - a phone choosing a
    # folder on someone else's disk makes no sense - and never in Docker,
    # where the compose file's volume decides (store.py's download_dir note).
    return _is_same_machine(request) and not is_docker()


def _forbidden_download_roots() -> list[str]:
    # NOTE: never inside MediaGrab's own program files: an update replaces
    # them and an uninstall deletes them - downloads must not ride along.
    roots = [os.path.dirname(os.path.abspath(__file__))]
    install = windows_install_dir()
    if install:
        roots.append(install)
    return [os.path.normcase(os.path.abspath(r)) for r in roots]


def _check_download_dir(path: str) -> str:
    """Validate (and create) a chosen downloads folder; return it normalised."""
    if not os.path.isabs(path):
        raise HTTPException(status_code=400, detail="relative")
    folder = os.path.abspath(path)
    key = os.path.normcase(folder)
    for root in _forbidden_download_roots():
        if key == root or key.startswith(root + os.sep):
            raise HTTPException(status_code=400, detail="inside_app")
    if os.path.exists(folder) and not os.path.isdir(folder):
        raise HTTPException(status_code=400, detail="not_a_folder")
    # NOTE: proven by actually writing, not guessed from permission bits -
    # Windows ACLs, read-only media and full disks all fail here the same way.
    probe = os.path.join(folder, f".mediagrab-write-test-{uuid.uuid4().hex}")
    try:
        os.makedirs(folder, exist_ok=True)
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
    except OSError:
        raise HTTPException(status_code=400, detail="not_writable")
    return folder


def _move_exclude(old: str, current: str) -> Optional[str]:
    # NOTE: when the current folder lies INSIDE the old one, its files are
    # already where they belong - a move must not pick them up again.
    return current if mover.is_inside(current, old) else None


def _change_download_dir(setting: str) -> None:
    """Save a new download_dir setting and remember the folder it replaces."""
    old = downloader.download_dir()
    store.save_settings(download_dir=setting)
    current = downloader.download_dir()
    previous = [p for p in store.get_settings().get("previous_download_dirs") or [] if isinstance(p, str)]
    # NOTE: back in a folder (or above it - History walks subfolders): its
    # files are visible again, nothing left to offer.
    previous = [p for p in previous if not mover.is_inside(p, current)]
    if (
        not mover.is_inside(old, current)
        and not any(mover.is_inside(old, p) and mover.is_inside(p, old) for p in previous)
        and mover.movable_files(old, HISTORY_EXTS, _move_exclude(old, current))
    ):
        previous.append(old)
    store.save_settings(previous_download_dirs=previous)


def _previous_download_dirs() -> list[dict]:
    """Earlier folders still holding downloads; drops the ones now empty."""
    current = downloader.download_dir()
    kept, info = [], []
    for path in store.get_settings().get("previous_download_dirs") or []:
        if not isinstance(path, str):
            continue
        if not os.path.isdir(path):
            # NOTE: e.g. a USB drive that's unplugged right now - kept, so the
            # offer comes back when it's plugged in again.
            kept.append(path)
            info.append({"path": path, "available": False, "files": 0, "bytes": 0})
            continue
        files = mover.movable_files(path, HISTORY_EXTS, _move_exclude(path, current))
        if files:
            kept.append(path)
            info.append({"path": path, "available": True, "files": len(files), "bytes": sum(s for _r, s in files)})
    if kept != store.get_settings().get("previous_download_dirs"):
        store.save_settings(previous_download_dirs=kept)
    return info


def _download_dir_info(request: Request) -> dict:
    current = downloader.download_dir()
    editable = _download_dir_editable(request)
    return {
        "previous": [] if is_docker() else _previous_download_dirs(),
        "move": _move_status(),
        "path": current,
        "default": downloader.DOWNLOAD_DIR,
        "is_default": os.path.normcase(os.path.abspath(current))
        == os.path.normcase(os.path.abspath(downloader.DOWNLOAD_DIR)),
        "editable": editable,
        # NOTE: the native folder picker runs on THIS machine's screen
        # (Windows only, see download_dir_browse).
        "can_browse": editable and os.name == "nt",
        "cloud": cloud_service_in_path(current),
        "is_docker": is_docker(),
    }


# NOTE: the Windows installer's "where should videos be saved?" page leaves
# the answer here (see packaging/mediagrab.iss) instead of editing
# settings.json from Pascal - this way the app's own checks
# (_check_download_dir) decide, exactly as if it was chosen in Settings.
INSTALLER_DOWNLOAD_DIR_FILE = "install-download-dir.txt"


def _apply_installer_download_dir() -> None:
    handoff = os.path.join(os.path.dirname(store.SETTINGS_PATH), INSTALLER_DOWNLOAD_DIR_FILE)
    if not os.path.isfile(handoff):
        return
    try:
        with open(handoff, "r", encoding="utf-8-sig") as f:
            chosen = f.read().strip()
        # NOTE: the installer's choice wins over an existing setting (a
        # reinstall with data kept): its page started from that setting, so
        # whatever it hands over is what the user last saw and confirmed.
        # The default needs no setting at all.
        if chosen:
            same_as_default = os.path.normcase(os.path.abspath(chosen)) == os.path.normcase(
                os.path.abspath(downloader.DOWNLOAD_DIR)
            )
            _change_download_dir("" if same_as_default else _check_download_dir(chosen))
    except (OSError, HTTPException):
        # NOTE: an unusable choice (a drive that's gone, say) just leaves the
        # default in place; Settings can change it any time.
        pass
    finally:
        try:
            os.remove(handoff)
        except OSError:
            pass


@app.get("/api/download-dir")
def get_download_dir(request: Request) -> dict:
    return _download_dir_info(request)


@app.post("/api/download-dir")
def set_download_dir(req: DownloadDirRequest, request: Request) -> dict:
    if not _download_dir_editable(request):
        raise HTTPException(status_code=403, detail="not_allowed")
    if _move_status()["running"]:
        # NOTE: the move's target is the current folder - it can't change
        # under a move that's halfway through.
        raise HTTPException(status_code=409, detail="already_moving")
    path = req.path.strip()
    # NOTE: switches right away, for NEW downloads; files already in the old
    # folder stay put until the user picks "Move here" or "Leave them there"
    # in Settings (the folder is remembered by _change_download_dir).
    _change_download_dir(_check_download_dir(path) if path else "")
    return _download_dir_info(request)


def _move_status() -> dict:
    with _move_cond:
        return dict(_move_state)


def _known_previous_dir(path: str) -> str:
    # NOTE: only a folder MediaGrab itself remembered can be moved from or
    # forgotten - never an arbitrary path sent in a request.
    for known in store.get_settings().get("previous_download_dirs") or []:
        if isinstance(known, str) and mover.is_inside(known, path) and mover.is_inside(path, known):
            return known
    raise HTTPException(status_code=404, detail="unknown_folder")


def _run_move(src: str) -> None:
    current = downloader.download_dir()

    def progress(done: int, total: int) -> None:
        with _move_cond:
            _move_state.update(done=done, total=total)

    result, error = None, None
    try:
        result = mover.move_files(src, current, HISTORY_EXTS, _move_exclude(src, current), progress)
    except mover.NotEnoughSpace as exc:
        error = {"code": "no_space", "needed": exc.needed, "free": exc.free}
    except OSError:
        error = {"code": "failed"}
    finally:
        with _move_cond:
            _move_state.update(running=False, result=result, error=error)
            _move_cond.notify_all()
    # NOTE: dropped here, not left to _previous_download_dirs: a move that
    # emptied the folder also removed it, and a missing folder there means
    # "drive unplugged, keep offering".
    if not os.path.isdir(src) or not mover.movable_files(src, HISTORY_EXTS, _move_exclude(src, current)):
        previous = [p for p in store.get_settings().get("previous_download_dirs") or [] if p != src]
        store.save_settings(previous_download_dirs=previous)


@app.post("/api/download-dir/move")
def download_dir_move(req: DownloadDirRequest, request: Request) -> dict:
    """Move an earlier folder's downloads into the current one, in the background."""
    if not _download_dir_editable(request):
        raise HTTPException(status_code=403, detail="not_allowed")
    src = _known_previous_dir(req.path)
    if not os.path.isdir(src):
        raise HTTPException(status_code=404, detail="unavailable")
    with _move_cond:
        if _move_state["running"]:
            raise HTTPException(status_code=409, detail="already_moving")
        # NOTE: running downloads finish first; ones that start meanwhile
        # wait in _download_slot until the move is over.
        if _running_downloads:
            raise HTTPException(status_code=409, detail="downloads_running")
        _move_state.update(running=True, path=src, done=0, total=0, result=None, error=None)
    threading.Thread(target=_run_move, args=(src,), daemon=True).start()
    return _move_status()


@app.get("/api/download-dir/move")
def download_dir_move_status() -> dict:
    return _move_status()


@app.post("/api/download-dir/forget")
def download_dir_forget(req: DownloadDirRequest, request: Request) -> dict:
    """ "Leave them there": stop offering to move this folder. Deletes nothing."""
    if not _download_dir_editable(request):
        raise HTTPException(status_code=403, detail="not_allowed")
    src = _known_previous_dir(req.path)
    with _move_cond:
        if _move_state["running"] and _move_state["path"] == src:
            raise HTTPException(status_code=409, detail="already_moving")
    previous = [p for p in store.get_settings().get("previous_download_dirs") or [] if p != src]
    store.save_settings(previous_download_dirs=previous)
    return _download_dir_info(request)


# NOTE: Windows' modern Explorer-style folder dialog, in its own process
# (see folder_picker.py for why it isn't run inside the server).
FOLDER_PICKER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "folder_picker.py")


@app.post("/api/download-dir/browse")
def download_dir_browse(request: Request, lang: Optional[str] = None) -> dict:
    """Open Windows' own folder picker on this machine's screen."""
    # NOTE: a browser page can't hand back a real folder path (only file
    # contents), and asking a non-technical user to type one is a dead end.
    # So the picker runs server-side - which is exactly why this is limited
    # to the same machine: a phone must never pop dialogs on the host.
    if not _download_dir_editable(request) or os.name != "nt":
        raise HTTPException(status_code=403, detail="not_allowed")
    title = ui_text(_resolve_lang(lang, request))["settings_download_dir_picker_title"]
    env = {**os.environ, "MEDIAGRAB_PICKER_TITLE": title, "MEDIAGRAB_PICKER_START": downloader.download_dir()}
    try:
        # NOTE: the strings travel in environment variables, not on the
        # command line - nothing in a folder name can be read as an option.
        result = subprocess.run(
            [sys.executable, "-I", FOLDER_PICKER_SCRIPT],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=600,
        )
    except (OSError, subprocess.SubprocessError):
        raise HTTPException(status_code=500, detail="picker_failed")
    chosen = (result.stdout or "").strip()
    return {"path": chosen or None}


@app.get("/api/diagnostics")
def diagnostics() -> dict:
    return {"text": diagnostics_text()}


@app.get("/api/mediagrab-version")
def mediagrab_version() -> dict:
    # NOTE: install_type picks the update instructions shown (Docker image /
    # installer's Repair-Update / git pull) - MediaGrab never updates itself.
    return deps.check_mediagrab_update()


@app.get("/api/ytdlp-version", response_model=YtdlpVersionResponse)
def ytdlp_version() -> dict:
    # NOTE: is_docker - same reason as /api/dependencies below: the Settings
    # page hides the manual venv/pip steps in a container (there is no venv,
    # and the image is what actually gets updated).
    return {**downloader.check_ytdlp_update(), "is_docker": is_docker()}


def _delayed_restart() -> None:
    # NOTE: os.execv replaces this process's image with a fresh one using the
    # exact same command line that launched it - works the same whether that
    # was "python run.py" or "uvicorn mediagrab.app:app", since both run this
    # same process. The 1s delay lets the HTTP response for the update
    # request actually reach the browser before the process restarts.
    #
    # sys.orig_argv (3.10+) is used over sys.argv when available: sys.argv
    # loses a "-m module" framing (e.g. "python -m uvicorn ...") down to just
    # "uvicorn ..." with no interpreter path, which makes os.execv run
    # uvicorn's OWN __main__.py directly instead of through "-m" - that
    # changes sys.path[0] to uvicorn's package directory, letting its
    # uvicorn/logging.py shadow the stdlib logging module and crashing the
    # restarted process (reproduced live: "module 'logging' has no attribute
    # 'Formatter'"). sys.orig_argv preserves the exact original invocation,
    # "-m" and all.
    time.sleep(1.0)
    if os.name == "nt":
        from . import tray  # NOTE: Windows-only module (Win32 API)

        tray.remove_running_icon()
    argv = getattr(sys, "orig_argv", None) or [sys.executable] + sys.argv
    os.execv(sys.executable, argv)


@app.post("/api/ytdlp-update")
def ytdlp_update() -> dict:
    result = downloader.update_ytdlp()
    if result["ok"]:
        threading.Thread(target=_delayed_restart, daemon=True).start()
    return result


@app.get("/api/settings", response_model=SettingsResponse)
def get_settings() -> dict:
    return store.get_settings()


@app.post("/api/settings", response_model=SettingsResponse)
def update_settings(req: SettingsUpdateRequest) -> dict:
    # NOTE: checked against every browser yt-dlp knows, NOT just the ones
    # usable on this OS - every settings form resends cookie_browser, so a
    # stricter check here would stop someone with an old "chrome" on Windows
    # from saving even an unrelated setting. cookie_opts() is what ignores an
    # unusable browser, and the Settings page says so.
    if req.cookie_mode == "browser" and req.cookie_browser not in downloader.SUPPORTED_COOKIE_BROWSERS:
        raise HTTPException(status_code=400, detail="Desteklenmeyen tarayici")
    # NOTE: a path that doesn't exist is rejected here rather than silently
    # ignored later - "cookies are on but nothing happens" is the worst
    # possible outcome for the user.
    if req.cookie_mode == "file":
        path = (req.cookie_file or "").strip()
        if not path or not os.path.isfile(path):
            raise HTTPException(status_code=400, detail="Cerez dosyasi bulunamadi")
    if req.download_speed_limit_mbps < 0:
        raise HTTPException(status_code=400, detail="Hiz siniri negatif olamaz")
    # NOTE: home_server_mode is only actually read once, at process startup
    # (see lifespan) - a live toggle needs a restart to take effect, same
    # restart dance as the yt-dlp/deps updaters and remote-access toggle.
    was_home_server_mode = bool(store.get_settings().get("home_server_mode"))
    result = store.save_settings(
        cookie_mode=req.cookie_mode,
        cookie_browser=req.cookie_browser,
        cookie_file=(req.cookie_file or "").strip(),
        default_audio_lang=(req.default_audio_lang or "").strip().lower(),
        download_speed_limit_mbps=req.download_speed_limit_mbps,
        home_server_mode=req.home_server_mode,
    )
    if req.home_server_mode != was_home_server_mode:
        threading.Thread(target=_delayed_restart, daemon=True).start()
    return result


# NOTE: never exported, and never accepted on import even if a hand-edited
# file includes them - a backup file is something people might share (moving
# to a new device, asking for help), and it must never be possible for the
# remote-access password to travel in it or be silently overwritten by
# importing someone else's file. The receiving device always sets its own
# password fresh (see docs/README's remote-access section).
#
# download_dir is left out for a different reason: it's a path on THIS
# machine. Restored on another computer (or into Docker) it would point at a
# folder that doesn't exist there.
_SETTINGS_BACKUP_EXCLUDED_KEYS = {
    "remote_access_password_salt",
    "remote_access_password_hash",
    "download_dir",
    "previous_download_dirs",
}


@app.get("/api/settings/export")
def export_settings() -> Response:
    settings = store.get_settings()
    exported_settings = {k: v for k, v in settings.items() if k not in _SETTINGS_BACKUP_EXCLUDED_KEYS}
    body = json.dumps(
        {
            "mediagrab_export_version": 1,
            "settings": exported_settings,
            "channels": store.list_channels(),
            "pending": store.get_pending(),
        },
        ensure_ascii=False,
        indent=2,
    )
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=mediagrab-yedek.json"},
    )


@app.post("/api/settings/import")
def import_settings(req: SettingsImportRequest) -> dict:
    safe_settings = {
        k: v
        for k, v in req.settings.items()
        if k in store.DEFAULT_SETTINGS and k not in _SETTINGS_BACKUP_EXCLUDED_KEYS
    }
    if safe_settings:
        store.save_settings(**safe_settings)
    store.replace_channels(
        [c.model_dump() for c in req.channels],
        [p.model_dump() for p in req.pending],
    )
    return {"ok": True}


@app.post("/api/settings/test-cookies")
def test_cookies() -> dict:
    return downloader.test_cookie_source()


@app.get("/api/cookie-browsers")
def cookie_browsers() -> dict:
    # NOTE: is_docker - a container has no browser profile to read, so the
    # Settings page hides the "From browser" option there entirely.
    return {
        # NOTE: only what works on THIS OS (on Windows: Firefox only) - see
        # downloader.usable_cookie_browsers for why.
        "browsers": list(downloader.usable_cookie_browsers()),
        "platform": sys.platform,
        "is_docker": is_docker(),
    }


def _is_uploaded_cookie_file(path: str) -> bool:
    return bool(path) and os.path.normcase(os.path.abspath(path)) == os.path.normcase(
        os.path.abspath(downloader.COOKIES_PATH)
    )


@app.get("/api/cookies")
def cookie_status() -> dict:
    # NOTE: a summary only (sites, counts, whether a YouTube session is in
    # there) - no route ever returns cookie names or values, so nothing that
    # can read this page (a logged-in remote device included) can lift a
    # session out of it.
    settings = store.get_settings()
    path = settings.get("cookie_file") or ""
    uploaded = _is_uploaded_cookie_file(path)
    return {
        "mode": settings.get("cookie_mode", "off"),
        "source": ("uploaded" if uploaded else "path") if path else None,
        # NOTE: a path the user typed themselves is shown back to them; the
        # uploaded file's internal location (a container path in Docker) isn't
        # something they ever need to see or type.
        "path": None if uploaded else (path or None),
        "uploaded_at": (settings.get("cookie_uploaded_at") or None) if uploaded else None,
        "summary": downloader.cookie_file_summary(path),
    }


def _cookie_error(exc: "downloader.CookieFileError") -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@app.post("/api/cookies/inspect")
def cookie_inspect(req: CookieInspectRequest) -> dict:
    try:
        return downloader.inspect_cookie_text(req.content)
    except downloader.CookieFileError as exc:
        raise _cookie_error(exc)


@app.post("/api/cookies/upload")
def cookie_upload(req: CookieUploadRequest) -> dict:
    try:
        summary = downloader.save_uploaded_cookies(req.content, req.sites)
    except downloader.CookieFileError as exc:
        raise _cookie_error(exc)
    # NOTE: uploading IS the choice - switching to file mode pointed at the
    # uploaded copy here saves a separate "Save" click that would be easy to
    # forget (leaving cookies uploaded but unused).
    store.save_settings(
        cookie_mode="file",
        cookie_file=downloader.COOKIES_PATH,
        cookie_uploaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    return summary


@app.delete("/api/cookies")
def cookie_delete() -> dict:
    settings = store.get_settings()
    removed = downloader.delete_uploaded_cookies()
    # NOTE: only un-points the setting when it pointed at the uploaded copy - a
    # path the user typed in themselves is their file, left alone.
    if _is_uploaded_cookie_file(settings.get("cookie_file") or ""):
        mode = settings.get("cookie_mode", "off")
        store.save_settings(cookie_mode="off" if mode == "file" else mode, cookie_file="", cookie_uploaded_at="")
    return {"ok": True, "removed": removed}


@app.get("/api/ffmpeg-version")
def ffmpeg_version() -> dict:
    # NOTE: in Docker ffmpeg is baked into the image, so the per-OS install
    # commands are meaningless there (and "your system" would say Linux - the
    # container's OS, not the user's). The same goes for the Windows
    # installer, which ships its own ffmpeg (paths.bundled_ffmpeg_dir).
    return {**deps.check_ffmpeg(), "is_docker": is_docker(), "bundled": bundled_ffmpeg_dir() is not None}


@app.get("/api/dependencies")
def dependencies() -> dict:
    # NOTE: is_docker tells the Settings page whether to offer the update
    # button below at all - a container's own filesystem changes (unlike
    # yt-dlp's, which use a volume-mounted PYTHONUSERBASE override, see
    # downloader.update_ytdlp) don't survive the image being recreated, so
    # "update in place" would be silently undone the next time someone pulls
    # a new image. See the route below, which refuses the same way server-side.
    return {**deps.check_dependencies(), "is_docker": is_docker()}


@app.post("/api/dependencies-update")
def dependencies_update() -> dict:
    if is_docker():
        raise HTTPException(
            status_code=400,
            detail="Docker'da bagimliliklar image icine gomulu - guncellemek icin 'docker pull' yapin.",
        )
    result = deps.update_dependencies()
    if result["ok"]:
        # NOTE: the freshly installed packages are only picked up by a new
        # process - same restart dance as the yt-dlp update.
        threading.Thread(target=_delayed_restart, daemon=True).start()
    return result


@app.get("/api/history", response_model=list[HistoryItem])
def history() -> list[dict]:
    # NOTE: recursive walk - downloads now land in per-channel subfolders, but
    # older files from before that change may still sit flat in DOWNLOAD_DIR,
    # so both must keep showing up here.
    items = []
    downloads = downloader.download_dir()
    for root, _dirs, files in os.walk(downloads):
        for name in files:
            path = os.path.join(root, name)
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext not in HISTORY_EXTS or not os.path.isfile(path):
                continue
            rel = os.path.relpath(path, downloads).replace(os.sep, "/")
            folder = rel.rsplit("/", 1)[0] if "/" in rel else None
            stat = os.stat(path)
            items.append(
                {
                    "filename": rel,
                    "folder": folder,
                    "ext": ext,
                    "size": downloader.human_size(stat.st_size),
                    "downloaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                }
            )
    items.sort(key=lambda x: x["downloaded_at"], reverse=True)
    return items


@app.get("/api/history/file/{filename:path}/download")
def history_download(filename: str, request: Request) -> FileResponse:
    # NOTE: the counterpart to /api/history/file - see /api/file/{job_id}/download
    # (including _relay_delete_background, which this shares).
    #
    # Registered BEFORE the plain /api/history/file/{filename:path} route
    # below, and this order is load-bearing: FastAPI/Starlette try routes in
    # registration order, and {filename:path} matches literal "/" characters
    # too - greedy enough to swallow this route's own literal "/download"
    # suffix as part of `filename` if the plain route were tried first
    # (reproduced directly - see tests/test_app.py's ordering regression test).
    path = _history_path(filename)
    background = _relay_delete_background(path, _is_same_machine(request))
    return FileResponse(path, filename=os.path.basename(path), background=background)


@app.post("/api/history/file/{filename:path}/saved")
def history_saved(filename: str) -> dict:
    return _confirm_saved(_history_path(filename))


@app.get("/api/history/file/{filename:path}")
def history_file(filename: str) -> dict:
    # NOTE: see the matching comment on /api/file/{job_id} - this reveals the
    # already-archived file in the OS file explorer instead of also streaming
    # a duplicate copy through the browser's own downloads folder.
    path = _history_path(filename)
    downloader.reveal_in_explorer(path)
    return {"ok": True}


def _guess_image_mime(data: bytes) -> str:
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return "image/jpeg"


# NOTE: extracting one cover costs an ffprobe AND an ffmpeg subprocess
# (~0.5s measured). The history grid asks for one per card, so without
# caching a 40-item library meant 80 process spawns and several seconds of
# waiting on EVERY page load. Two layers fix that:
#   1. an in-process memo, keyed by (path, mtime, size) so a re-downloaded
#      file with the same name still produces a fresh cover;
#   2. ETag + Cache-Control on the response, so the browser normally doesn't
#      even re-request it (and gets a cheap 304 when it revalidates).
_THUMB_CACHE: dict[str, tuple[str, Optional[bytes]]] = {}
_THUMB_CACHE_LIMIT = 500
_thumb_cache_lock = threading.Lock()


def _thumb_version(path: str) -> str:
    stat = os.stat(path)
    return f"{int(stat.st_mtime)}-{stat.st_size}"


def _cached_thumbnail(path: str, version: str) -> Optional[bytes]:
    with _thumb_cache_lock:
        cached = _THUMB_CACHE.get(path)
        if cached and cached[0] == version:
            return cached[1]

    # NOTE: deliberately outside the lock - extraction shells out and is slow,
    # so holding the lock would serialize every thumbnail request.
    thumb = downloader.extract_thumbnail(path)

    with _thumb_cache_lock:
        if len(_THUMB_CACHE) >= _THUMB_CACHE_LIMIT:
            _THUMB_CACHE.clear()
        _THUMB_CACHE[path] = (version, thumb)
    return thumb


@app.get("/api/history/thumb/{filename:path}")
def history_thumb(request: Request, filename: str) -> Response:
    path = _history_path(filename)
    version = _thumb_version(path)
    etag = f'"{version}"'

    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": "private, max-age=86400"})

    thumb = _cached_thumbnail(path, version)
    if not thumb:
        raise HTTPException(status_code=404, detail="Kapak resmi yok")
    return Response(
        content=thumb,
        media_type=_guess_image_mime(thumb),
        headers={"ETag": etag, "Cache-Control": "private, max-age=86400"},
    )


_STREAM_MIME_TYPES = {
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "opus": "audio/ogg",
    "mp4": "video/mp4",
}


@app.get("/api/history/stream/{filename:path}")
def history_stream(filename: str) -> FileResponse:
    # NOTE: unlike /api/history/file, this deliberately omits the `filename=`
    # argument - that sets Content-Disposition: attachment, which makes the
    # browser save the file instead of playing it inline in <audio>/<video>.
    # FileResponse supports Range requests out of the box, so seeking works.
    path = _history_path(filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media_type = _STREAM_MIME_TYPES.get(ext)
    if not media_type:
        raise HTTPException(status_code=415, detail="Bu dosya turu onizlenemez")
    return FileResponse(path, media_type=media_type)


def _remove_sidecar_json(path: str) -> None:
    json_path = downloader.metadata_sidecar_path(path)
    if os.path.isfile(json_path):
        os.remove(json_path)


def _cleanup_empty_dir(path: str) -> None:
    # NOTE: best-effort - after deleting the last file in a per-channel
    # folder, remove the now-empty folder too so indirilenler/ doesn't
    # accumulate stray empty channel folders over time.
    download_dir = os.path.abspath(downloader.download_dir())
    parent = os.path.abspath(os.path.dirname(path))
    if parent != download_dir and os.path.isdir(parent) and not os.listdir(parent):
        try:
            os.rmdir(parent)
        except OSError:
            pass


@app.get("/api/history/json/{filename:path}")
def history_json(filename: str) -> FileResponse:
    path = _history_path(filename)
    json_path = downloader.metadata_sidecar_path(path)
    if not os.path.isfile(json_path):
        raise HTTPException(status_code=404, detail="Meta veri bulunamadi")
    return FileResponse(json_path, filename=os.path.basename(json_path), media_type="application/json")


@app.delete("/api/history/{filename:path}")
def delete_history(filename: str) -> dict:
    path = _history_path(filename)
    os.remove(path)
    _remove_sidecar_json(path)
    _cleanup_empty_dir(path)
    return {"ok": True}


@app.delete("/api/history")
def clear_history() -> dict:
    removed = 0
    folder = downloader.download_dir()
    for root, _dirs, files in os.walk(folder):
        for name in files:
            path = os.path.join(root, name)
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext in HISTORY_EXTS and os.path.isfile(path):
                os.remove(path)
                _remove_sidecar_json(path)
                removed += 1
    for entry in os.listdir(folder):
        sub = os.path.join(folder, entry)
        if os.path.isdir(sub) and not os.listdir(sub):
            try:
                os.rmdir(sub)
            except OSError:
                pass
    return {"ok": True, "removed": removed}


def _fmt_duration(seconds: Optional[int]) -> Optional[str]:
    if not seconds:
        return None
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _fmt_number(value: float, lang: str) -> str:
    # NOTE: 30.0 -> "30", 29.97 -> "29.97" ("29,97" in Turkish).
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text.replace(".", ",") if lang == "tr" else text


def _stream_rows(info: dict, lang: str) -> list[tuple[str, str]]:
    """The detail page's "what's in this file" rows, already formatted."""
    ui = ui_text(lang)
    rows = []
    video = info.get("video")
    if video:
        resolution = f"{video['width']}×{video['height']}"
        if video.get("quality"):
            resolution += f" ({video['quality']})"
        if video.get("fps"):
            resolution += f" · {_fmt_number(video['fps'], lang)} fps"
        rows.append((ui["item_resolution"], resolution))
        if video.get("codec"):
            rows.append((ui["item_video_codec"], video["codec"]))
    audio = info.get("audio")
    if audio:
        parts = [audio["codec"]] if audio.get("codec") else []
        if audio.get("sample_rate"):
            parts.append(f"{_fmt_number(audio['sample_rate'] / 1000, lang)} kHz")
        channels = audio.get("channels")
        if channels == 1:
            parts.append(ui["item_channels_mono"])
        elif channels == 2:
            parts.append(ui["item_channels_stereo"])
        elif channels:
            parts.append(ui["item_channels_n"].format(n=channels))
        if audio.get("bitrate_kbps"):
            parts.append(f"{audio['bitrate_kbps']} kbps")
        if parts:
            rows.append((ui["item_audio"], " · ".join(parts)))
    return rows


@app.get("/item/{filename:path}")
def item_detail(request: Request, filename: str, lang: Optional[str] = None):
    lang = _resolve_lang(lang, request)
    path = _history_path(filename)
    stat = os.stat(path)
    base_name = filename.rsplit("/", 1)[-1]
    ext = base_name.rsplit(".", 1)[-1].lower() if "." in base_name else ""
    meta = downloader.get_metadata(path)
    # NOTE: goes through the same memo as the /thumb endpoint - this page only
    # needs to know WHETHER a cover exists, and the <img> it renders will ask
    # for the bytes right after, so extracting twice would be pure waste.
    has_thumb = _cached_thumbnail(path, _thumb_version(path)) is not None
    has_metadata = os.path.isfile(downloader.metadata_sidecar_path(path))
    folder = filename.rsplit("/", 1)[0] if "/" in filename else None

    context = {
        "lang": lang,
        "ui": ui_text(lang),
        "filename": base_name,
        "filename_url": _url_path_quote(filename),
        "folder": folder,
        "ext": ext,
        "size": downloader.human_size(stat.st_size),
        "downloaded_at": datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
        "has_thumb": has_thumb,
        "has_metadata": has_metadata,
        "title": meta["title"] or base_name,
        "artist": meta["artist"],
        "duration_label": _fmt_duration(meta["duration"]),
        "stream_rows": _stream_rows(downloader.get_stream_info(path), lang),
        "is_local": _is_local_request(request),
    }
    return templates.TemplateResponse(request, "item.html", context)


@app.get("/api/channels", response_model=list[ChannelItem])
def list_channels() -> list[dict]:
    return store.list_channels()


@app.post("/api/channels", response_model=ChannelItem)
def add_channel(req: ChannelAddRequest) -> dict:
    try:
        info = downloader.resolve_channel(req.url)
    except downloader.ProbeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return store.add_channel(
        url=info["url"],
        name=info["name"],
        thumbnail=info["thumbnail"],
        mode=req.mode,
        choice_kind=req.choice_kind,
        choice=req.choice,
        last_video_id=info["last_video_id"],
    )


@app.get("/api/channels/pending", response_model=list[PendingVideo])
def get_pending_videos() -> list[dict]:
    return store.get_pending()


@app.delete("/api/channels/pending")
def clear_pending_videos() -> dict:
    store.clear_pending()
    return {"ok": True}


# NOTE: the two literal "/pending" routes above MUST be registered before the
# "/{channel_id}" routes below - FastAPI matches routes in registration
# order, so a parameterized route registered first would swallow "pending" as
# if it were a channel_id (this was a real bug: DELETE /api/channels/pending
# matched delete_channel("pending") instead, silently doing nothing).
@app.delete("/api/channels/{channel_id}")
def delete_channel(channel_id: str) -> dict:
    store.remove_channel(channel_id)
    return {"ok": True}


@app.post("/api/channels/{channel_id}/check")
def check_channel_now(channel_id: str) -> dict:
    channels = {c["id"]: c for c in store.list_channels()}
    channel = channels.get(channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="Kanal bulunamadi")
    _check_channel(channel)
    return {"ok": True}
