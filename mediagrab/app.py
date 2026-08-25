import glob
import locale
import os
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
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import deps, downloader, store
from .i18n import ui_text
from .models import (
    ChannelAddRequest,
    ChannelItem,
    DownloadRequest,
    DownloadStartResponse,
    HistoryItem,
    LocaleResponse,
    PendingVideo,
    ProbeRequest,
    SettingsResponse,
    SettingsUpdateRequest,
    StatusResponse,
    YtdlpVersionResponse,
)
from .paths import resource_dir


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # NOTE: replaces the deprecated @app.on_event("startup") hook.
    # This is a "check on launch" design, not a persistent background service -
    # the app only runs while opened, so followed channels are checked once
    # here rather than on a timer. See README for why.
    _sweep_orphaned_parts()
    threading.Thread(target=_check_all_channels, daemon=True).start()
    yield


app = FastAPI(lifespan=lifespan)

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

# NOTE: job records live in memory only and are lost on server restart.
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()
_job_counter = 0

# NOTE: at most 3 concurrent downloads; the rest queue up.
executor = ThreadPoolExecutor(max_workers=3)

# NOTE: we don't keep a separate DB for download history; the indirilenler/
# folder already holds the actual files, so the history list is built by
# reading that folder.
HISTORY_EXTS = {"mp3", "m4a", "opus", "mp4", "srt", "txt"}


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


def _set_job(job_id: str, **fields) -> None:
    with jobs_lock:
        jobs[job_id].update(fields)


def _format_speed(bytes_per_sec) -> Optional[str]:
    if not bytes_per_sec:
        return None
    speed = float(bytes_per_sec)
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if speed < 1024 or unit == "GB/s":
            return f"{speed:.1f} {unit}"
        speed /= 1024
    return None


class JobCancelled(Exception):
    """Raised inside a download's progress hook to abort it on request."""


def _job_cancelled(job_id: str) -> bool:
    with jobs_lock:
        job = jobs.get(job_id)
        return bool(job and job.get("cancel_requested"))


def _run_job(job_id: str, url: str, kind: str, choice: str, subtitle_langs: list[str]) -> None:
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
            )
        elif status == "finished":
            # NOTE: yt-dlp says "finished" here, but ffmpeg (merge/remux/encode)
            # may not have run yet; we don't count the job as "done" here.
            _set_job(job_id, state="isleniyor", percent=100.0, speed=None)

    def on_postprocess(d: dict) -> None:
        if d.get("status") == "started":
            _set_job(job_id, state="isleniyor")

    # NOTE: a job can be cancelled while it's still queued behind the
    # executor's 3 worker slots, so check once more before starting any work.
    if _job_cancelled(job_id):
        _set_job(job_id, state="iptal", speed=None)
        return

    try:
        _set_job(job_id, state="indiriliyor")
        filepath = downloader.download(url, kind, choice, on_progress, on_postprocess, subtitle_langs=subtitle_langs)
        _set_job(job_id, state="bitti", percent=100.0, ready=True, filepath=filepath)
    except JobCancelled:
        # NOTE: mark it cancelled BEFORE cleaning up - the cleanup waits for
        # the download's file handles to close, and the UI shouldn't sit on
        # "downloading" for those extra seconds.
        _set_job(job_id, state="iptal", speed=None)
        _cleanup_partial_download(job_id)
    except Exception as exc:
        # NOTE: yt-dlp wraps hook exceptions, so a cancel can surface here as a
        # generic DownloadError instead of JobCancelled - trust the flag, not
        # the exception type, or a cancelled job would be reported as failed.
        if _job_cancelled(job_id):
            _set_job(job_id, state="iptal", speed=None)
            _cleanup_partial_download(job_id)
        else:
            _set_job(job_id, state="hata", error=downloader.strip_ansi_codes(str(exc)))


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

    stale = []
    for candidate in candidates:
        path = os.path.abspath(candidate)
        name = os.path.basename(path)
        if not path.startswith(download_dir + os.sep):
            continue
        if ".part" not in name and not name.endswith(".ytdl"):
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
            for v in new_videos:
                job_id = uuid.uuid4().hex
                with jobs_lock:
                    jobs[job_id] = _new_job_record()
                executor.submit(_run_job, job_id, v["url"], channel["choice_kind"], channel["choice"], [])
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
    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = _new_job_record()
    executor.submit(_run_job, job_id, req.url, req.kind, req.choice, req.subtitle_langs)
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


@app.get("/api/locale", response_model=LocaleResponse)
def locale_info() -> dict:
    return {"lang": _detect_system_lang()}


@app.get("/api/ytdlp-version", response_model=YtdlpVersionResponse)
def ytdlp_version() -> dict:
    return downloader.check_ytdlp_update()


def _delayed_restart() -> None:
    # NOTE: os.execv replaces this process's image with a fresh one using the
    # exact same command line (sys.argv) that launched it - works the same
    # whether that was "python run.py" or "uvicorn mediagrab.app:app", since
    # both run this same process. The 1s delay lets the HTTP response for the
    # update request actually reach the browser before the process restarts.
    time.sleep(1.0)
    os.execv(sys.executable, [sys.executable] + sys.argv)


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
    return store.save_settings(
        cookie_mode=req.cookie_mode,
        cookie_browser=req.cookie_browser,
        cookie_file=(req.cookie_file or "").strip(),
    )


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
