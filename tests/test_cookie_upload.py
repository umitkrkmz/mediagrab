"""Tests for uploading a cookies.txt in Settings -> Cookies.

NOTE: every cookie value below is fake. The file paths are isolated by
conftest.py (downloader.COOKIES_PATH points into a temp dir), so nothing
here can touch a real cookies.txt.
"""

import json
import os
import stat

import pytest
from fastapi.testclient import TestClient

from mediagrab import app as app_module
from mediagrab import downloader, store

_LINES = [
    "# Netscape HTTP Cookie File",
    "# fake values for testing",
    ".youtube.com\tTRUE\t/\tTRUE\t2145916800\tSAPISID\tfake-yt-a",
    # NOTE: Get cookies.txt LOCALLY writes HttpOnly cookies with this prefix -
    # a plain MozillaCookieJar would skip them as comments.
    "#HttpOnly_.youtube.com\tTRUE\t/\tTRUE\t2145916800\tLOGIN_INFO\tfake-yt-b",
    "www.youtube.com\tFALSE\t/\tFALSE\t0\tPREF\tfake-yt-c",
    ".google.com\tTRUE\t/\tTRUE\t2145916800\tSID\tfake-google",
    ".google.com.tr\tTRUE\t/\tTRUE\t2145916800\tNID\tfake-google-tr",
    ".mybank.example\tTRUE\t/\tTRUE\t2145916800\tsession\tfake-bank",
]
EXPORT_ALL = "\n".join(_LINES) + "\n"


# --- cookie_site --------------------------------------------------------------


@pytest.mark.parametrize(
    "domain, site",
    [
        (".youtube.com", "youtube.com"),
        ("www.youtube.com", "youtube.com"),
        ("m.youtube.com", "youtube.com"),
        ("youtube.com", "youtube.com"),
        (".google.com.tr", "google.com.tr"),
        ("www.bbc.co.uk", "bbc.co.uk"),
        ("accounts.google.com", "google.com"),
        ("localhost", "localhost"),
    ],
)
def test_cookie_site_groups_subdomains_under_their_site(domain, site):
    assert downloader.cookie_site(domain) == site


# --- parse_cookie_text --------------------------------------------------------


def test_parses_httponly_lines():
    names = {c.name for c in downloader.parse_cookie_text(EXPORT_ALL)}
    assert "LOGIN_INFO" in names


def test_windows_line_endings_dont_leak_into_cookie_values():
    # NOTE: the bug this guards - yt-dlp's reader only strips "\n", so a
    # "\r\n" file left "\r" glued to every value and YouTube rejected them.
    jar = downloader.parse_cookie_text(EXPORT_ALL.replace("\n", "\r\n"))
    assert all("\r" not in c.value for c in jar)


def test_a_utf8_bom_is_tolerated():
    assert len(downloader.parse_cookie_text("﻿" + EXPORT_ALL)) == 6


@pytest.mark.parametrize(
    "text, code",
    [
        ("", "empty"),
        ("   \n  ", "empty"),
        ('[{"domain": ".youtube.com"}]', "json"),
        ("just some text\n", "not_netscape"),
        ("# Netscape HTTP Cookie File\n", "no_cookies"),
    ],
)
def test_rejects_what_isnt_a_cookie_file(text, code):
    with pytest.raises(downloader.CookieFileError) as exc:
        downloader.parse_cookie_text(text)
    assert str(exc.value) == code


def test_rejects_an_oversized_upload(monkeypatch):
    monkeypatch.setattr(downloader, "COOKIES_MAX_BYTES", 100)
    with pytest.raises(downloader.CookieFileError) as exc:
        downloader.parse_cookie_text(EXPORT_ALL)
    assert str(exc.value) == "too_large"


# --- inspect / summary --------------------------------------------------------


def test_inspect_suggests_only_youtube_and_google():
    info = downloader.inspect_cookie_text(EXPORT_ALL)
    assert set(info["suggested"]) == {"youtube.com", "google.com", "google.com.tr"}
    assert {"site": "mybank.example", "count": 1} in info["sites"]
    assert info["total"] == 6
    assert info["youtube_signed_in"] is True


def test_a_file_without_a_youtube_session_is_flagged():
    text = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tFALSE\t0\tPREF\tfake\n"
    assert downloader.inspect_cookie_text(text)["youtube_signed_in"] is False


def test_the_summary_never_contains_cookie_names_or_values():
    dumped = json.dumps(downloader.inspect_cookie_text(EXPORT_ALL))
    for secret in ("fake-", "SAPISID", "LOGIN_INFO", "session"):
        assert secret not in dumped


# --- save_uploaded_cookies ----------------------------------------------------


def _saved_text():
    with open(downloader.COOKIES_PATH, encoding="utf-8") as f:
        return f.read()


