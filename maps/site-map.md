# Site map (routes)

Every route in `mediagrab/app.py`, what it does, and which template / JS drives
it. Guarded by `tests/test_maps.py`: a route added to `app.py` must be added here.

All pages take `?lang=tr|en` (else cookie/OS locale, see `_resolve_lang`).
The download dock (`#download-dock`, bottom of every page) keeps one shared
`/api/events` (SSE) connection open and applies pushed job updates by
`job_id`; job ids are kept in `localStorage` so progress survives navigation.
A one-shot `GET /api/status/{job_id}` fills in the very first snapshot right
after a job is tracked (before any event has fired) and reconciles a job that
turns out to be gone (404 - almost always a server restart since it was
tracked) - see `refreshJobOnce` in app.js.

**Auth gate:** every route below except `/login`, `/api/login`, `/api/locale`,
`/sw.js` and `/static/*` goes through `_RequireLoginForRemoteAccess` in
`app.py`. It's a no-op unless `store.remote_access_active()` is true (remote
access turned on AND a password set) - see the invariant in
`maps/project-map.md`. When active, an unauthenticated page request gets
redirected to `/login`, an API request gets a 401.

**Keep vs. relay:** every download route branches on `_is_local_request` and
`store.get_settings()["remote_download_mode"]` via `_relay_delete_background`.
"keep" (default) never auto-deletes anything. "relay" deletes the host's own
copy, but ONLY after a REMOTE device's download has fully completed - the
host's own reveal/download of its own file is never affected either way.

## Pages (HTML, server-rendered via Jinja)

| Route | Template | Purpose | JS that drives it (`app.js`) |
|---|---|---|---|
| `/` | `index.html` | Paste a link → resolve → pick audio/video/subtitles/transcript → download. Playlists list their entries with range + bulk download. Shows pending channel videos and recent downloads. | `probe`, `renderCard`, `renderPlaylist`, `queuePlaylistRange`, `startDownload`, `renderPending`, `renderRecent` |
| `/history` | `history.html` | Downloaded files as cards or a compact list; search, channel + type filters; delete / clear all | `loadHistory`, `applyHistoryFilters`, `applyHistoryViewMode`, `deleteHistoryItem`, `clearAllHistory` |
| `/item/{filename:path}` | `item.html` | One file's detail: metadata, in-page preview, reveal in explorer, sidecar JSON | `itemRevealBtn`, `itemPreviewBtn` handlers |
| `/channels` | `channels.html` | Follow YouTube channels (notify / auto-download); checked once per app start | `loadChannels`, `addChannel`, `renderChannelList` |
| `/supported-sites` | `supported_sites.html` | Clickable, branded chips for popular yt-dlp sites + link to the full list | none (static) |
| `/settings` | `settings.html` | Sidebar tabs: theme · default audio track · cookies · version checks (yt-dlp, ffmpeg, Python deps) · feedback | `showSettingsTab` (hash routing), `renderThemeControls`, cookie panel, `loadYtdlpVersion`, `loadFfmpegVersion`, `loadDependencies` |
| `/about` | `about.html` | Project description, licence, GitHub / issues / changelog links | none (static) |
| `/login` | `login.html` | Password prompt for LAN access - only reachable (not auto-redirected away) when remote access is on and there's no valid session | inline script in the template itself, not app.js |
| `/sw.js` | — | Serves the PWA service worker from `static/` at the root scope | — |

## API — download flow

| Route | Method | Purpose |
|---|---|---|
| `/api/probe` | POST | Resolve a URL → `downloader.probe()`: title, uploader, duration, thumbnail, description, video formats (with size estimates), subtitles, transcript language, audio tracks; or a playlist listing |
| `/api/download` | POST | Start a job (`kind`: audio/video/transcript, `choice`, `subtitle_langs`, `audio_langs`); runs in a thread pool, returns `job_id` |
| `/api/status/{job_id}` | GET | Job state, percent, speed, ETA, queue position, error - one-shot snapshot |
| `/api/events` | GET | SSE stream (`text/event-stream`); pushes `{job_id, ...status fields}` for every job update, to every connected tab |
| `/api/cancel/{job_id}` | POST | Cancel a running job and clean partial files |
| `/api/file/{job_id}` | GET | Reveal the finished file in the OS file explorer (host client only) |
| `/api/file/{job_id}/download` | GET | Stream the actual bytes with `Content-Disposition: attachment` - what a remote device's dock uses instead (unambiguous with the route above since `{job_id}` can't contain a `/`, unlike the history pair) |

