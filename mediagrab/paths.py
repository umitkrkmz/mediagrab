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