def test_only_the_chosen_sites_are_written_to_disk():
    summary = downloader.save_uploaded_cookies(EXPORT_ALL, ["youtube.com", "google.com"])
    saved = _saved_text()
    assert "fake-yt-a" in saved and "fake-yt-b" in saved and "fake-google" in saved
    # NOTE: the whole point of the allowlist - an "Export All Cookies" file's
    # other sessions never reach the disk at all.
    assert "fake-bank" not in saved
    assert "fake-google-tr" not in saved
    assert summary["total"] == 4


def test_the_saved_file_is_one_yt_dlp_accepts(monkeypatch):
    downloader.save_uploaded_cookies(EXPORT_ALL, ["youtube.com"])
    store.save_settings(cookie_mode="file", cookie_file=downloader.COOKIES_PATH)
    assert downloader.test_cookie_source() == {"ok": True, "count": 3}


def test_saving_nothing_is_refused_and_keeps_the_previous_file():
    downloader.save_uploaded_cookies(EXPORT_ALL, ["youtube.com"])
    before = _saved_text()
    with pytest.raises(downloader.CookieFileError) as exc:
        downloader.save_uploaded_cookies(EXPORT_ALL, ["not-in-the-file.example"])
    assert str(exc.value) == "nothing_selected"
    assert _saved_text() == before


