"""Tests for the mDNS convenience address (see app.py's _register_mdns/
_close_mdns and _remote_access_status's mdns_url field).

NOTE: lan_url is always the primary, guaranteed-correct address - mDNS is
purely a best-effort extra alongside it (see V2_PLANNING.md's mDNS section
for why: Android Chrome's ".local" resolution is historically unreliable).
These tests use a fake Zeroconf class - no real network/multicast traffic.
"""

import zeroconf as zeroconf_module

import pytest
from fastapi.testclient import TestClient

import mediagrab.app as app_module
from mediagrab import auth, store


@pytest.fixture(autouse=True)
def _reset_mdns_state():
    # NOTE: _zeroconf_instance/_mdns_hostname are module-level globals -
    # reset around every test so one test's registration can't leak into
    # the next (mirrors the auto-download slot tests' own pattern).
    app_module._zeroconf_instance = None
    app_module._mdns_hostname = None
    yield
    app_module._zeroconf_instance = None
    app_module._mdns_hostname = None


class _FakeZeroconf:
    """Stands in for the real Zeroconf class - records what it was asked to
    register/close without touching a real socket."""

    instances: list = []

    def __init__(self):
        self.registered = None
        self.closed = False
        _FakeZeroconf.instances.append(self)

    def register_service(self, info, allow_name_change=False):
        self.registered = (info, allow_name_change)

    def close(self):
        self.closed = True


# --- _register_mdns / _close_mdns --------------------------------------------


def test_register_mdns_sets_the_hostname_on_success(monkeypatch):
    monkeypatch.setattr(zeroconf_module, "Zeroconf", _FakeZeroconf)
    _FakeZeroconf.instances = []

    app_module._register_mdns("192.168.1.50", 8420)

    assert app_module._mdns_hostname == "mediagrab.local"
    assert app_module._zeroconf_instance is not None
    info, allow_name_change = app_module._zeroconf_instance.registered
    assert info.port == 8420
    assert allow_name_change is True


def test_register_mdns_reflects_whatever_hostname_was_actually_claimed(monkeypatch):
    # NOTE: allow_name_change lets the library resolve a collision by
    # renaming - the displayed address must reflect what it actually
    # registered (e.g. "mediagrab-2.local"), never a hardcoded assumption.
    class _RenamingFakeZeroconf(_FakeZeroconf):
        def register_service(self, info, allow_name_change=False):
            info.server = "mediagrab-2.local."
            super().register_service(info, allow_name_change)

    monkeypatch.setattr(zeroconf_module, "Zeroconf", _RenamingFakeZeroconf)

    app_module._register_mdns("192.168.1.50", 8420)

    assert app_module._mdns_hostname == "mediagrab-2.local"


def test_register_mdns_fails_silently_on_any_error(monkeypatch):
    class _FailingZeroconf:
        def __init__(self):
            raise RuntimeError("no multicast support on this interface")

    monkeypatch.setattr(zeroconf_module, "Zeroconf", _FailingZeroconf)

    # NOTE: must never raise - a network without multicast support, or any
    # other registration failure, must never take the whole app down. The
    # LAN IP address (lan_url) always still works regardless.
    app_module._register_mdns("192.168.1.50", 8420)

    assert app_module._mdns_hostname is None
    assert app_module._zeroconf_instance is None


def test_close_mdns_closes_and_clears_the_instance(monkeypatch):
    monkeypatch.setattr(zeroconf_module, "Zeroconf", _FakeZeroconf)
    app_module._register_mdns("192.168.1.50", 8420)
    zc = app_module._zeroconf_instance

    app_module._close_mdns()

    assert zc.closed is True
    assert app_module._zeroconf_instance is None


def test_close_mdns_is_a_noop_when_nothing_was_registered():
    app_module._close_mdns()  # must not raise
    assert app_module._zeroconf_instance is None


# --- _remote_access_status's mdns_url field -----------------------------------


@pytest.fixture
def client_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setattr(store, "STORE_PATH", str(tmp_path / "channels.json"))
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: None)


@pytest.fixture
def client(client_settings):
    with TestClient(app_module.app) as test_client:
        yield test_client


def _enable_remote_access(client, password="a-fine-password"):
    res = client.post("/api/remote-access/password", json={"password": password})
    assert res.status_code == 200, res.text
    res = client.post("/api/remote-access", json={"enabled": True})
    assert res.status_code == 200, res.text
    return password


def test_status_includes_mdns_url_when_a_hostname_is_registered(client):
    password = _enable_remote_access(client)
    client.post("/api/login", json={"password": password})
    app_module._mdns_hostname = "mediagrab.local"

    body = client.get("/api/remote-access").json()

    assert body["mdns_url"] is not None
    assert "mediagrab.local" in body["mdns_url"]


def test_status_mdns_url_is_none_when_nothing_is_registered(client):
    password = _enable_remote_access(client)
    client.post("/api/login", json={"password": password})
    app_module._mdns_hostname = None

    body = client.get("/api/remote-access").json()

    assert body["mdns_url"] is None


def test_status_mdns_url_is_none_while_remote_access_is_inactive(client):
    # NOTE: even if a hostname happened to still be registered (shouldn't
    # normally happen - lifespan only registers when active - but defensive:
    # never show an mDNS address for a feature that's off).
    app_module._mdns_hostname = "mediagrab.local"

    body = client.get("/api/remote-access").json()

    assert body["mdns_url"] is None


# --- lifespan must never block app startup on mDNS registration --------------


class _ObserverThread:
    """Records what it would have run, without actually running it."""

    started_targets: list = []

    def __init__(self, target=None, args=(), daemon=None):
        _ObserverThread.started_targets.append(target)
        self._target = target
        self._args = args

    def start(self):
        pass


def test_lifespan_registers_mdns_on_a_background_thread_not_synchronously(client_settings, monkeypatch):
    # NOTE: regression test - reproduced live. _register_mdns called directly
    # (synchronously) inside lifespan blocked the ENTIRE app's startup for as
    # long as Zeroconf()/register_service's collision probe took to resolve -
    # in one observed case, indefinitely ("Application startup complete."
    # never printed). A try/except around a call only guards against it
    # raising - it does nothing for a call that simply never returns. mDNS is
    # a best-effort convenience (lan_url is unaffected and always usable
    # immediately) and must never be able to delay the app itself starting.
    salt, password_hash = auth.hash_password("x")
    store.save_settings(remote_access_enabled=True, remote_access_password_salt=salt, remote_access_password_hash=password_hash)
    monkeypatch.setattr(_ObserverThread, "started_targets", [])
    monkeypatch.setattr(app_module.threading, "Thread", _ObserverThread)

    with TestClient(app_module.app):
        pass

    assert app_module._register_mdns in _ObserverThread.started_targets
