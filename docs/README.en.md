# MediaGrab — User Guide

**[🇹🇷 Türkçe sürüm](README.tr.md)** · **[← Back to main README](../README.md)**

---

**Contents**

- [What it does](#what-it-does)
- [Features](#features)
- [Installation](#installation)
  - [Method A: Easy install (Windows)](#method-a-easy-install-windows-mediagrabsetupexe)
  - [Method B: Manual install (any platform)](#method-b-manual-install-from-source-any-platform)
  - [Method C: Docker (any platform)](#method-c-docker-any-platform)
- [Running](#running)
- [How Channel Following Works](#how-channel-following-works)
- [Remote Access (From Your Local Network)](#remote-access-from-your-local-network)
- [Home Server Mode](#home-server-mode)
- [Tests](#tests)
- [Troubleshooting](#troubleshooting)
- [Project structure](#project-structure)
- [License & Third-Party Notices](#license--third-party-notices)
- [Legal Notice](#legal-notice)
- [Keep yt-dlp updated](#keep-yt-dlp-updated)

---

Paste a link, download it. A local, personal-use video/audio downloader.

## What it does

Paste a YouTube or YouTube Music link (a single video, a playlist, or an album). MediaGrab resolves it, lists the available audio/video qualities and any subtitle languages, and downloads whichever option you pick straight to your disk. Beyond YouTube, many other sites supported by yt-dlp (Vimeo, SoundCloud, X/Twitter, Twitch, archive.org, and more — [full list](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)) work through the same flow; channel following, however, currently supports YouTube channels only.

## Features

- **Audio** — Opus / M4A (remuxed, no re-encoding, no quality loss) or MP3 (re-encoded for universal compatibility)
- **Video** — every available resolution, auto-merged with audio into an mp4; when YouTube reports no real filesize, an estimate (`~1.2 GB`) is computed from the average bitrate
- **Audio track (dub) selection, more than one at once** — pick the language you want when a video has more than one dub, or pick several at once (e.g. original + Turkish) to get them embedded as separate tracks in a `.mkv`. Only shows up when the video actually has a dub, and picking nothing gets you the original. Multi-select only applies to video downloads; a single pick works for audio too. Save a default language in `/settings` so you don't have to click a chip every time — channel auto-download uses it too (single language). Not sure of a code? Check the [language code reference](language-codes.en.md)
- **Subtitles** — check off manually-provided subtitle languages and they download together with whichever video you pick, sharing the same filename (`video.mp4` + `video.en.srt`) so media players auto-match them
- **Transcript download** — for videos with subtitles (manual or auto-generated), you can separately download a plain-text transcript (`.txt`)
- **Paste-to-resolve & quick options** — a paste button that auto-detects the clipboard link; one-click buttons for best audio/best video, with every other quality/format tucked under "advanced options"
- **Persistent download panel** — track multiple downloads at once, with an estimated time remaining alongside the speed; progress survives page navigation and even closing and reopening the app
- **In-place preview** — play audio/video files straight from the item detail page without opening a file explorer
- **Installable app (PWA)** — use your browser's "Add to Home Screen" to run MediaGrab like a standalone app
- **Playlists & YouTube Music** — paste a playlist link and get a list of videos with covers/titles/durations; click one to download it individually, or pick a range (e.g. 1–19) and **queue them all with one click**
- **Multi-platform** — not YouTube-only; works through the same UI with any of the 1700+ sites yt-dlp supports (Vimeo, SoundCloud, X/Twitter, Twitch, archive.org, and more)
- **Metadata (JSON) export** — every download also saves a JSON file with the same base name (`video.mp4` + `video.json`) containing title, uploader, upload date, description, tags, and the source URL; also downloadable from the item detail page
- **Automatic folder organization** — every download is saved into its own subfolder by channel/uploader (`indirilenler/Channel Name/`), so files stay organized in your file explorer or media library apps
- **Supported Sites page** (`/supported-sites`) — a short, categorized list of popular sites yt-dlp supports, with a link to the full list (1700+ sites); each one carries its site's brand color/logo and links to that site's homepage
- **About page** (`/about`) — what the project is, its GPL-3.0 license, and links to the source code and feedback
- **yt-dlp version check with one-click update** (`/settings`) — compares your installed yt-dlp version against the latest on PyPI; if an update is available, installs it with one click and restarts the app automatically
- **Channel following** (`/channels`) — follow a channel; every time you open the app, it's checked for new videos. Two modes: **Notify** (a banner on the home page tells you, you pick what to download) or **Auto-download** (downloads new uploads automatically in your chosen format). Not a persistent background service - see the note below.
- **Remote access** (`/settings`) — set a password and turn it on, and your phone or another computer on the same Wi-Fi/network can connect to MediaGrab from its own browser and download on its own; see the dedicated section below for details.
- **Home Server Mode** (`/settings`) — for anyone running MediaGrab on a machine that's on 24/7, like a Raspberry Pi: periodic (every 3 hours) automatic channel checking, and an easy-to-remember `mediagrab.local` address; see the dedicated section below for details.
- **Docker support** — run it in a container without installing Python or Git; one click from the Windows installer, or `docker compose up -d` by hand — see below for details.
- **Download speed limiting** and a **disk-space shield** (`/settings`) — set an optional overall speed cap, and a download is refused up front when there isn't enough free disk space left to finish it
- **Backup / restore settings** (`/settings`) — export all your settings and followed channels (minus your password) into one file and import them into another install
- **Download history** — its own page (`/history`), switchable between cover-art cards and a compact list view; search by title, filter by channel and by file type (built dynamically from what's actually on disk), re-download, delete, or clear all
- **Light / dark theme** — follows your system setting, or pick it by hand from `/settings` or the header toggle
- **Cancel a download** — stop a running download from the panel; partial files are cleaned up automatically
- **Existing files are protected** — if a re-download is cancelled, fails, or the app crashes, your previous file comes back untouched
- **Cookie support** (`/settings`) — use your browser session's cookies for age-restricted, members-only or sign-in-required content: either a `cookies.txt` file (works everywhere) or straight from the browser. Your cookies are never copied; only the source name is stored
- **Environment checks** (`/settings`) — ffmpeg/ffprobe version plus a Python dependency check, with one-click package updates
- **Feedback** (`/settings`) — one click to GitHub's ready-made templates for reporting a bug or suggesting a feature
- **Friendly error messages** — common cases (age restriction, bot check, geo-restriction, removed videos, and more) show an explanatory message in your language instead of yt-dlp's raw output
- **Auto reveal in file explorer** — clicking "Download file" opens your OS file explorer with the file selected
- **Turkish / English UI** — follows your system locale by default, switchable by hand
- **No** database, account system, or cloud connection — runs only on this machine

## Installation

There are three paths: **easy install** (Windows-only, a ready-made `.exe`, no typing commands), **manual install** (git clone + pip, works on every platform), or **Docker** (in a container, no Python/Git needed — works on every platform).

### Method A: Easy install (Windows, `MediaGrabSetup.exe`)

**1. Install Git and Python first**

- Git: [git-scm.com/downloads](https://git-scm.com/downloads)
- Python 3.9+: [python.org/downloads](https://www.python.org/downloads/) — check **"Add python.exe to PATH"** during setup.

**2. Download the installer**

Grab `MediaGrabSetup.exe` from the [GitHub Releases page](https://github.com/umitkrkmz/mediagrab/releases/latest).

Optionally verify it's intact — **that release's SHA256 is printed in its release notes** (it differs per release, since the exe is rebuilt each time). In PowerShell:

```powershell
certutil -hashfile MediaGrabSetup.exe SHA256
```

Compare the output against the value on the release page.

**3. Choose the install folder**

By default MediaGrab installs into whichever folder `MediaGrabSetup.exe` sits in — but you can pick a different one with **"Browse…"** in the setup window. Use an **empty folder dedicated to MediaGrab** (e.g. `C:\MediaGrab\`).

> **Important:** don't use a folder that's **watched by a cloud sync service** like OneDrive, Dropbox, or Google Drive (note: on Windows, "Desktop" and "Documents" are often OneDrive-synced by default). Downloads write and delete a lot of small temp files in quick succession; if the sync client locks one of them at just the wrong moment, the download can fail mid-way with a "No such file or directory" error. A plain, non-synced folder like `C:\MediaGrab\` avoids this entirely.
>
> The installer checks this for you too: it warns if you pick a cloud-synced folder, and refuses drive roots and your personal folders (Desktop, Documents, your user folder) outright — because **Remove** deletes the install folder's contents.

**4. Run it**

Double-click `MediaGrabSetup.exe`. The welcome page opens in Turkish or English depending on your system language (switch with **TR / EN** in the top-right corner) and offers three choices: **Install**, **Repair / Update**, **Remove**. Pick **Install** and the wizard walks you through:

- **Requirements** — Git, Python (including its version) and ffmpeg are checked; anything missing gets a download button and a copyable command, and **Refresh** re-checks once you've installed it.
- **Install folder** — pick the folder from step 3; the Desktop / Start Menu shortcut boxes live here too.
- **Summary** — what's about to happen (folder, tools found, shortcuts, any existing files that will be overwritten) on one page; **Install** starts it.
- **Progress** — a live log; when it's done, **"Start MediaGrab"** launches the app directly.

The installer remembers the last install folder: choosing **Repair / Update** or **Remove** later pre-fills it (you can still change it).

> Since it's an unsigned `.exe`, Windows may show a "Windows protected your PC" warning the first time — click **More info → Run anyway** to continue. The source is `setup_mediagrab.py` in this repo if you'd like to inspect it first.

**5. Install ffmpeg (required — the installer does not do this)**

MediaGrab needs `ffmpeg` and `ffprobe` to merge audio/video, convert formats, and read duration/cover art. They are not bundled with MediaGrab and `pip` does not install them; **you install them on your system separately.** Without them the app still starts, but downloads fail at the merge step.

Run the command for your OS in a terminal:

```powershell
winget install --id Gyan.FFmpeg -e
```

```bash
brew install ffmpeg
```

```bash
sudo apt install ffmpeg
```

In order: Windows (PowerShell) · macOS (Homebrew) · Linux (Debian/Ubuntu).

Afterwards **open a new terminal** (a PATH update doesn't reach an already-open one) and verify with `ffmpeg -version`.

> You can also find these inside the app: **Settings → ffmpeg / ffprobe** shows the installed version and lists every platform's command with a copy button.

**6. Launch it**

Once install finishes, just double-click the **`MediaGrab Baslat.bat`** file it created — no terminal needed (or use the Desktop/Start Menu shortcut if you added one in step 3).

To update or remove later: run `MediaGrabSetup.exe` again and click **Repair / Update** or **Remove** — your downloads and followed-channel list are preserved either way.

### Method B: Manual install (from source, any platform)

**1. Get the project files**

```bash
git clone https://github.com/umitkrkmz/mediagrab.git
cd mediagrab
```

**2. Create and activate a virtual environment**

Keeps dependencies scoped to the project instead of your whole system:

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You'll see `(.venv)` at the start of your prompt once it's active. Run every command below in that same terminal, with the environment active.

**3. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**4. ffmpeg (system dependency — required)**

yt-dlp uses it for remux/merge/encode steps; MediaGrab itself calls `ffprobe` from PATH to read accurate media duration.

Windows:

```bash
winget install --id Gyan.FFmpeg -e
```

Open a **new terminal** afterwards — the PATH update may not show up in a terminal that was already open.

macOS:

```bash
brew install ffmpeg
```

Linux (Debian/Ubuntu):

```bash
sudo apt install ffmpeg
```

Verify with: `ffmpeg -version`

### Method C: Docker (any platform)

Run it in a container without installing Python or Git. First [install Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + the Compose plugin on Linux).

**Easy way on Windows:** run `MediaGrabSetup.exe` and click **"Install with Docker"** on the welcome page. The wizard checks that Docker is installed and running, asks for a folder and an initial admin password, writes the `docker-compose.yml` for you, and starts it with `docker compose up -d` — no terminal commands needed.

**By hand (any platform):**

```bash
git clone https://github.com/umitkrkmz/mediagrab.git
cd mediagrab
```

Open the repo's `docker-compose.yml` and replace `MEDIAGRAB_INITIAL_PASSWORD` with a real password — it's only ever read the very first time the container starts with no password already set; after that it can safely stay in the file, it's simply never read again. On Linux, `network_mode: host` is on by default (needed so the app sees your real LAN IP and so `mediagrab.local` works); on Windows/Mac, Docker Desktop doesn't support that, so comment that line out and uncomment the `ports: ["8420:8420"]` lines below it instead.

```bash
docker compose up -d
```

The repo's compose file currently uses `build: .`, so this command builds the image locally from the `Dockerfile` the first time (can take a few minutes); later runs reuse the built image. From another device, go to `http://<this-computer's-LAN-IP>:8420`. Your downloads, settings, and followed channels are kept in `./data/`, outside the container - they survive a rebuild or the container being recreated.

**Updating:** update yt-dlp from the Settings page with one click, same as always (it installs into a folder that persists even across a rebuild). Every other dependency (FastAPI, ffmpeg, etc.) is baked into the image; updating those means pulling the latest source and rebuilding:

```bash
git pull && docker compose up -d --build
```

> Once an official image is published under a version tag (`v2.0.0`, say) at `ghcr.io/umitkrkmz/mediagrab`, you can replace `docker-compose.yml`'s `build: .` line with `image: ghcr.io/umitkrkmz/mediagrab:latest` (as its own comment shows) and use `docker compose pull && docker compose up -d` from then on — the Windows installer's "Install with Docker" option already targets that published image.

The "update dependencies" button in Settings is disabled in Docker and reminds you of this — it can't update or rebuild the image itself.

## Running

With the virtual environment active, from the project root:

```bash
python run.py
```

This starts the server and opens your browser automatically (default port 8420). Stop it with `Ctrl+C` in the terminal.

Alternatively, you can run `uvicorn` directly:

```bash
uvicorn mediagrab.app:app --port 8420
```

In that case you'll need to open `http://127.0.0.1:8420` in your browser yourself.

> **Port conflicts:** 8420 was chosen as the default because "standard" ports like 8000/3000/5000/8080 tend to collide with other local projects. But `python run.py` isn't limited to that either: if 8420 is taken, it first checks whether it's actually another MediaGrab instance already running there — if so, it opens that same tab; if not (some other project is holding the port), it automatically asks the OS for a free port and uses that instead. Running `uvicorn` directly skips this automatic behavior, so you'd need to pick a different port yourself with `--port` if there's a conflict.

## How Channel Following Works

MediaGrab is **not** a persistent background service - it only runs while you have it open. So channel following works on a "check once per launch" basis: every time you start the app (running `python run.py` or the `uvicorn` command), every channel on your list is checked in the background. New uploads that happen while the app is closed aren't detected until you open it again - that's the expected behavior for a personal/local tool; we deliberately didn't turn this into a 24/7 Windows service.

The followed-channel list and each channel's "last seen video" state live in a `channels.json` file (not committed to git) instead of a database - same "real data lives on disk, no separate DB" philosophy as the rest of the project.

## Remote Access (From Your Local Network)

You can run MediaGrab on one computer and open it from your phone or another device on the same Wi-Fi/network, browser to browser - no need to install MediaGrab separately on every device.

**How to turn it on:** `/settings` → **Remote Access** tab → set a password first, then enable "Allow access from the local network". The server restarts itself once while the setting is applied; once it's back, the same panel shows the connection address (something like `http://192.168.x.x:8420`) - type that into the other device's browser. That device logs in with the password the first time it connects.

- **Connected devices** — the same panel shows every device currently logged in (browser + OS guess, e.g. "Chrome · Windows") and when it connected; you can sign any one of them out individually without affecting your own device.
- **Changing the password** — done with current password / new password / new password (again). If you forget it: on this computer, delete the `remote_access_password_salt` and `remote_access_password_hash` fields from `settings.json` and restart MediaGrab, then set a new password from Settings. Whenever the password changes (including through this recovery path), every logged-in device - including the one that changed it - is signed out and has to log back in with the new password.
- **Storage mode** — **Keep Here** (default): downloaded files stay permanently in this computer's `indirilenler/` folder, same as always; recommended for a personal computer. **Relay To Device**: if you're running this on a storage-constrained device (e.g. a Raspberry Pi), once a file has been fully sent to a device, this computer's copy is deleted right after. Downloads you make from this computer itself (the host's own browser) are never affected by this setting - it only applies to files sent to another device.

> **Security note:** this connection runs over plain HTTP, not HTTPS - only use it on a home/office network you trust, and never forward the port to expose it directly to the internet. Sessions are kept in memory only; whenever the server restarts (an update, the computer shutting down, etc.) everyone has to log back in with the password - a deliberate simplification, since a personal/local tool doesn't need sessions to survive on disk.

## Home Server Mode

Normally MediaGrab only runs while you have it open, and channel following only checks once per launch (see "How Channel Following Works" above). If you're running it on a machine that stays on 24/7, like a Raspberry Pi, you can change that from `/settings` → **Remote Access** tab → **Home Server Mode**:

- **Periodic channel checking** — your followed list is checked automatically every 3 hours, even if you never open the app; channels set to "Auto-download" start downloading a new upload as soon as the next check finds it.
- **The `mediagrab.local` address** — alongside your LAN IP (`http://192.168.x.x:8420`), other devices on the network can also reach you at the easy-to-remember `http://mediagrab.local:8420` (works on operating systems with mDNS/Bonjour support - Windows, macOS, most Linux distros; in Docker it only works on Linux with `network_mode: host`, not on Windows/Mac Docker Desktop). The Settings page shows two separate, clearly labeled QR codes - one for the IP, one for this address - so you can just scan and go from your phone.

Home Server Mode is independent of Remote Access: you can turn on either one alone, or both together.

## Tests

There's a small suite that needs no network access and finishes in a couple of seconds (path safety, VTT/transcript parsing, version comparison, backup-and-restore, translation integrity, front-end HTML escaping).

```bash
pip install -r requirements-dev.txt
pytest
```

The JavaScript tests need Node.js installed; they're skipped automatically if it isn't.

## Troubleshooting

**`ModuleNotFoundError` or "package not found" errors**
Make sure the virtual environment is active (you should see `(.venv)` in your prompt), then run `pip install -r requirements.txt` again.

**`ffmpeg`/`ffprobe` not found**
Make sure you opened a **new terminal** after installing ffmpeg — the PATH update doesn't show up in a terminal that was already open. Verify with `ffmpeg -version`.

**`[Errno 10048] ... address already in use` / port 8420 is busy**
If you're running with `python run.py`, this resolves itself automatically (see the port conflicts note above). If you're running `uvicorn` directly: a previous MediaGrab instance is probably still running in the background, or another project of yours is using the same port - pick a different one with `--port` in that case.

On Windows, find out which process holds the port and stop it with:

```powershell
Get-NetTCPConnection -LocalPort 8420 | Select-Object OwningProcess
Stop-Process -Id <PID from above> -Force
```

**`ImportError: attempted relative import with no known parent package`**
Don't run `mediagrab/app.py` directly with `python app.py`; always use `uvicorn mediagrab.app:app` from the project root — otherwise the package's internal relative imports break.

**yt-dlp fails to resolve a video / "Unable to extract" error**
Older yt-dlp versions break whenever YouTube changes its interface. Update it:

```bash
pip install -U yt-dlp
```

## Project structure

```
mediagrab/
    app.py          # FastAPI app, endpoints
    downloader.py   # yt-dlp wrapper — the ONLY file that imports yt_dlp
    models.py       # Pydantic models
    i18n.py         # server-rendered UI strings (TR/EN) - single source
    deps.py         # ffmpeg/ffprobe and Python package version checks
    store.py        # reads/writes channels.json / settings.json, not a DB
    paths.py         # resolves the right folders whether running from source or as the exe
    templates/      # Jinja2: base, index, history, item, channels, settings, supported_sites, about
    static/         # style.css, app.js
    static/icons/   # supported-site logos (from Simple Icons, kept locally)
indirilenler/       # downloaded files, auto-organized into per-channel subfolders (not in git)
    Channel Name/
        Video.mp4
        Video.json  # metadata sidecar
channels.json       # followed channels (not in git)
settings.json       # cookie source and default audio-language settings (not in git)
run.py              # entry point for `python run.py`
setup_mediagrab.py  # the installer tool (source of MediaGrabSetup.exe on Releases, with its Docker mode)
Dockerfile          # the Docker image (python:3.12-slim + ffmpeg)
docker-compose.yml  # example compose file (for a manual Docker install)
.dockerignore
tests/              # pytest suite (no network required)
docs/               # this file, its Turkish counterpart, and the language code reference (language-codes.*.md)
maps/               # detailed project map and route map (test-guarded, for AI tools and contributors)
requirements.txt
requirements-dev.txt  # development only (pytest) — the app never reads this
LICENSE             # v1.9.0+ (GPL-3.0-or-later)
LICENSE-MIT         # v1.0.0 – v1.8.0 (MIT)
README.md
```

## License & Third-Party Notices

**MediaGrab v1.0.0 – v1.8.0** was released under the **MIT** license (see [LICENSE-MIT](../LICENSE-MIT)), and that grant doesn't change retroactively — you can keep using or forking those releases under MIT terms.

**MediaGrab v1.9.0 and later is licensed under the GNU GPL-3.0 (or later)** (see [LICENSE](../LICENSE)). The reason for the switch is simple: staying MIT while depending on a GPL package like `mutagen` meant never importing it directly and relying entirely on yt-dlp running it as a separate process at arm's length (explained below). Moving to GPL-3.0 removes that constraint — if a future feature genuinely needs to import a GPL-licensed library directly, we can, without the workaround MIT required. GPL-3.0 was chosen over something more restrictive like AGPL because MediaGrab isn't offered as a network service, only a local tool.

**The application itself ships as source code.** You clone the repo, install dependencies into your own environment with `pip install -r requirements.txt`, and run it. None of the packages below are bundled with MediaGrab — `pip` fetches each one itself, which makes this "mere aggregation" as far as licensing goes.

**`MediaGrabSetup.exe` on the Releases page is not an exception:** it is only a small helper that *performs the install*, and it contains **no third-party packages at all** — just MediaGrab's own code, the Python standard library ([PSF license](https://docs.python.org/3/license.html)), and Tcl/Tk (BSD-style) for its window. yt-dlp, ffmpeg and the rest are **not** inside that exe; `pip` and your system package manager fetch them when you run it.

| Package | License | Note |
|---|---|---|
| [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) | [Unlicense](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE) (public domain) | download/resolve engine |
| [`fastapi`](https://github.com/fastapi/fastapi) | [MIT](https://github.com/fastapi/fastapi/blob/master/LICENSE) | web framework |
| [`starlette`](https://github.com/encode/starlette) | [BSD-3-Clause](https://github.com/encode/starlette/blob/master/LICENSE.md) | fastapi's ASGI layer |
| [`uvicorn`](https://github.com/encode/uvicorn) | [BSD-3-Clause](https://github.com/encode/uvicorn/blob/master/LICENSE.md) | ASGI server |
| [`pydantic`](https://github.com/pydantic/pydantic) | [MIT](https://github.com/pydantic/pydantic/blob/main/LICENSE) | data validation |
| [`jinja2`](https://github.com/pallets/jinja) | [BSD-3-Clause](https://github.com/pallets/jinja/blob/main/LICENSE.txt) | HTML templating |
| [`mutagen`](https://github.com/quodlibet/mutagen) | [GPL-2.0-or-later](https://github.com/quodlibet/mutagen/blob/master/COPYING) | **not imported by MediaGrab** — yt-dlp uses it to embed cover art into Opus files |
| [`zeroconf`](https://github.com/python-zeroconf/python-zeroconf) | [LGPL-2.1-or-later](https://github.com/python-zeroconf/python-zeroconf/blob/master/LICENSE) | publishes the `mediagrab.local` (mDNS) address used by Home Server Mode — unlike mutagen, **this one IS imported directly by MediaGrab's own code** (`_register_mdns`, on a background thread; fails silently and never affects the rest of the app). LGPL permits use by code under any license, GPL-3.0 included, so this isn't a conflict |
| [`ffmpeg`](https://github.com/FFmpeg/FFmpeg) / `ffprobe` | [LGPL-2.1+ or GPL-2+](https://www.ffmpeg.org/legal.html) (depends on the build) | NOT bundled — the user installs it separately on their own system; tag/cover-art reading and duration are also done through it via subprocess |

**About `mutagen`:** MediaGrab's source currently contains no `import mutagen` — yt-dlp uses it internally, and `pip` fetches it into your own environment; we neither bundle nor redistribute it. That's exactly why v1.8.0 and earlier could stay MIT: GPL's copyleft obligation only attaches once you combine and distribute GPL code, and we never did. From v1.9.0 on, that's no longer a requirement, just a fact — MediaGrab itself is GPL-3.0, so importing `mutagen` (GPL-2.0-or-later, compatible with GPL-3.0) directly in the future wouldn't be a problem either way. `ffmpeg` is unchanged: never redistributed, only invoked as a separate program via `subprocess`.

If you find MediaGrab useful, a ⭐ helps other people find it.

## Legal Notice

This tool is for **personal use only**. You are solely responsible for the copyright status of any content you download and for complying with the relevant platform's (including YouTube's) terms of service. MediaGrab is not a platform-circumvention or DRM-stripping tool — it only downloads publicly available, downloadable media via yt-dlp.

## Keep yt-dlp updated

YouTube changes its interface often; older yt-dlp versions eventually start failing to resolve or download. If you run into trouble, update first:

```bash
pip install -U yt-dlp
```
