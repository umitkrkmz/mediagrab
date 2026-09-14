import asyncio
import glob
import json
import re
import locale
import os
import shutil
import socket
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask

from . import auth, deps, downloader, store
from .i18n import ui_text
from .models import (
    ChannelAddRequest,
    ChannelItem,
    ClientInfoResponse,
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
from .paths import resource_dir


# NOTE: the running event loop, captured once at startup by `lifespan` below -
# needed so `_broadcast_job_event` (called from arbitrary download WORKER
# THREADS, see `_run_job`) can safely hand a value to an asyncio.Queue that
# only the main event loop thread is allowed to touch directly.
_event_loop: Optional[asyncio.AbstractEventLoop] = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # NOTE: replaces the deprecated @app.on_event("startup") hook.
    # This is a "check on launch" design, not a persistent background service -
    # the app only runs while opened, so followed channels are checked once
    # here rather than on a timer. See README for why.
    global _event_loop
    _event_loop = asyncio.get_running_loop()
    _sweep_orphaned_parts()
    threading.Thread(target=_check_all_channels, daemon=True).start()
    yield


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
    return {"lang": resolved, "active": active, "ui": ui_text(resolved)}


def lan_ip() -> Optional[str]:
    # NOTE: shared with run.py's own startup print AND the Settings ->
    # Remote Access address panel - both must always agree on what "the LAN
    # address" is, so there's exactly one implementation of it.
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return None


def _is_local_request(request: Request) -> bool:
    # NOTE: request.client can be None on some ASGI transports (e.g. certain
    # test harnesses) - treated as "local" to match this app's pre-existing,
    # loopback-only behaviour rather than accidentally locking the host out.
    client = request.client
    return client is None or client.host in ("127.0.0.1", "::1")


@app.get("/api/client-info", response_model=ClientInfoResponse)
def client_info(request: Request) -> dict:
    return {"is_local": _is_local_request(request)}


def _history_path(rel_path: str) -> str:
    # NOTE: rel_path may include a channel subfolder (e.g. "Kanal Adi/Video.mp4")
    # now that downloads are auto-organized - os.path.commonpath guards against
    # ".." escaping DOWNLOAD_DIR while still allowing that one nesting level.
    download_dir = os.path.abspath(downloader.DOWNLOAD_DIR)
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


def _broadcast_job_event(job_id: str, job: dict) -> None:
    with _event_queues_lock:
        queues = list(_event_queues)
    if not queues or _event_loop is None:
        return
    payload = json.dumps({"job_id": job_id, **job})
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
    free = shutil.disk_usage(downloader.DOWNLOAD_DIR).free
    if estimated_size_bytes:
        return free >= estimated_size_bytes * _DISK_SPACE_SAFETY_MARGIN
    return free >= _MIN_FREE_DISK_BYTES


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


# NOTE: yt-dlp downloads video and audio as separate streams named
# "<stem>.f<format_id>.<ext>" and deletes them once ffmpeg has merged the two.
# If the merge never runs - cancelled, ffmpeg failed, process killed - they
# survive, and the ".part"/".ytdl" sweep below never sees them because a
# finished stream carries neither marker. They are large (a 1080p video stream
# runs to hundreds of MB), so they are worth deleting rather than hiding.
# OUTTMPL has no %(format_id)s in it, so a file MediaGrab finished writing can
# never carry this infix.
_FORMAT_STREAM_RE = re.compile(r"^(?P<stem>.+)\.f\d+\.[^.]+$")


def _cleanup_partial_download(job_id: str) -> None:
    with jobs_lock:
        tmp = (jobs.get(job_id) or {}).get("tmpfile")
    if not tmp:
        return
    download_dir = os.path.abspath(downloader.DOWNLOAD_DIR)
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
    for root, _dirs, files in os.walk(downloader.DOWNLOAD_DIR):
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
                executor.submit(
                    _run_job, job_id, v["url"], channel["choice_kind"], channel["choice"], [], audio_langs
                )
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
    if active:
        ip = lan_ip()
        if ip:
            port = request.url.port or 8420
            lan_url = f"http://{ip}:{port}"
    return {
        "enabled": bool(settings.get("remote_access_enabled")),
        "has_password": bool(settings.get("remote_access_password_hash")),
        "lan_url": lan_url,
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
        _run_job, job_id, req.url, req.kind, req.choice, req.subtitle_langs, req.audio_langs, req.estimated_size_bytes
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
        return {**job, "queue_position": _queue_position(job)}


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


def _relay_delete_background(path: str, is_local: bool) -> Optional[BackgroundTask]:
    # NOTE: "relay" mode only ever applies to a REMOTE device's own transfer.
    # The host's own downloads are never auto-deleted in either mode - there
    # is no "other device" they were relayed to, so deleting the only copy
    # the user directly asked for on their own machine would just be data
    # loss with no corresponding benefit.
    if is_local or store.get_settings().get("remote_download_mode") != "relay":
        return None
    return BackgroundTask(_delete_relayed_file, path)


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
    background = _relay_delete_background(filepath, _is_local_request(request))
    return FileResponse(filepath, filename=os.path.basename(filepath), background=background)


@app.get("/api/locale", response_model=LocaleResponse)
def locale_info() -> dict:
    return {"lang": _detect_system_lang()}


@app.get("/api/ytdlp-version", response_model=YtdlpVersionResponse)
def ytdlp_version() -> dict:
    return downloader.check_ytdlp_update()


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
    return store.save_settings(
        cookie_mode=req.cookie_mode,
        cookie_browser=req.cookie_browser,
        cookie_file=(req.cookie_file or "").strip(),
        default_audio_lang=(req.default_audio_lang or "").strip().lower(),
        download_speed_limit_mbps=req.download_speed_limit_mbps,
    )


# NOTE: never exported, and never accepted on import even if a hand-edited
# file includes them - a backup file is something people might share (moving
# to a new device, asking for help), and it must never be possible for the
# remote-access password to travel in it or be silently overwritten by
# importing someone else's file. The receiving device always sets its own
# password fresh (see docs/README's remote-access section).
_SETTINGS_BACKUP_EXCLUDED_KEYS = {"remote_access_password_salt", "remote_access_password_hash"}


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
    return {"browsers": list(downloader.SUPPORTED_COOKIE_BROWSERS), "platform": sys.platform}


@app.get("/api/ffmpeg-version")
def ffmpeg_version() -> dict:
    return deps.check_ffmpeg()


@app.get("/api/dependencies")
def dependencies() -> dict:
    return deps.check_dependencies()


@app.post("/api/dependencies-update")
def dependencies_update() -> dict:
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
    for root, _dirs, files in os.walk(downloader.DOWNLOAD_DIR):
        for name in files:
            path = os.path.join(root, name)
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext not in HISTORY_EXTS or not os.path.isfile(path):
                continue
            rel = os.path.relpath(path, downloader.DOWNLOAD_DIR).replace(os.sep, "/")
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
    background = _relay_delete_background(path, _is_local_request(request))
    return FileResponse(path, filename=os.path.basename(path), background=background)


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
    download_dir = os.path.abspath(downloader.DOWNLOAD_DIR)
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
    for root, _dirs, files in os.walk(downloader.DOWNLOAD_DIR):
        for name in files:
            path = os.path.join(root, name)
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext in HISTORY_EXTS and os.path.isfile(path):
                os.remove(path)
                _remove_sidecar_json(path)
                removed += 1
    for entry in os.listdir(downloader.DOWNLOAD_DIR):
        sub = os.path.join(downloader.DOWNLOAD_DIR, entry)
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