## API — history

| Route | Method | Purpose |
|---|---|---|
| `/api/history` | GET | List downloaded files (`HISTORY_EXTS`) with metadata, newest first |
| `/api/history/file/{filename:path}` | GET | Reveal a history file in the explorer (host client only, see `/api/client-info`) |
| `/api/history/file/{filename:path}/download` | GET | Stream the actual bytes with `Content-Disposition: attachment`, for a remote device that can't use "reveal in explorer" - **must stay registered before** the plain `{filename:path}` route above (that one's `:path` converter is greedy enough to swallow a literal `/download` suffix otherwise - reproduced directly, see the route's own comment and `tests/test_app.py`'s ordering regression test) |
| `/api/history/thumb/{filename:path}` | GET | Cover art via ffmpeg, cached + `ETag` |
| `/api/history/stream/{filename:path}` | GET | Stream a file for the in-page preview |
| `/api/history/json/{filename:path}` | GET | The metadata sidecar (`<file>.json`) |
| `/api/history/{filename:path}` | DELETE | Delete one file (+ sidecar, empty folder) |
| `/api/history` | DELETE | Delete everything in `indirilenler/` |

## API — channels

| Route | Method | Purpose |
|---|---|---|
| `/api/channels` | GET | Followed channels |
| `/api/channels` | POST | Follow a channel (`mode`: notify / auto, format choice) |
| `/api/channels/{channel_id}` | DELETE | Unfollow |
| `/api/channels/{channel_id}/check` | POST | Check one channel now |
| `/api/channels/pending` | GET | New videos found in notify mode (home-page banner) |
| `/api/channels/pending` | DELETE | Dismiss the pending list |

## API — settings & environment

| Route | Method | Purpose |
|---|---|---|
| `/api/settings` | GET | Current settings (cookie source, default audio language) |
| `/api/settings` | POST | Update settings |
| `/api/settings/test-cookies` | POST | Try reading cookies from the configured source |
| `/api/cookie-browsers` | GET | Browsers yt-dlp can read cookies from |
| `/api/locale` | GET | Server-detected language |
| `/api/client-info` | GET | `{is_local}` - whether THIS request came from the host machine (127.0.0.1/::1) or a LAN device; fetched once at page load (see `loadClientInfo` in app.js) and used to pick "reveal in explorer" vs a real "download to this device" action |
| `/api/ytdlp-version` | GET | Installed vs latest yt-dlp |
| `/api/ytdlp-update` | POST | `pip install -U yt-dlp`, then restart |
| `/api/ffmpeg-version` | GET | ffmpeg/ffprobe versions + install commands |
| `/api/dependencies` | GET | venv packages vs PyPI |
| `/api/dependencies-update` | POST | Update all, then restart |

## API — authentication & remote access

| Route | Method | Purpose |
|---|---|---|
| `/api/login` | POST | `{password}` -> verifies against the stored hash, sets the session cookie |
| `/api/logout` | POST | Destroys the current session and clears the cookie |
| `/api/remote-access` | GET | `{enabled, has_password, lan_url, download_mode}` - never the hash itself; `lan_url` only set once genuinely reachable |
| `/api/remote-access` | POST | `{enabled, download_mode}` - refuses to enable without a password set; restarts the server only when `enabled` actually flips (see `store.remote_access_active`/run.py's bind-host decision) - saving a `download_mode` change alone never restarts |
| `/api/remote-access/password` | POST | `{password}` (min 8 chars) - hashes and stores it, invalidates every existing session |
| `/api/remote-access/sessions` | GET | Connected devices: `{id, created_at, device, is_current}` per active session - `id` is a non-secret display handle, never the real cookie token |
| `/api/remote-access/sessions/{session_id}` | DELETE | Sign out one specific device by its `id` (e.g. "kick" a session that isn't this one) |
