"""Entry point for the packaged .exe. Not used when running via
`uvicorn mediagrab.app:app` from source - that stays the documented dev flow."""
import socket
import sys
import threading
import time
import traceback
import webbrowser

import uvicorn

from mediagrab.app import app

HOST = "127.0.0.1"
PORT = 8000


def _port_in_use() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, PORT)) == 0


def _open_browser() -> None:
    time.sleep(1.5)
    webbrowser.open(f"http://{HOST}:{PORT}")


def main() -> None:
    # NOTE: if the port is already taken, MediaGrab is most likely already
    # running (e.g. the user double-clicked the exe twice) - just open the
    # existing instance instead of crashing with a bind error.
    if _port_in_use():
        print(f"MediaGrab zaten çalışıyor gibi görünüyor / MediaGrab already seems to be running.")
        print(f"Tarayıcıda açılıyor / Opening in browser: http://{HOST}:{PORT}")
        webbrowser.open(f"http://{HOST}:{PORT}")
        time.sleep(2)
        return

    threading.Thread(target=_open_browser, daemon=True).start()
    try:
        uvicorn.run(app, host=HOST, port=PORT)
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
