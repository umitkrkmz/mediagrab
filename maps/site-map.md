# Site map (routes)

Every route in `mediagrab/app.py`, what it does, and which template / JS drives
it. Guarded by `tests/test_maps.py`: a route added to `app.py` must be added here.

All pages take `?lang=tr|en` (else cookie/OS locale, see `_resolve_lang`).
The download dock (`#download-dock`, bottom of every page) polls `/api/status/{job_id}`
for job ids kept in `localStorage`, so progress survives navigation.

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
| `/sw.js` | — | Serves the PWA service worker from `static/` at the root scope | — |

## API — download flow

| Route | Method | Purpose |
|---|---|---|
| `/api/probe` | POST | Resolve a URL → `downloader.probe()`: title, uploader, duration, thumbnail, description, video formats (with size estimates), subtitles, transcript language, audio tracks; or a playlist listing |
| `/api/download` | POST | Start a job (`kind`: audio/video/transcript, `choice`, `subtitle_langs`, `audio_langs`); runs in a thread pool, returns `job_id` |
| `/api/status/{job_id}` | GET | Job state, percent, speed, ETA, queue position, error |
| `/api/cancel/{job_id}` | POST | Cancel a running job and clean partial files |
| `/api/file/{job_id}` | GET | Reveal the finished file in the OS file explorer |

## API — history

| Route | Method | Purpose |
|---|---|---|
| `/api/history` | GET | List downloaded files (`HISTORY_EXTS`) with metadata, newest first |
| `/api/history/file/{filename:path}` | GET | Reveal a history file in the explorer |
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
| `/api/ytdlp-version` | GET | Installed vs latest yt-dlp |
| `/api/ytdlp-update` | POST | `pip install -U yt-dlp`, then restart |
| `/api/ffmpeg-version` | GET | ffmpeg/ffprobe versions + install commands |
| `/api/dependencies` | GET | venv packages vs PyPI |
| `/api/dependencies-update` | POST | Update all, then restart |
