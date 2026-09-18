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
| `mediagrab/app.py` | FastAPI app: page routes, `/api/*` endpoints, job runner, channel checks, history/thumbnail serving | `_run_job` (download thread + status), `_set_job` (the only place a job's fields change - also broadcasts), `_broadcast_job_event`/`_event_queues`/`/api/events` (SSE push, replaces the dock's old polling), `_check_channel` (auto-download), `_history_path` (path-traversal guard), `HISTORY_EXTS`, `_page_context`/`_resolve_lang`, `_sweep_orphaned_parts`/`_cleanup_partial_download`, `lifespan` (also captures the asyncio event loop for SSE), `_RequireLoginForRemoteAccess` (the auth middleware - plain ASGI, not `@app.middleware("http")`, see its own docstring for why), `_PUBLIC_PATHS`, `lan_ip` (shared with run.py's own startup print; checks `MEDIAGRAB_HOST_LAN_IP` first - a bridge-networked Docker container's own socket call would otherwise return its unreachable internal bridge IP, see `setup_mediagrab.py`'s `detect_host_lan_ip`), `_is_local_request` (127.0.0.1/::1 vs a LAN device), `_relay_delete_background`/`_delete_relayed_file` (deletes a file after a REMOTE device's download only, and only in `remote_download_mode: "relay"` - see `store.py`), `_has_enough_disk_space` (checked both when `/api/download` queues a job and again inside `_run_job` right before it actually starts - a playlist bulk download can fill the disk mid-batch), `_periodic_channel_check_loop` (only started by `lifespan` when `home_server_mode` is on - the launch-time check-once always runs regardless), `_submit_auto_download`/`_finish_auto_download` (reserves at least 1 of the executor's 3 slots for a manual download - channel auto-downloads queue behind `_MAX_CONCURRENT_AUTO_DOWNLOADS` instead of submitting straight to `executor`), `_register_mdns`/`_close_mdns` (best-effort "mediagrab.local" convenience address alongside `lan_url`, registered once in `lifespan` when remote access is active - never blocks or crashes the app on failure), `_ensure_docker_has_a_password` (refuses to start in Docker with no password - see `paths.is_docker`) |
| `mediagrab/auth.py` | Password hashing (PBKDF2, stdlib-only) and in-memory sessions for the optional remote-access login | `hash_password`/`verify_password`, `create_session`/`is_valid_session`/`destroy_session`/`clear_all_sessions`, `list_sessions`/`destroy_session_by_id` (the "connected devices" list in Settings - `id` is a non-secret display handle, never the real cookie token), `describe_user_agent`, `SESSION_COOKIE_NAME` |
| `mediagrab/downloader.py` | The only yt-dlp wrapper | `probe` (what the UI lists: formats, subtitles, audio tracks, description), `download`, `_video_opts` (format selector, multi-track → mkv + `allow_multiple_audio_streams`), `_audio_opts`, `_dedupe_video_formats` (size estimate + tbr cap), `_audio_track_list`, `_subtitle_list`, `_transcript_language`, `_vtt_to_text`, `cookie_opts`, `resolve_channel`/`check_channel_new_videos`, `get_metadata`/`extract_thumbnail` (ffprobe/ffmpeg subprocesses), `check_ytdlp_update`/`update_ytdlp` (installs with `--user` in Docker, landing in the `PYTHONUSERBASE` volume override instead of the container's own ephemeral filesystem) |
| `mediagrab/models.py` | Pydantic request/response models for every `/api/*` route | `DownloadRequest` (`audio_langs` is a list, `estimated_size_bytes` feeds the disk-space guard), `StatusResponse`, `HistoryItem`, `ChannelItem`, `SettingsImportRequest` (validates channels/pending as real models, `settings` stays a plain dict) |
| `mediagrab/i18n.py` | Server-side UI strings, `UI = {"tr": {...}, "en": {...}}` (keys must match; `test_i18n.py`) | `ui_text(lang)`; nav labels, page titles, settings labels, hints |
| `mediagrab/store.py` | JSON persistence: followed channels, pending videos, settings | `get_settings`/`save_settings` (`DEFAULT_SETTINGS`: cookies, default audio lang, remote-access password hash, `remote_download_mode`: `"keep"` a personal computer keeps every download permanently (default), `"relay"` a storage-constrained host (e.g. Raspberry Pi) deletes its own copy right after a REMOTE device's download completes - the host's own downloads are never auto-deleted in either mode), `remote_access_active`, `add_channel`/`update_channel`, `add_pending`, `replace_channels` (full replace, not merge - used by the settings-import route) |
| `mediagrab/deps.py` | Environment checks for the Settings page | `check_ffmpeg`, `check_dependencies` (venv vs PyPI), `update_dependencies` (refused by app.py's route in Docker - a container's own filesystem changes don't survive an image update, unlike yt-dlp's own `PYTHONUSERBASE` override), `_requirement_names` (parses `requirements.txt`) |
| `mediagrab/paths.py` | `app_dir()` (where JSON/downloads live) and `resource_dir()` (templates/static), source vs PyInstaller-frozen | `is_docker()` (`/.dockerenv` check - drives run.py's bind-host decision and app.py's mandatory-first-password check) |
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
| `run.py` | `python run.py`: starts uvicorn on 127.0.0.1:8420 by default, or `0.0.0.0` when `store.remote_access_active()` says so OR `paths.is_docker()` is true (a container always binds to 0.0.0.0 - see app.py's `_ensure_docker_has_a_password` for why that's still safe), falls back to a free port if another app holds 8420, opens the browser (skipped in Docker - no desktop to open one on) |
| `Dockerfile` | `python:3.12-slim` + ffmpeg + `requirements.txt`, no venv (see its own comment on why that matters for `PYTHONUSERBASE`) |
| `docker-compose.yml` | Example compose file: `network_mode: host` (Linux - real LAN IP + mDNS need it), volumes for `indirilenler/`/`settings.json`/`channels.json`/`pip-packages` (the last one is the yt-dlp `PYTHONUSERBASE` override), `MEDIAGRAB_INITIAL_PASSWORD`, commented `MEDIAGRAB_HOST_LAN_IP` (Docker Desktop/`ports` path only - fill in by hand, see its own comment and app.py's `lan_ip`) |
| `.dockerignore` | Keeps the host's own `settings.json`/`channels.json`/`indirilenler/` out of the build context - those only ever belong in volumes, never baked into an image |
| `setup_mediagrab.py` | Windows installer wizard (tkinter): welcome (install/repair/remove, TR/EN) → requirements → folder → summary → log. A separate "Docker ile kur" path: checks `docker`/`docker compose`/daemon readiness, writes a bridge-networked `docker-compose.yml` referencing the published `ghcr.io/umitkrkmz/mediagrab` image into a chosen folder (including `MEDIAGRAB_HOST_LAN_IP`, detected on the host by `detect_host_lan_ip()` - see app.py's `lan_ip`), runs `docker compose up -d`, then polls `http://localhost:8420` for a real response before declaring success. Remembers the last (source) install folder in `%LOCALAPPDATA%/MediaGrab/installer.json`. Stdlib-only by design |
| `setup_mediagrab.spec` | PyInstaller spec for `MediaGrabSetup.exe` (built by CI on tag push) |
| `MediaGrab.spec` | Legacy PyInstaller spec for bundling the app itself; not built by CI, kept for reference |
| `.github/workflows/release.yml` | On `v*` tag: run tests → build installer exe → SHA256 → smoke-start the exe → GitHub Release |
| `.github/workflows/docker.yml` | Builds the Docker image (QEMU + Buildx), smoke-starts an amd64 build locally; on a `v*` tag only, also builds+pushes a multi-arch (amd64+arm64) image to `ghcr.io/<owner>/mediagrab` tagged `latest` and the version |
| `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/ISSUE_TEMPLATE/feature_request.yml`, `.github/ISSUE_TEMPLATE/config.yml` | Issue forms linked from the in-app Feedback button |
| `requirements.txt` | Runtime deps (fastapi, uvicorn, yt-dlp, pydantic, jinja2, mutagen — the last one only because yt-dlp needs it for Opus cover art; zeroconf — the mDNS convenience address, the one deliberate exception to "avoid new dependencies", see its own comment) |
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
| `tests/test_home_server_mode.py` | `home_server_mode`: `/api/settings` only restarts when it actually changes, the periodic channel-check loop's sleep/check cadence, `lifespan` only starting that loop when the setting is on |
| `tests/test_queue_priority.py` | The auto-download slot cap (`_submit_auto_download`/`_finish_auto_download`): queuing past the limit, a finished slot handing off to a pending one, the slot freeing even when the job fails, and manual downloads (`/api/download`) never being subject to the cap at all |
| `tests/test_mdns.py` | `_register_mdns`/`_close_mdns` with a fake `Zeroconf` (no real network traffic): the happy path, reflecting a renamed hostname after a collision, failing silently on any error, and `_remote_access_status`'s `mdns_url` field (present only when active AND a hostname is actually registered) |
| `tests/test_docker.py` | `paths.is_docker`, `_ensure_docker_has_a_password` (refuses to start with no password and no `MEDIAGRAB_INITIAL_PASSWORD`, sets one from the env var when missing, leaves a deliberately-disabled password alone), `lifespan` only running that check inside Docker, and `lan_ip`'s `MEDIAGRAB_HOST_LAN_IP` override |
| `tests/test_run.py` | `run.main()`'s bind-host decision (loopback by default, `0.0.0.0` when remote access is active OR always in Docker), browser-opening skipped in Docker, the `MEDIAGRAB_PORT` env var, the already-running/port-fallback branches - all with `uvicorn.run` faked out so no real server starts |
| `tests/test_disk_space.py` | The disk-space guard (`_has_enough_disk_space`): the absolute floor, the estimate-plus-margin check, both call sites (`/api/download` refusing to queue a doomed job, and `_run_job` re-checking right before a queued job actually starts - the playlist-mid-batch scenario) |
| `tests/test_settings_backup.py` | `/api/settings/export`/`/import`: the security property (a backup file can never carry or accept the remote-access password hash, even hand-edited in), full round-trip, channel-list replace-not-merge, malformed-file rejection |
| `tests/test_auth.py` | Password hashing, session lifecycle, `remote_access_active`, and (via `fastapi.testclient.TestClient`) the real login gate end to end: enable/disable, wrong password, logout, password-change signs out existing sessions |
| `tests/test_events.py` | The `/api/events` SSE stream: immediate ready comment, a broadcast job update reaching a connected client, `queue_position` matching a polled snapshot, cleanup on disconnect. Drives `job_events()`'s generator directly with `asyncio.run()` rather than `TestClient` (its streaming support hangs in this environment - see the file's own note; a real uvicorn server was confirmed live to stream correctly) |
| `tests/test_deps.py` | Version parsing, ffmpeg banner parsing, `requirements.txt` parsing, `mutagen` declared |
| `tests/test_i18n.py` | TR/EN key parity, no empty strings, placeholders match |
| `tests/test_frontend.py` | Pure `app.js` helpers run under Node (skipped without Node); shipped-file sanity |
| `tests/test_setup.py` | Installer: stdlib-only, no `mediagrab` import, string tables, probes, folder safety, remembered-folder state, every wizard page rendered on one shared Tk root, and the Docker install mode (`docker_status()` branching, generated `docker-compose.yml` content/escaping, data-file safety, password/folder validation) |
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
