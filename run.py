"""Entry point for running MediaGrab from source: `python run.py`.
Equivalent to `uvicorn mediagrab.app:app --port 8420`, but also opens the
browser automatically and handles the port-already-in-use case gracefully."""
import http.client
import socket
import sys
import threading
import time
import traceback
import webbrowser

import uvicorn

from mediagrab.app import app

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


def main() -> None:
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

    threading.Thread(target=_open_browser, args=(port,), daemon=True).start()
    try:
        uvicorn.run(app, host=HOST, port=port)
    except Exception:
        # NOTE: a console-mode PyInstaller exe closes its window the instant
        # the process exits, so an unhandled exception would flash red text
        # and vanish before anyone could read it. Print the traceback and
        # wait for a keypress instead.
        traceback.print_exc()
        input("\nBir hata oluştu / An error occurred. Kapatmak için Enter'a basın / Press Enter to close...")
        sys.exit(1)


if __name__ == "__main__":
    main()
