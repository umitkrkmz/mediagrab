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
- Videos are `mp4` with one audio track, or `mkv` when more than one audio track is embedded. Any list of "media extensions" (`HISTORY_EXTS` in `app.py`, `VIDEO_EXTS`/`THUMBNAILABLE_EXTS` in `app.js`) must include both.

## Backend — `mediagrab/`

| File | Purpose | Look here for |
|---|---|---|
| `mediagrab/app.py` | FastAPI app: page routes, `/api/*` endpoints, job runner, channel checks, history/thumbnail serving | `_run_job` (download thread + status), `_check_channel` (auto-download), `_history_path` (path-traversal guard), `HISTORY_EXTS`, `_page_context`/`_resolve_lang`, `_sweep_orphaned_parts`/`_cleanup_partial_download`, `lifespan` |
| `mediagrab/downloader.py` | The only yt-dlp wrapper | `probe` (what the UI lists: formats, subtitles, audio tracks, description), `download`, `_video_opts` (format selector, multi-track → mkv + `allow_multiple_audio_streams`), `_audio_opts`, `_dedupe_video_formats` (size estimate + tbr cap), `_audio_track_list`, `_subtitle_list`, `_transcript_language`, `_vtt_to_text`, `cookie_opts`, `resolve_channel`/`check_channel_new_videos`, `get_metadata`/`extract_thumbnail` (ffprobe/ffmpeg subprocesses), `check_ytdlp_update`/`update_ytdlp` |
| `mediagrab/models.py` | Pydantic request/response models for every `/api/*` route | `DownloadRequest` (`audio_langs` is a list), `StatusResponse`, `HistoryItem`, `ChannelItem` |
| `mediagrab/i18n.py` | Server-side UI strings, `UI = {"tr": {...}, "en": {...}}` (keys must match; `test_i18n.py`) | `ui_text(lang)`; nav labels, page titles, settings labels, hints |
| `mediagrab/store.py` | JSON persistence: followed channels, pending videos, settings | `get_settings`/`save_settings` (`DEFAULT_SETTINGS`: cookies, default audio lang), `add_channel`/`update_channel`, `add_pending` |
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
| `mediagrab/templates/settings.html` | Sidebar tabs (`data-tab`/`data-panel`, hash-routed): theme, default audio track (+ language-codes link), cookies, version checks (yt-dlp/ffmpeg/deps), feedback |
| `mediagrab/templates/supported_sites.html` | Categorised, clickable site chips with brand colour + local logo (Jinja macro) |
| `mediagrab/templates/about.html` | What MediaGrab is, GPL-3.0 licence, GitHub/issues/changelog links (inline TR/EN) |
| `mediagrab/static/app.js` | All client logic, one file, plain script (top-level functions are globals). Sections in order: DOM roots → theme → `I18N` (TR/EN, incl. `audioTrackNames` code→name map) → state (`lastProbe`, `selectedSubtitles`, `selectedAudioLangs`) → home page (`probe`, `renderCard` with audio/video tabs + description, `renderPlaylist`, `startDownload`) → download dock (`pollDockJob`, `renderDock`, localStorage-tracked job ids) → history (`loadHistory`, filters, view mode) → channels/pending → settings (yt-dlp/ffmpeg/deps, tab routing `showSettingsTab`, cookies, default audio lang) → `updateHeaderHeightVar` (sticky preview offset) |
| `mediagrab/static/style.css` | All styles; design tokens on `:root` (`--bg`, `--surface`, `--accent`, …), dark-first with light overrides; `.result-layout` (1/3 preview sticky : 2/3 options), `.format-tabs`, `.settings-layout`, `#history-list.view-list`, `.sites-chip`, `.download-dock` |
| `mediagrab/static/sw.js` | PWA service worker (served at `/sw.js` by `app.py`) |
| `mediagrab/static/manifest.json` | PWA manifest |
| `mediagrab/static/icon.svg` | App icon |
| `mediagrab/static/icons/` | Brand logos for supported sites + GitHub (Simple Icons, CC0, colour baked into `fill`, kept local — not hotlinked) |

## Entry points, packaging, CI

| File | Purpose |
|---|---|
| `run.py` | `python run.py`: starts uvicorn on 127.0.0.1:8420 (falls back to a free port if another app holds it), opens the browser |
| `setup_mediagrab.py` | Windows installer wizard (tkinter): welcome (install/repair/remove, TR/EN, Docker placeholder) → requirements → folder → summary → log. Remembers the last install folder in `%LOCALAPPDATA%/MediaGrab/installer.json`. Stdlib-only by design |
| `setup_mediagrab.spec` | PyInstaller spec for `MediaGrabSetup.exe` (built by CI on tag push) |
| `MediaGrab.spec` | Legacy PyInstaller spec for bundling the app itself; not built by CI, kept for reference |
| `.github/workflows/release.yml` | On `v*` tag: run tests → build installer exe → SHA256 → smoke-start the exe → GitHub Release |
| `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/ISSUE_TEMPLATE/feature_request.yml`, `.github/ISSUE_TEMPLATE/config.yml` | Issue forms linked from the in-app Feedback button |
| `requirements.txt` | Runtime deps (fastapi, uvicorn, yt-dlp, pydantic, jinja2, mutagen — the last one only because yt-dlp needs it for Opus cover art) |
| `requirements-dev.txt` | pytest only |
| `pytest.ini` | `testpaths = tests`, `pythonpath = .` |
| `.gitignore` | Ignores `indirilenler/`, `channels.json`, `settings.json`, venv, build output, `.claude/` |

## Tests — `tests/` (no network, seconds)

| File | Covers |
|---|---|
| `tests/test_app.py` | `app.py` helpers: path traversal, asset versioning, speed/ETA formatting, lang resolution, orphan/partial cleanup, `HISTORY_EXTS`, channel auto-download passing `audio_langs` |
| `tests/test_downloader.py` | Format selectors (`_video_opts` incl. multi-track), size-estimate capping, subtitle/transcript/audio-track listing, VTT parsing, channel URL normalisation, backup/restore |
| `tests/test_cookies.py` | Cookie source setting → yt-dlp options; privacy (no cookie contents stored) |
| `tests/test_settings.py` | `store.py` settings defaults/persistence |
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
