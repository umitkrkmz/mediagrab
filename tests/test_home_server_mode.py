"""Tests for home_server_mode: the /api/settings restart trigger, and the
periodic channel-check loop it turns on (see app.py's lifespan and
_periodic_channel_check_loop).

NOTE: the launch-time check-once behaviour itself is unchanged and untested
here - see tests/test_app.py and the channel-following tests for that. This
file is specifically about the NEW periodic-vs-once-only distinction.
"""

import pytest
from fastapi.testclient import TestClient

import mediagrab.app as app_module
from mediagrab import store
from mediagrab.models import SettingsUpdateRequest


class _FakeThread:
    """Runs the target synchronously instead of on a real thread - lets a
    test observe (and control) what would otherwise be background work."""

    def __init__(self, target=None, daemon=None):
        self.target = target

    def start(self):
        if self.target:
            self.target()


# --- /api/settings restarting on a real home_server_mode change -------------


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    return tmp_path


def test_turning_home_server_mode_on_triggers_a_restart(settings_file, monkeypatch):
    restart_calls = []
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: restart_calls.append(1))
    monkeypatch.setattr(app_module.threading, "Thread", _FakeThread)

    req = SettingsUpdateRequest(cookie_mode="off", cookie_browser="firefox", cookie_file="", home_server_mode=True)
    app_module.update_settings(req)

    assert restart_calls == [1]
    assert store.get_settings()["home_server_mode"] is True


def test_turning_home_server_mode_off_also_triggers_a_restart(settings_file, monkeypatch):
    store.save_settings(home_server_mode=True)
    restart_calls = []
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: restart_calls.append(1))
    monkeypatch.setattr(app_module.threading, "Thread", _FakeThread)

    req = SettingsUpdateRequest(cookie_mode="off", cookie_browser="firefox", cookie_file="", home_server_mode=False)
    app_module.update_settings(req)

    assert restart_calls == [1]


def test_saving_settings_without_changing_home_server_mode_does_not_restart(settings_file, monkeypatch):
    restart_calls = []
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: restart_calls.append(1))
    monkeypatch.setattr(app_module.threading, "Thread", _FakeThread)

    # NOTE: home_server_mode defaults to False - explicitly resending False
    # (unchanged) alongside an unrelated field change must not restart.
    req = SettingsUpdateRequest(
        cookie_mode="off", cookie_browser="firefox", cookie_file="", default_audio_lang="tr", home_server_mode=False
    )
    app_module.update_settings(req)

    assert restart_calls == []
    assert store.get_settings()["default_audio_lang"] == "tr"


# --- the periodic loop itself -------------------------------------------------


class _StopLoop(Exception):
    """Breaks the intentionally-infinite _periodic_channel_check_loop for testing."""


def test_the_periodic_loop_sleeps_the_configured_interval_then_checks(monkeypatch):
    check_calls = []
    monkeypatch.setattr(app_module, "_check_all_channels", lambda: check_calls.append(1))

    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)
        if len(sleep_calls) >= 3:
            raise _StopLoop()

    monkeypatch.setattr(app_module.time, "sleep", fake_sleep)

    with pytest.raises(_StopLoop):
        app_module._periodic_channel_check_loop()

    assert sleep_calls == [app_module._HOME_SERVER_CHANNEL_CHECK_INTERVAL_SECONDS] * 3
    # NOTE: sleeps BEFORE checking each time - the launch-time check in
    # lifespan() already covers "right away", this loop is purely the
    # repeat-later behaviour on top of it. Only 2 checks, not 3: the 3rd
    # sleep() call is where _StopLoop interrupts the loop, before that
    # iteration's check ever runs.
    assert check_calls == [1, 1]


# --- lifespan wiring: only starts the loop when the setting is actually on --


@pytest.fixture
def client_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setattr(store, "STORE_PATH", str(tmp_path / "channels.json"))
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: None)


class _ObserverThread:
    """Records what it would have run, without actually running it - used
    where the real target is either infinite (_periodic_channel_check_loop)
    or does real I/O (_check_all_channels) that a lifespan test shouldn't
    trigger."""

    started_targets: list = []

    def __init__(self, target=None, daemon=None):
        _ObserverThread.started_targets.append(target)

    def start(self):
        pass


def test_lifespan_starts_the_periodic_loop_when_home_server_mode_is_on(client_settings, monkeypatch):
    store.save_settings(home_server_mode=True)
    monkeypatch.setattr(_ObserverThread, "started_targets", [])
    monkeypatch.setattr(app_module.threading, "Thread", _ObserverThread)

    with TestClient(app_module.app):
        pass

    assert app_module._periodic_channel_check_loop in _ObserverThread.started_targets


def test_lifespan_does_not_start_the_periodic_loop_by_default(client_settings, monkeypatch):
    # home_server_mode defaults to False - no save_settings call needed.
    monkeypatch.setattr(_ObserverThread, "started_targets", [])
    monkeypatch.setattr(app_module.threading, "Thread", _ObserverThread)

    with TestClient(app_module.app):
        pass

    assert app_module._periodic_channel_check_loop not in _ObserverThread.started_targets
