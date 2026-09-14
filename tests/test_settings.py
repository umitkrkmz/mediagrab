"""Tests for the general settings store (mediagrab/store.py).

NOTE: cookie-specific option-building lives in test_cookies.py; this file
covers the settings mechanism itself - defaults, persistence, and the
cross-field independence that matters once more than one settings panel
writes to the same settings.json.
"""

import pytest

from mediagrab import store


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    return tmp_path


def test_default_audio_lang_defaults_to_empty(settings_file):
    # NOTE: empty means "no preference" - the video's original audio plays,
    # same as before this setting existed.
    assert store.get_settings()["default_audio_lang"] == ""


def test_default_audio_lang_round_trips(settings_file):
    store.save_settings(default_audio_lang="tr")
    assert store.get_settings()["default_audio_lang"] == "tr"


def test_saving_cookies_does_not_reset_the_default_audio_lang(settings_file):
    # NOTE: the reason this matters - /api/settings replaces the whole
    # object, so two independent Settings panels writing to it must each
    # resend the other panel's current value or they'll clobber each other.
    # This test is about store.py's merge behaviour; app.js's
    # collectSettingsPayload() is what supplies that value on the way in.
    store.save_settings(default_audio_lang="tr")
    store.save_settings(cookie_mode="file", cookie_file="/some/path/cookies.txt")
    assert store.get_settings()["default_audio_lang"] == "tr"


def test_saving_the_default_audio_lang_does_not_reset_cookies(settings_file):
    store.save_settings(cookie_mode="file", cookie_file="/some/path/cookies.txt")
    store.save_settings(default_audio_lang="tr")
    settings = store.get_settings()
    assert settings["cookie_mode"] == "file"
    assert settings["cookie_file"] == "/some/path/cookies.txt"


def test_saving_the_speed_limit_does_not_reset_other_settings(settings_file):
    store.save_settings(default_audio_lang="tr", cookie_mode="file", cookie_file="/some/path/cookies.txt")
    store.save_settings(download_speed_limit_mbps=5)
    settings = store.get_settings()
    assert settings["default_audio_lang"] == "tr"
    assert settings["cookie_mode"] == "file"


def test_saving_other_settings_does_not_reset_the_speed_limit(settings_file):
    store.save_settings(download_speed_limit_mbps=10)
    store.save_settings(default_audio_lang="tr")
    assert store.get_settings()["download_speed_limit_mbps"] == 10


# --- home_server_mode ---------------------------------------------------------


def test_home_server_mode_defaults_to_off(settings_file):
    # NOTE: matches the app's original "you open it, it runs" design - a
    # fresh install must not silently start checking channels in the
    # background before the user has ever opted in.
    assert store.get_settings()["home_server_mode"] is False


def test_home_server_mode_round_trips(settings_file):
    store.save_settings(home_server_mode=True)
    assert store.get_settings()["home_server_mode"] is True


def test_home_server_mode_is_independent_of_remote_access(settings_file):
    store.save_settings(home_server_mode=True, remote_access_enabled=False)
    settings = store.get_settings()
    assert settings["home_server_mode"] is True
    assert settings["remote_access_enabled"] is False
