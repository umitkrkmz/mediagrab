"""Settings -> Feedback -> "Copy diagnostic info".

NOTE: the text is meant to be pasted into a PUBLIC GitHub issue, so what it
must NOT contain is tested as carefully as what it does: no file paths (they
carry the user's name), no hostname, no IP, no cookie names/values.
"""

import platform

import pytest
from fastapi.testclient import TestClient

from mediagrab import __version__, downloader, store
from mediagrab import app as app_module
from mediagrab.paths import app_dir

FAKE_COOKIES = (
    "# Netscape HTTP Cookie File\n"
    ".youtube.com\tTRUE\t/\tTRUE\t2145916800\tSAPISID\tsecret-sapisid-value\n"
    ".youtube.com\tTRUE\t/\tTRUE\t2145916800\tLOGIN_INFO\tsecret-login-value\n"
)


def _assert_nothing_private(text: str, *extra: str) -> None:
    for private in (app_dir(), downloader.COOKIES_PATH, platform.node(), "secret-", "SAPISID", "LOGIN_INFO", *extra):
        assert private and private not in text, private


def test_lists_the_versions_and_states():
    text = app_module.diagnostics_text()
    assert f"MediaGrab: {__version__}" in text
    assert f"yt-dlp: {downloader.YT_DLP_VERSION}" in text
    for label in ("OS:", "Python:", "JS runtime:", "ffmpeg:", "Cookies: off", "Remote access: off"):
        assert label in text
    _assert_nothing_private(text)


def test_an_uploaded_cookie_file_shows_only_counts():
    downloader.save_uploaded_cookies(FAKE_COOKIES, ["youtube.com"])
    store.save_settings(cookie_mode="file", cookie_file=downloader.COOKIES_PATH)
    text = app_module.diagnostics_text()
    assert "Cookies: file (uploaded, 2 cookies, YouTube session: yes)" in text
    _assert_nothing_private(text)


def test_a_typed_in_cookie_path_never_appears(tmp_path):
    # NOTE: a path like this is exactly what would leak a real name.
    own = tmp_path / "Users" / "Jane Doe" / "cookies.txt"
    own.parent.mkdir(parents=True)
    own.write_text(FAKE_COOKIES, encoding="utf-8")
    store.save_settings(cookie_mode="file", cookie_file=str(own))
    text = app_module.diagnostics_text()
    assert "Cookies: file (path," in text
    _assert_nothing_private(text, str(own), "Jane Doe")


def test_an_unusable_saved_browser_is_flagged(monkeypatch):
    monkeypatch.setattr(downloader.sys, "platform", "win32")
    store.save_settings(cookie_mode="browser", cookie_browser="chrome")
    assert "Cookies: browser (chrome, not usable on this OS)" in app_module.diagnostics_text()


def test_the_lan_address_is_never_included(monkeypatch):
    monkeypatch.setattr(app_module, "lan_ip", lambda: "192.168.77.77")
    store.save_settings(remote_access_enabled=True, remote_access_password_salt="s", remote_access_password_hash="h")
    text = app_module.diagnostics_text()
    assert "Remote access: on" in text
    assert "192.168.77.77" not in text


def test_the_route_returns_the_text():
    with TestClient(app_module.app) as client:
        assert client.get("/api/diagnostics").json()["text"] == app_module.diagnostics_text()