def test_a_failed_write_leaves_the_previous_file_and_no_temp_file(monkeypatch):
    downloader.save_uploaded_cookies(EXPORT_ALL, ["youtube.com"])
    before = _saved_text()

    def broken_replace(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(downloader.os, "replace", broken_replace)
    with pytest.raises(OSError):
        downloader.save_uploaded_cookies(EXPORT_ALL, ["google.com"])
    assert _saved_text() == before
    assert not os.path.exists(downloader.COOKIES_PATH + ".tmp")


@pytest.mark.skipif(os.name != "posix", reason="POSIX file modes")
def test_the_saved_file_is_owner_only():
    downloader.save_uploaded_cookies(EXPORT_ALL, ["youtube.com"])
    assert stat.S_IMODE(os.stat(downloader.COOKIES_PATH).st_mode) == 0o600


# --- routes -------------------------------------------------------------------


@pytest.fixture
def client():
    with TestClient(app_module.app) as c:
        yield c


def test_inspect_route_returns_an_error_code_for_a_bad_file(client):
    res = client.post("/api/cookies/inspect", json={"content": "not a cookie file"})
    assert res.status_code == 400
    assert res.json()["detail"] == "not_netscape"


def test_inspect_route_saves_nothing(client):
    res = client.post("/api/cookies/inspect", json={"content": EXPORT_ALL})
    assert res.status_code == 200
    assert not os.path.exists(downloader.COOKIES_PATH)
    assert store.get_settings()["cookie_mode"] == "off"


def test_upload_route_saves_and_switches_cookies_to_the_uploaded_file(client):
    res = client.post("/api/cookies/upload", json={"content": EXPORT_ALL, "sites": ["youtube.com"]})
    assert res.status_code == 200
    settings = store.get_settings()
    assert settings["cookie_mode"] == "file"
    assert settings["cookie_file"] == downloader.COOKIES_PATH
    assert downloader.cookie_opts() == {"cookiefile": downloader.COOKIES_PATH}


def test_status_route_reports_a_summary_without_secrets(client):
    client.post("/api/cookies/upload", json={"content": EXPORT_ALL, "sites": ["youtube.com", "google.com"]})
    body = client.get("/api/cookies").json()
    assert body["source"] == "uploaded"
    assert body["path"] is None
    assert body["summary"]["total"] == 4
    assert body["summary"]["youtube_signed_in"] is True
    assert "fake-" not in json.dumps(body)


def test_status_route_with_nothing_configured(client):
    assert client.get("/api/cookies").json() == {
        "mode": "off",
        "source": None,
        "path": None,
        "uploaded_at": None,
        "summary": None,
    }


def test_delete_route_removes_the_upload_and_turns_cookies_off(client):
    client.post("/api/cookies/upload", json={"content": EXPORT_ALL, "sites": ["youtube.com"]})
    res = client.delete("/api/cookies")
    assert res.json() == {"ok": True, "removed": True}
    assert not os.path.exists(downloader.COOKIES_PATH)
    settings = store.get_settings()
    assert settings["cookie_mode"] == "off"
    assert settings["cookie_file"] == ""


def test_delete_route_never_deletes_a_file_the_user_pointed_to(client, tmp_path):
    # NOTE: a path typed in by hand is the user's own file - "Delete cookies"
    # must only ever remove MediaGrab's uploaded copy.
    own_file = tmp_path / "my-cookies.txt"
    own_file.write_text(EXPORT_ALL, encoding="utf-8")
    store.save_settings(cookie_mode="file", cookie_file=str(own_file))

    client.delete("/api/cookies")

    assert own_file.exists()
    assert store.get_settings()["cookie_file"] == str(own_file)
    assert store.get_settings()["cookie_mode"] == "file"


@pytest.mark.parametrize("in_docker", [True, False])
def test_cookie_browsers_route_reports_is_docker(monkeypatch, in_docker):
    monkeypatch.setattr(app_module, "is_docker", lambda: in_docker)
    monkeypatch.setattr(app_module, "_ensure_docker_has_a_password", lambda: None)
    with TestClient(app_module.app) as c:
        assert c.get("/api/cookie-browsers").json()["is_docker"] is in_docker


def test_updated_at_carries_a_timezone():
    # NOTE: the bug this guards - found live in Docker: the container runs in
    # UTC, a naive "19:26" was read by the browser as the USER's local time,
    # and the page showed the upload as three hours old in Turkey.
    downloader.save_uploaded_cookies(EXPORT_ALL, ["youtube.com"])
    updated_at = downloader.cookie_file_summary(downloader.COOKIES_PATH)["updated_at"]
    assert updated_at.endswith("+00:00")



# --- upload time vs. last-updated time ------------------------------------------


def test_upload_records_its_own_time_and_delete_clears_it(client):
    client.post("/api/cookies/upload", json={"content": EXPORT_ALL, "sites": ["youtube.com"]})
    body = client.get("/api/cookies").json()
    assert body["uploaded_at"].endswith("+00:00")
    assert store.get_settings()["cookie_uploaded_at"] == body["uploaded_at"]

    client.delete("/api/cookies")
    assert store.get_settings()["cookie_uploaded_at"] == ""


def test_a_typed_in_path_has_no_upload_time(client, tmp_path):
    own_file = tmp_path / "my-cookies.txt"
    own_file.write_text(EXPORT_ALL, encoding="utf-8")
    store.save_settings(cookie_mode="file", cookie_file=str(own_file), cookie_uploaded_at="2026-01-01T00:00:00+00:00")
    assert client.get("/api/cookies").json()["uploaded_at"] is None


# --- yt-dlp's write-back never clobbers a newer file ---------------------------
#
# NOTE: these use the REAL YoutubeDL (downloader's subclass) - no network, it
# only loads and saves the cookie file. yt-dlp writes its jar back on close();
# a download can run for minutes, and an upload in the meantime must win.


def _run_that_refreshes_cookies():
    """A yt-dlp run that has loaded the cookie file and 'refreshed' every value."""
    ydl = downloader.YoutubeDL({"cookiefile": downloader.COOKIES_PATH, "quiet": True, "no_warnings": True})
    for cookie in ydl.cookiejar:
        cookie.value = "refreshed-by-yt-dlp"
    return ydl


def test_write_back_still_happens_when_nothing_changed():
    # NOTE: the behaviour being protected must still exist - refreshed YouTube
    # cookies are kept by exactly this write-back.
    downloader.save_uploaded_cookies(EXPORT_ALL, ["youtube.com"])
    ydl = _run_that_refreshes_cookies()
    ydl.close()
    assert "refreshed-by-yt-dlp" in _saved_text()


def test_a_new_upload_during_a_run_is_not_overwritten():
    downloader.save_uploaded_cookies(EXPORT_ALL, ["youtube.com"])
    ydl = _run_that_refreshes_cookies()

    downloader.save_uploaded_cookies(EXPORT_ALL, ["youtube.com", "google.com"])  # the user uploads anew
    new_upload = _saved_text()
    ydl.close()  # the old run finishes

    assert _saved_text() == new_upload
    assert "refreshed-by-yt-dlp" not in _saved_text()


def test_deleted_cookies_are_not_brought_back_by_a_finishing_run():
    downloader.save_uploaded_cookies(EXPORT_ALL, ["youtube.com"])
    ydl = _run_that_refreshes_cookies()

    downloader.delete_uploaded_cookies()
    ydl.close()

    assert not os.path.exists(downloader.COOKIES_PATH)


def test_a_run_never_creates_a_cookie_file_that_did_not_exist():
    # NOTE: yt-dlp's own save() would happily create the file - a run pointed
    # at a cookie path that isn't there must not conjure one into existence.
    ydl = downloader.YoutubeDL({"cookiefile": downloader.COOKIES_PATH, "quiet": True, "no_warnings": True})
    ydl.close()
    assert not os.path.exists(downloader.COOKIES_PATH)


def test_a_rotated_session_is_not_reported_as_signed_in():
    # NOTE: found live - after YouTube rejected stale cookies, the write-back
    # left __Secure-3PAPISID behind (YouTube doesn't clear it on rotation) but
    # LOGIN_INFO gone. yt-dlp itself then treats the account as signed OUT
    # (YoutubeBaseInfoExtractor._has_auth_cookies needs LOGIN_INFO too), so
    # the summary must not claim a session either.
    rotated = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t2145916800\t__Secure-3PAPISID\tfake\n"
    assert downloader.inspect_cookie_text(rotated)["youtube_signed_in"] is False
