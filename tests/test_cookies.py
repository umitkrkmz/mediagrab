"""Tests for the cookie source setting.

NOTE: only the *source* is ever stored (a browser name or a path) - the cookies
themselves stay where they are and yt-dlp reads them directly. These tests
check the option yt-dlp receives, not any cookie content.
"""

import pytest

from mediagrab import downloader, store


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    """Point the settings store at a throwaway file."""
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    return tmp_path


@pytest.fixture
def cookies_txt(tmp_path):
    path = tmp_path / "cookies.txt"
    path.write_text(
        "# Netscape HTTP Cookie File\n"
        ".youtube.com\tTRUE\t/\tTRUE\t2145916800\tSESSION\tabc123\n",
        encoding="utf-8",
    )
    return path


# --- settings storage --------------------------------------------------------


def test_defaults_to_cookies_off(settings_file):
    assert store.get_settings()["cookie_mode"] == "off"


def test_settings_round_trip(settings_file, cookies_txt):
    store.save_settings(cookie_mode="file", cookie_file=str(cookies_txt))
    assert store.get_settings()["cookie_mode"] == "file"
    assert store.get_settings()["cookie_file"] == str(cookies_txt)


def test_unknown_keys_are_ignored(settings_file):
    # NOTE: a hand-edited settings.json must not be able to inject arbitrary
    # keys that later get splatted into yt-dlp's options.
    store.save_settings(cookie_mode="off", something_else="danger")
    assert "something_else" not in store.get_settings()


def test_corrupt_settings_file_falls_back_to_defaults(settings_file):
    (settings_file / "settings.json").write_text("{not json", encoding="utf-8")
    assert store.get_settings() == store.DEFAULT_SETTINGS


# --- the options handed to yt-dlp -------------------------------------------


def test_off_passes_nothing(settings_file):
    store.save_settings(cookie_mode="off")
    assert downloader.cookie_opts() == {}


def test_file_mode_passes_the_path(settings_file, cookies_txt):
    store.save_settings(cookie_mode="file", cookie_file=str(cookies_txt))
    assert downloader.cookie_opts() == {"cookiefile": str(cookies_txt)}


def test_browser_mode_passes_the_browser_tuple(settings_file):
    store.save_settings(cookie_mode="browser", cookie_browser="firefox")
    # NOTE: yt-dlp expects (browser, profile, keyring, container).
    assert downloader.cookie_opts() == {"cookiesfrombrowser": ("firefox", None, None, None)}


def test_a_missing_cookie_file_degrades_to_no_cookies(settings_file, tmp_path):
    # NOTE: deliberately NOT an exception - a stale path (file moved or
    # deleted) should cost you the cookies, not every download. The Settings
    # page is where a bad path gets reported.
    store.save_settings(cookie_mode="file", cookie_file=str(tmp_path / "gone.txt"))
    assert downloader.cookie_opts() == {}


def test_an_unsupported_browser_degrades_to_no_cookies(settings_file):
    store.save_settings(cookie_mode="browser", cookie_browser="netscape-navigator")
    assert downloader.cookie_opts() == {}


# --- test_cookie_source ------------------------------------------------------


def test_reports_not_configured_when_off(settings_file):
    store.save_settings(cookie_mode="off")
    assert downloader.test_cookie_source() == {"ok": False, "reason": "not_configured"}


def test_reads_a_real_cookies_file(settings_file, cookies_txt):
    store.save_settings(cookie_mode="file", cookie_file=str(cookies_txt))
    result = downloader.test_cookie_source()
    assert result["ok"] is True
    assert result["count"] == 1


def test_reports_why_a_broken_source_failed(settings_file, tmp_path):
    # NOTE: a malformed file must produce a *reason*, not a silent no-op -
    # "cookies are on but nothing happens" is the outcome to avoid.
    bad = tmp_path / "bad.txt"
    bad.write_text("this is not a cookie jar", encoding="utf-8")
    store.save_settings(cookie_mode="file", cookie_file=str(bad))
    result = downloader.test_cookie_source()
    assert result["ok"] is False
    assert result.get("detail")


# --- privacy -----------------------------------------------------------------


def test_only_the_source_is_persisted(settings_file, cookies_txt):
    store.save_settings(cookie_mode="file", cookie_file=str(cookies_txt))
    written = (settings_file / "settings.json").read_text(encoding="utf-8")
    # NOTE: the path is stored; the cookie VALUE must never be.
    assert "abc123" not in written
    assert "SESSION" not in written


def test_supported_browsers_are_declared(settings_file):
    assert "firefox" in downloader.SUPPORTED_COOKIE_BROWSERS
    assert "chrome" in downloader.SUPPORTED_COOKIE_BROWSERS
