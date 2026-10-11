"""Entry point for running MediaGrab from source: `python run.py`.
Equivalent to `uvicorn mediagrab.app:app --port 8420`, but also opens the
browser automatically and handles the port-already-in-use case gracefully."""
import http.client
import os
import socket
import subprocess
import sys
import threading
import time
import traceback
import webbrowser

import uvicorn

from mediagrab.app import app, lan_ip as _app_lan_ip
from mediagrab.paths import app_dir, is_docker, use_bundled_ffmpeg
from mediagrab.store import get_settings, remote_access_active

# NOTE: HOST is what THIS process uses to reach the server itself (probing
# whether it's already running, opening the browser) - always loopback,
# regardless of what uvicorn is told to listen on. A browser can't usefully
# be pointed at 0.0.0.0 anyway; 127.0.0.1 reaches a server bound there too.
HOST = "127.0.0.1"
# NOTE: deliberately not 8000/3000/5000/8080 - common ports that other local
# projects often default to. This is just the FIRST port tried, though - see
# _find_free_port() below for what happens if even this one is taken.
PORT = 8420


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) == 0


def _is_mediagrab_running(port: int) -> bool:
    # NOTE: a port being taken doesn't necessarily mean MediaGrab is already
    # running there - it could be a completely unrelated app (this is
    # exactly what happened with another local project also defaulting to
    # the same port). Probe a MediaGrab-specific endpoint to tell the two
    # cases apart instead of just assuming.
    try:
        conn = http.client.HTTPConnection(HOST, port, timeout=1.5)
        conn.request("GET", "/api/locale")
        resp = conn.getresponse()
        data = resp.read()
        conn.close()
        return resp.status == 200 and b'"lang"' in data
    except Exception:
        return False


def _find_free_port() -> int:
    # NOTE: binding to port 0 asks the OS to hand back any currently-free
    # port - guaranteed not to collide with whatever else is running.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


def _open_browser(port: int) -> None:
    time.sleep(1.5)
    webbrowser.open(f"http://{HOST}:{port}")


LOG_NAME = "mediagrab.log"
# NOTE: past this size the old log is kept once as .old and a new one starts -
# enough history for a bug report without growing forever.
LOG_MAX_BYTES = 2 * 1024 * 1024


