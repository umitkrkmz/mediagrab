# Project map

Read this before grepping. One line per file: what it is, where to look.
Guarded by `tests/test_maps.py` — every file in the repo must be listed here (a
directory entry ending in `/` covers its contents), so this stays current.

Stack: FastAPI + Jinja2 + vanilla JS, no build step, no database. State lives
in JSON files beside the app. yt-dlp does the downloading, ffmpeg the merging.

## Invariants (things that are true on purpose)

- `yt_dlp` is imported **only** in `mediagrab/downloader.py`. Every other module goes through it.
- **Two separate i18n systems, don't mix them:** `mediagrab/i18n.py` `UI` dict → server-rendered Jinja text (`{{ ui.some_key }}`, snake_case, single source for first paint); `mediagrab/static/app.js` `I18N` dict → strings the client (re)builds at runtime (camelCase, e.g. dynamic `<option>` labels, card HTML, dock rows). A key used in a template must exist in `i18n.py`; a key used in JS must exist in `app.js`.
- No DB: `channels.json` and `settings.json` (both gitignored) via `mediagrab/store.py`; downloads go to `indirilenler/<uploader>/`.
- User data is never overwritten destructively — see `_backup_existing_outputs` / `_restore_backups` in `downloader.py` and `USER_DATA_ENTRIES` in `setup_mediagrab.py`.
- `setup_mediagrab.py` runs before the package exists: stdlib-only, never imports `mediagrab` (tests enforce both).
- Static assets are cache-busted with `?v=<mtime>` via the `asset_version` Jinja global (`app.py`).
- Remote (LAN) access requires BOTH `remote_access_enabled` AND a password hash to be set (`store.remote_access_active`) - the same predicate gates the login middleware (`app.py`) and the bind-host decision (`run.py`), so "login required" and "reachable beyond localhost" can never drift apart.
- Videos are `mp4` with one audio track, or `mkv` when more than one audio track is embedded. Any list of "media extensions" (`HISTORY_EXTS` in `app.py`, `VIDEO_EXTS`/`THUMBNAILABLE_EXTS` in `app.js`) must include both.

## Backend — `mediagrab/`

| File | Purpose | Look here for |
|---|---|---|
| `mediagrab/app.py` | FastAPI app: page routes, `/api/*` endpoints, job runner, channel checks, history/thumbnail serving | `_run_job` (download thread + status), `_set_job` (the only place a job's fields change - also broadcasts), `_broadcast_job_event`/`_event_queues`/`/api/events` (SSE push, replaces the dock's old polling), `_check_channel` (auto-download), `_history_path` (path-traversal guard), `HISTORY_EXTS`, `_page_context`/`_resolve_lang`, `_sweep_orphaned_parts`/`_cleanup_partial_download`, `lifespan` (also captures the asyncio event loop for SSE), `_RequireLoginForRemoteAccess` (the auth middleware - plain ASGI, not `@app.middleware("http")`, see its own docstring for why), `_PUBLIC_PATHS`, `lan_ip` (shared with run.py's own startup print), `_is_local_request` (127.0.0.1/::1 vs a LAN device), `_relay_delete_background`/`_delete_relayed_file` (deletes a file after a REMOTE device's download only, and only in `remote_download_mode: "relay"` - see `store.py`), `_has_enough_disk_space` (checked both when `/api/download` queues a job and again inside `_run_job` right before it actually starts - a playlist bulk download can fill the disk mid-batch) |
| `mediagrab/auth.py` | Password hashing (PBKDF2, stdlib-only) and in-memory sessions for the optional remote-access login | `hash_password`/`verify_password`, `create_session`/`is_valid_session`/`destroy_session`/`clear_all_sessions`, `list_sessions`/`destroy_session_by_id` (the "connected devices" list in Settings - `id` is a non-secret display handle, never the real cookie token), `describe_user_agent`, `SESSION_COOKIE_NAME` |
| `mediagrab/downloader.py` | The only yt-dlp wrapper | `probe` (what the UI lists: formats, subtitles, audio tracks, description), `download`, `_video_opts` (format selector, multi-track → mkv + `allow_multiple_audio_streams`), `_audio_opts`, `_dedupe_video_formats` (size estimate + tbr cap), `_audio_track_list`, `_subtitle_list`, `_transcript_language`, `_vtt_to_text`, `cookie_opts`, `resolve_channel`/`check_channel_new_videos`, `get_metadata`/`extract_thumbnail` (ffprobe/ffmpeg subprocesses), `check_ytdlp_update`/`update_ytdlp` |
| `mediagrab/models.py` | Pydantic request/response models for every `/api/*` route | `DownloadRequest` (`audio_langs` is a list), `StatusResponse`, `HistoryItem`, `ChannelItem` |
| `mediagrab/i18n.py` | Server-side UI strings, `UI = {"tr": {...}, "en": {...}}` (keys must match; `test_i18n.py`) | `ui_text(lang)`; nav labels, page titles, settings labels, hints |
| `mediagrab/store.py` | JSON persistence: followed channels, pending videos, settings | `get_settings`/`save_settings` (`DEFAULT_SETTINGS`: cookies, default audio lang, remote-access password hash, `remote_download_mode`: `"keep"` a personal computer keeps every download permanently (default), `"relay"` a storage-constrained host (e.g. Raspberry Pi) deletes its own copy right after a REMOTE device's download completes - the host's own downloads are never auto-deleted in either mode), `remote_access_active`, `add_channel`/`update_channel`, `add_pending` |
| `mediagrab/deps.py` | Environment checks for the Settings page | `check_ffmpeg`, `check_dependencies` (venv vs PyPI), `update_dependencies`, `_requirement_names` (parses `requirements.txt`) |
| `mediagrab/paths.py` | `app_dir()` (where JSON/downloads live) and `resource_dir()` (templates/static), source vs PyInstaller-frozen | — |
| `mediagrab/__init__.py` | empty package marker | — |

