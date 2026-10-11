import os
import sys


def app_dir() -> str:
    """Directory for user-facing, writable locations (e.g. indirilenler/).

    When frozen into a PyInstaller onefile exe, this is the folder the .exe
    itself lives in - NOT sys._MEIPASS, which is a temp extraction dir wiped
    after each run. When running from source, it's the project root.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_dir(*parts: str) -> str:
    """Directory for bundled read-only resources (static/, templates/).

    PyInstaller extracts --add-data files into sys._MEIPASS at startup; when
    running from source there's no _MEIPASS, so this falls back to the
    package directory.
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def is_docker() -> bool:
    """True when running inside a Docker container.

    `/.dockerenv` is created by the container runtime itself (Docker, and
    most compatible runtimes) - no environment variable or build-time flag
    needed, so this works even for an image someone else built. Used to
    change two things: run.py's bind-host decision (a fresh container has no
    password yet, so it must not silently bind to loopback-only - see
    app.py's lifespan) and which self-update buttons stay usable (only
    yt-dlp's, via a PYTHONUSERBASE override - see downloader.update_ytdlp)
    since a container's own filesystem changes don't survive being
    recreated from a fresh image.
    """
    return os.path.exists("/.dockerenv")


def windows_install_dir() -> "str | None":
    """The install folder when this is the v2.4.0 Windows installer's layout.

    That layout is <install>\\app (this code) next to <install>\\python (the
    embedded interpreter) - see packaging/build_windows.py. Both are
    required: a source checkout that merely lives in some folder called
    "app" must not be mistaken for it. None for source, Docker and the old
    git-based installer.
    """
    base = app_dir()
    install = os.path.dirname(base)
    if os.path.basename(base) == "app" and os.path.isdir(os.path.join(install, "python")):
        return install
    return None


def data_dir() -> str:
    """Where settings, followed channels, cookies and statistics live.

    The Windows installer keeps them in %LOCALAPPDATA%\\MediaGrab, apart from
    the program files, so an update or an uninstall never touches them.
    Everywhere else (source, Docker, the old git-based installer) it is
    app_dir(), exactly as before. MEDIAGRAB_DATA_DIR overrides both.
    """
    override = os.environ.get("MEDIAGRAB_DATA_DIR")
    if override:
        return os.path.abspath(override)
    if windows_install_dir():
        local = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
        return os.path.join(local, "MediaGrab")
    return app_dir()


def _windows_downloads_folder() -> "str | None":
    # NOTE: asked from Windows itself (Known Folder "Downloads") rather than
    # assumed to be ~\Downloads - people move it to another drive.
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", ctypes.c_ubyte * 8),
            ]

        # FOLDERID_Downloads {374DE290-123F-4565-9164-39C4925E467B}
        folder_id = GUID(
            0x374DE290, 0x123F, 0x4565, (ctypes.c_ubyte * 8)(0x91, 0x64, 0x39, 0xC4, 0x92, 0x5E, 0x46, 0x7B)
        )
        path_ptr = ctypes.c_wchar_p()
        if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(folder_id), 0, None, ctypes.byref(path_ptr)) != 0:
            return None
        try:
            return path_ptr.value
        finally:
            ctypes.windll.ole32.CoTaskMemFree(path_ptr)
    except Exception:
        return None


def default_download_dir() -> str:
    """Where downloads go unless Settings says otherwise.

    The Windows installer: <Downloads>\\MediaGrab - where people look for
    downloaded things, and (unlike Documents/Desktop) not swept into
    OneDrive by its folder backup. Everywhere else: app_dir()\\indirilenler,
    as it always was.
    """
    if windows_install_dir():
        downloads = _windows_downloads_folder() or os.path.join(os.path.expanduser("~"), "Downloads")
        return os.path.join(downloads, "MediaGrab")
    return os.path.join(app_dir(), "indirilenler")


# NOTE: the same list setup_mediagrab.py warns about (a deliberate small
# duplicate - the installer can't import this package, see AGENTS.md;
# tests/test_version.py checks they still match). A synced folder would
# upload every downloaded video.
CLOUD_MARKERS = ("onedrive", "dropbox", "google drive", "googledrive", "icloud", "yandex.disk")


def cloud_service_in_path(folder: str) -> "str | None":
    lowered = folder.replace("\\", "/").lower()
    for marker in CLOUD_MARKERS:
        if marker in lowered:
            return marker
    return None


def bundled_ffmpeg_dir() -> "str | None":
    """The ffmpeg folder shipped by the Windows installer, if this is one.

    <install>\\ffmpeg next to the app and the embedded Python (see
    windows_install_dir) - a source checkout that merely happens to sit next
    to some "ffmpeg" folder must not pick up whatever binaries are in it.
    """
    install = windows_install_dir()
    if install and os.path.isfile(os.path.join(install, "ffmpeg", "ffmpeg.exe")):
        return os.path.join(install, "ffmpeg")
    return None


def use_bundled_ffmpeg() -> None:
    # NOTE: put first on PATH rather than passed around - yt-dlp, the
    # Settings version check (deps._tool_version) and every ffprobe call
    # all find ffmpeg through PATH already, so this one line covers them.
    folder = bundled_ffmpeg_dir()
    if folder:
        os.environ["PATH"] = folder + os.pathsep + os.environ.get("PATH", "")


# NOTE: the launcher setup_mediagrab.py writes into every folder it installs
# to (see its _launcher_name) - a deliberate small duplicate, since the
# installer runs before this package exists and can't share code with it
# (AGENTS.md). tests/test_version.py checks the two lists still match.
INSTALLER_LAUNCHERS = ("MediaGrab Baslat.bat", "mediagrab-baslat.sh")


def install_type() -> str:
    """How this copy was installed: "docker", "installer" or "source".

    Decides which update instructions Settings -> Version Checks shows - each
    of the three updates differently (pull a new image / run the installer's
    Repair-Update / git pull + pip install).
    """
    if is_docker():
        return "docker"
    base = app_dir()
    if any(os.path.isfile(os.path.join(base, name)) for name in INSTALLER_LAUNCHERS):
        return "installer"
    return "source"