def _ensure_output_streams(folder: str) -> "str | None":
    """Give stdout/stderr somewhere to go when there's no console.

    The Windows installer starts MediaGrab with pythonw.exe (no console
    window), where sys.stdout and sys.stderr are None. uvicorn's log setup
    calls sys.stdout.isatty() and crashed on that before the server ever
    started - silently, since there was no window to show it (found trying
    the first installer build). Returns the log file's path, or None when
    real streams exist and nothing was changed.
    """
    if sys.stdout is not None and sys.stderr is not None:
        return None
    path = os.path.join(folder, LOG_NAME)
    try:
        if os.path.getsize(path) > LOG_MAX_BYTES:
            os.replace(path, path + ".old")
    except OSError:
        pass
    stream = open(path, "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or stream
    sys.stderr = sys.stderr or stream
    return path


def _hide_child_console_windows() -> None:
    """Stop every console program MediaGrab starts from popping a window.

    Without a console of its own (pythonw), each console child - ffprobe for
    a cover or a duration, ffmpeg merging, Deno, the version checks - got a
    brand-new console window that flashed open and shut, several per
    download; on a non-technical user's screen that looks like malware (found
    trying the first installer build). Patched once at subprocess.Popen,
    which every call goes through - yt-dlp's own Popen subclass included -
    instead of at each call site. GUI programs (explorer) ignore the flag.
    """
    if os.name != "nt":
        return
    original_init = subprocess.Popen.__init__

    def init(self, *args, **kwargs):
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | subprocess.CREATE_NO_WINDOW
        original_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = init


def _report_fatal(log_path: "str | None") -> None:
    traceback.print_exc()
    if sys.stdin is not None and sys.stdin.isatty():
        # NOTE: a console window closes the instant the process exits, so a
        # crash would flash red text and vanish - wait for a keypress.
        input("\nBir hata oluştu / An error occurred. Kapatmak için Enter'a basın / Press Enter to close...")
        return
    # NOTE: no console (pythonw): input() itself raises "lost sys.stdin" and
    # buried the real error. Windows' own message box is the only thing the
    # user can see; the details are in the log.
    if os.name == "nt":
        import ctypes

        where = f"\n\n{log_path}" if log_path else ""
        ctypes.windll.user32.MessageBoxW(
            None,
            f"MediaGrab başlatılamadı.\nMediaGrab could not start.{where}",
            "MediaGrab",
            0x10,  # MB_ICONERROR
        )


def main() -> None:
    log_path = _ensure_output_streams(app_dir())
    if log_path:
        # NOTE: no console of our own (pythonw) - see the function.
        _hide_child_console_windows()
    use_bundled_ffmpeg()
    port = PORT
    if _port_in_use(port):
        if _is_mediagrab_running(port):
            # NOTE: most likely the user launched MediaGrab twice (e.g.
            # double-clicked the exe again) - just open the existing
            # instance instead of crashing with a bind error.
            print("MediaGrab zaten çalışıyor gibi görünüyor / MediaGrab already seems to be running.")
            print(f"Tarayıcıda açılıyor / Opening in browser: http://{HOST}:{port}")
            webbrowser.open(f"http://{HOST}:{port}")
            time.sleep(2)
            return
        # NOTE: some other, unrelated app is using this port - fall back to
        # a free one from the OS instead of failing or fighting over it.
        fallback = _find_free_port()
        print(f"Port {port} başka bir uygulama tarafından kullanılıyor / Port {port} is in use by another app.")
        print(f"Bunun yerine boş bir port kullanılıyor / Using a free port instead: {fallback}")
        port = fallback

    in_docker = is_docker()
    # NOTE: no desktop/browser exists inside a container - opening one there
    # would just be a silent no-op at best.
    if not in_docker:
        threading.Thread(target=_open_browser, args=(port,), daemon=True).start()

    # NOTE: only listen beyond localhost when Settings -> Remote Access is
    # both turned on AND a password is set (remote_access_active checks
    # both - see its docstring in store.py) - the exact same condition the
    # app's own login gate uses, so "requires a login" and "reachable from
    # the network at all" can never drift apart.
    #
    # A container is the one exception - it ALWAYS binds to 0.0.0.0
    # regardless of that setting. A fresh container has no password yet, so
    # requiring remote_access_active() first would make Settings itself
    # unreachable (you'd need to already be in to turn on the thing that
    # lets you in). app.py's lifespan (_ensure_docker_has_a_password)
    # refuses to start at all unless a password already exists or
    # MEDIAGRAB_INITIAL_PASSWORD provides one, so this is never "wide open
    # with no login" in practice.
    bind_host = "0.0.0.0" if (in_docker or remote_access_active(get_settings())) else HOST
    if bind_host != HOST:
        # NOTE: _app_lan_ip is the exact same function Settings -> Remote
        # Access shows an address from - this print can never disagree with it.
        print(f"Uzaktan erisim acik / Remote access is on - LAN: http://{_app_lan_ip() or '?'}:{port}")

    # NOTE: the actual port (after the free-port fallback above) is only ever
    # decided here - app.py's lifespan() reads this to register the correct
    # port for mDNS, since it has no other way to know it (uvicorn doesn't
    # pass it through to the ASGI app). A direct `uvicorn mediagrab.app:app`
    # launch (bypassing run.py) never sets this, so mDNS falls back to 8420
    # in that case - an accepted limitation for a non-default launch method.
    os.environ["MEDIAGRAB_PORT"] = str(port)

    try:
        uvicorn.run(app, host=bind_host, port=port)
    except Exception:
        _report_fatal(log_path)
        sys.exit(1)


if __name__ == "__main__":
    main()