## Frontend — `mediagrab/templates/`, `mediagrab/static/`

| File | Purpose |
|---|---|
| `mediagrab/templates/base.html` | Layout: sticky header + nav (home, history, channels, supported sites, settings, about), theme toggle, TR/EN switch, footer, download dock container; loads `style.css`/`app.js` with `asset_version` |
| `mediagrab/templates/index.html` | Home: hero, URL input + paste + resolve, `#card` (filled by `renderCard` / `renderPlaylist` in JS), pending-channel banner, recent downloads |
| `mediagrab/templates/history.html` | History: search, channel filter, dynamic type filter, grid/list toggle, `#history-list` |
| `mediagrab/templates/item.html` | One downloaded file: metadata, reveal-in-explorer, in-page preview player, JSON sidecar link |
| `mediagrab/templates/channels.html` | Follow a channel (notify / auto-download), followed list |
| `mediagrab/templates/settings.html` | Sidebar tabs (`data-tab`/`data-panel`, hash-routed): theme, default audio track (+ language-codes link), cookies, remote access (enable toggle, LAN address, storage mode keep/relay, password change, connected devices), version checks (yt-dlp/ffmpeg/deps), feedback |
| `mediagrab/templates/supported_sites.html` | Categorised, clickable site chips with brand colour + local logo (Jinja macro) |
| `mediagrab/templates/about.html` | What MediaGrab is, GPL-3.0 licence, GitHub/issues/changelog links (inline TR/EN) |
| `mediagrab/templates/login.html` | Standalone (doesn't extend base.html - no nav to pages behind the gate) password prompt shown only when remote access is active and there's no valid session |
| `mediagrab/static/app.js` | All client logic, one file, plain script (top-level functions are globals). Sections in order: DOM roots → theme → `I18N` (TR/EN, incl. `audioTrackNames` code→name map) → state (`lastProbe`, `selectedSubtitles`, `selectedAudioLangs`) → home page (`probe`, `renderCard` with audio/video tabs + description, `renderPlaylist`, `startDownload`) → download dock (`ensureJobEventStream`/`applyJobUpdate`, one shared `/api/events` SSE connection, localStorage-tracked job ids) → `loadClientInfo`/`isLocalClient`/`revealFile` (reveal-in-explorer on the host vs a real `/download` for a LAN device) → history (`loadHistory`, filters, view mode) → channels/pending → settings (yt-dlp/ffmpeg/deps, tab routing `showSettingsTab`, cookies, default audio lang, remote access: `toggleRemoteAccess`, `saveRemoteAccessStorageMode`/`renderRemoteAccessStorageMode` (keep/relay), `saveRemoteAccessPassword`, `loadRemoteAccessDevices`/`revokeRemoteAccessDevice`) → `updateHeaderHeightVar` (sticky preview offset) |
| `mediagrab/static/style.css` | All styles; design tokens on `:root` (`--bg`, `--surface`, `--accent`, …), dark-first with light overrides; `.result-layout` (1/3 preview sticky : 2/3 options), `.format-tabs`, `.settings-layout`, `#history-list.view-list`, `.sites-chip`, `.download-dock` |
| `mediagrab/static/sw.js` | PWA service worker (served at `/sw.js` by `app.py`) |
| `mediagrab/static/manifest.json` | PWA manifest |
| `mediagrab/static/qrcode.js` | Third-party (MIT, davidshimjs/qrcodejs), unmodified - local file, not CDN-loaded, matching the app's offline/local philosophy. Only loaded on `/settings` (see its `<script>` tag there); renders the remote-access LAN address as a scannable QR code |
| `mediagrab/static/icon.svg` | App icon |
| `mediagrab/static/icons/` | Brand logos for supported sites + GitHub (Simple Icons, CC0, colour baked into `fill`, kept local — not hotlinked) |

## Entry points, packaging, CI

| File | Purpose |
|---|---|
| `run.py` | `python run.py`: starts uvicorn on 127.0.0.1:8420 by default, or `0.0.0.0` when `store.remote_access_active()` says so (falls back to a free port if another app holds 8420), opens the browser |
| `setup_mediagrab.py` | Windows installer wizard (tkinter): welcome (install/repair/remove, TR/EN, Docker placeholder) → requirements → folder → summary → log. Remembers the last install folder in `%LOCALAPPDATA%/MediaGrab/installer.json`. Stdlib-only by design |
| `setup_mediagrab.spec` | PyInstaller spec for `MediaGrabSetup.exe` (built by CI on tag push) |
| `MediaGrab.spec` | Legacy PyInstaller spec for bundling the app itself; not built by CI, kept for reference |
| `.github/workflows/release.yml` | On `v*` tag: run tests → build installer exe → SHA256 → smoke-start the exe → GitHub Release |
| `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/ISSUE_TEMPLATE/feature_request.yml`, `.github/ISSUE_TEMPLATE/config.yml` | Issue forms linked from the in-app Feedback button |
| `requirements.txt` | Runtime deps (fastapi, uvicorn, yt-dlp, pydantic, jinja2, mutagen — the last one only because yt-dlp needs it for Opus cover art) |
| `requirements-dev.txt` | pytest, httpx2 (only for `fastapi.testclient.TestClient`, real HTTP round trips against the auth middleware) |
| `pytest.ini` | `testpaths = tests`, `pythonpath = .` |
| `.gitignore` | Ignores `indirilenler/`, `channels.json`, `settings.json`, venv, build output, `.claude/` |

## Tests — `tests/` (no network, seconds)

| File | Covers |
|---|---|
| `tests/test_app.py` | `app.py` helpers: path traversal, asset versioning, speed/ETA formatting, lang resolution, orphan/partial cleanup, `HISTORY_EXTS`, channel auto-download passing `audio_langs` |
| `tests/test_downloader.py` | Format selectors (`_video_opts` incl. multi-track), size-estimate capping, subtitle/transcript/audio-track listing, VTT parsing, channel URL normalisation, backup/restore |
| `tests/test_cookies.py` | Cookie source setting → yt-dlp options; privacy (no cookie contents stored); download speed limit → `ratelimit` option, incl. the `/api/settings` route's negative-value validation |
| `tests/test_settings.py` | `store.py` settings defaults/persistence, incl. cross-field independence between the speed limit and other settings |
| `tests/test_disk_space.py` | The disk-space guard (`_has_enough_disk_space`): the absolute floor, the estimate-plus-margin check, both call sites (`/api/download` refusing to queue a doomed job, and `_run_job` re-checking right before a queued job actually starts - the playlist-mid-batch scenario) |
| `tests/test_auth.py` | Password hashing, session lifecycle, `remote_access_active`, and (via `fastapi.testclient.TestClient`) the real login gate end to end: enable/disable, wrong password, logout, password-change signs out existing sessions |
| `tests/test_events.py` | The `/api/events` SSE stream: immediate ready comment, a broadcast job update reaching a connected client, `queue_position` matching a polled snapshot, cleanup on disconnect. Drives `job_events()`'s generator directly with `asyncio.run()` rather than `TestClient` (its streaming support hangs in this environment - see the file's own note; a real uvicorn server was confirmed live to stream correctly) |
| `tests/test_deps.py` | Version parsing, ffmpeg banner parsing, `requirements.txt` parsing, `mutagen` declared |
| `tests/test_i18n.py` | TR/EN key parity, no empty strings, placeholders match |
| `tests/test_frontend.py` | Pure `app.js` helpers run under Node (skipped without Node); shipped-file sanity |
| `tests/test_setup.py` | Installer: stdlib-only, no `mediagrab` import, string tables, probes, folder safety, remembered-folder state, and every wizard page rendered on one shared Tk root |
| `tests/test_maps.py` | Keeps `maps/` in sync with the repo (every file listed, every route listed) |

## Docs

| File | Purpose |
|---|---|
| `README.md` | Short landing page: what it is, install links, licence split, legal |
| `docs/README.tr.md`, `docs/README.en.md` | Full guides: features, install (installer + from source), running, channels, troubleshooting, structure, licences |
| `docs/language-codes.tr.md`, `docs/language-codes.en.md` | ISO 639-1 code ↔ name tables (linked from Settings → Default Audio Track) |
| `maps/project-map.md`, `maps/site-map.md` | This file and the route map |
| `CHANGELOG.md` | Per-release notes, TR then EN |
| `CONTRIBUTING.md`, `SECURITY.md`, `AGENTS.md` | Contributor guide, vulnerability reporting, rules for AI tools |
| `LICENSE`, `LICENSE-MIT` | GPL-3.0-or-later (v1.9.0+), MIT (v1.0.0–v1.8.0) |
