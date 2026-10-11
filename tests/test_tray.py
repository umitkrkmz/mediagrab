"""The Windows tray icon (mediagrab/tray.py) on the real Win32 API.

NOTE: Windows only. Each test really adds an icon to the notification area
for a moment and removes it again; messages are posted to its hidden window
the way the installer and the tray menu would.
"""

import ctypes
import os
import threading
import time
from pathlib import Path

import pytest
from conftest import start_tray_icon

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows tray icon")

ICON = str(Path(__file__).parent.parent / "packaging" / "mediagrab.ico")


@pytest.fixture(autouse=True)
def _not_with_a_real_mediagrab_running():
    # NOTE: these look the window up by class name - with the developer's
    # own MediaGrab running they would find (and message!) that one.
    from mediagrab import tray as tray_module

    if tray_module.other_process_window():
        pytest.skip("a real MediaGrab is running on this machine - quit it to run these")


def _wait(condition, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.02)
    return False


@pytest.fixture
def tray():
    from mediagrab import tray as tray_module

    calls = {"open": 0, "quit": 0}

    def on_open():
        calls["open"] += 1

    def on_quit():
        calls["quit"] += 1

    icon = tray_module.TrayIcon("MediaGrab - test", "Open", "Quit", on_open, on_quit, ICON)
    start_tray_icon(icon)
    icon.calls = calls
    yield icon
    icon.stop()


def _post(icon, msg, wparam=0, lparam=0):
    ctypes.windll.user32.PostMessageW(ctypes.c_void_p(icon.hwnd), msg, wparam, lparam)


def test_the_installer_can_find_the_window_by_its_class(tray):
    from mediagrab import tray as tray_module

    find = ctypes.windll.user32.FindWindowW
    find.restype = ctypes.c_void_p
    assert find(tray_module.TRAY_WINDOW_CLASS, None) == tray.hwnd


def test_wm_close_asks_to_quit_once(tray):
    # NOTE: what the installer/uninstaller sends - and may send twice.
    from mediagrab import tray as tray_module

    _post(tray, tray_module.WM_CLOSE)
    _post(tray, tray_module.WM_CLOSE)
    assert _wait(lambda: tray.calls["quit"] >= 1)
    time.sleep(0.2)
    assert tray.calls["quit"] == 1
    assert tray.added, "the icon stays until run.py has stopped the server"


def test_left_click_and_the_menu_open_mediagrab(tray):
    from mediagrab import tray as tray_module

    _post(tray, tray_module.WM_TRAY_CALLBACK, 0, tray_module.WM_LBUTTONUP)
    _post(tray, tray_module.WM_COMMAND, tray_module.ID_OPEN)
    assert _wait(lambda: tray.calls["open"] == 2)


def test_the_menus_quit(tray):
    from mediagrab import tray as tray_module

    _post(tray, tray_module.WM_COMMAND, tray_module.ID_QUIT)
    assert _wait(lambda: tray.calls["quit"] == 1)


def test_stop_removes_the_icon_and_the_window(tray):
    from mediagrab import tray as tray_module

    tray.stop()
    assert not tray.added
    find = ctypes.windll.user32.FindWindowW
    find.restype = ctypes.c_void_p
    assert not find(tray_module.TRAY_WINDOW_CLASS, None)
    assert not tray._thread.is_alive()


def test_a_missing_icon_file_still_shows_an_icon():
    from mediagrab import tray as tray_module

    icon = tray_module.TrayIcon("t", "o", "q", lambda: None, lambda: None, "C:/nope/missing.ico")
    try:
        start_tray_icon(icon)
    finally:
        icon.stop()


def test_two_icons_one_after_another_each_get_their_own_messages():
    # NOTE: the window class is registered once per process.
    from mediagrab import tray as tray_module

    for _ in range(2):
        hits = []
        icon = tray_module.TrayIcon("t", "o", "q", lambda: hits.append(1), lambda: None, ICON)
        start_tray_icon(icon)
        _post(icon, tray_module.WM_COMMAND, tray_module.ID_OPEN)
        assert _wait(lambda: hits == [1])
        icon.stop()


def test_installer_and_app_agree_on_the_window_class():
    from mediagrab import tray as tray_module

    packaging = Path(__file__).parent.parent / "packaging"
    assert f"'{tray_module.TRAY_WINDOW_CLASS}'" in (packaging / "close_mediagrab.iss").read_text(encoding="utf-8")
    assert '#include "close_mediagrab.iss"' in (packaging / "mediagrab.iss").read_text(encoding="utf-8-sig")
