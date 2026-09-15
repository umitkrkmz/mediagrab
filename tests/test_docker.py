"""Tests for Docker-specific behaviour: detection (paths.is_docker) and the
mandatory-first-password check that runs before anything else in Docker
(app.py's _ensure_docker_has_a_password).

NOTE: see V2_PLANNING.md's Docker section for why this exists - a container
always binds to 0.0.0.0 (run.py), unlike a desktop install's "just runs on
localhost until you opt in" default. Without this check, a freshly-started
container would be reachable from the whole network with no login required
at all the very first time it runs.
"""

import pytest
from fastapi.testclient import TestClient

import mediagrab.app as app_module
import mediagrab.downloader as downloader_module
from mediagrab import auth, paths, store


# --- paths.is_docker ---------------------------------------------------------


def test_is_docker_true_when_the_marker_file_exists(monkeypatch):
    monkeypatch.setattr(paths.os.path, "exists", lambda p: p == "/.dockerenv")
    assert paths.is_docker() is True


def test_is_docker_false_when_the_marker_file_is_absent(monkeypatch):
    monkeypatch.setattr(paths.os.path, "exists", lambda p: False)
    assert paths.is_docker() is False


# --- _ensure_docker_has_a_password -------------------------------------------


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    return tmp_path


def test_does_nothing_when_a_password_already_exists(settings_file, monkeypatch):
    salt, password_hash = auth.hash_password("already-set")
    store.save_settings(remote_access_password_salt=salt, remote_access_password_hash=password_hash)
    monkeypatch.delenv("MEDIAGRAB_INITIAL_PASSWORD", raising=False)

    app_module._ensure_docker_has_a_password()  # must not raise, must not change anything

    assert store.get_settings()["remote_access_password_hash"] == password_hash


def test_refuses_to_start_with_no_password_and_no_env_var(settings_file, monkeypatch):
    monkeypatch.delenv("MEDIAGRAB_INITIAL_PASSWORD", raising=False)

    with pytest.raises(RuntimeError):
        app_module._ensure_docker_has_a_password()

    # NOTE: must not have silently enabled remote access without a real
    # password behind it.
    assert store.get_settings()["remote_access_enabled"] is False


def test_sets_the_password_from_the_env_var_when_none_exists_yet(settings_file, monkeypatch):
    monkeypatch.setenv("MEDIAGRAB_INITIAL_PASSWORD", "a-fresh-container-password")

    app_module._ensure_docker_has_a_password()

    settings = store.get_settings()
    assert settings["remote_access_enabled"] is True
    assert auth.verify_password(
        "a-fresh-container-password",
        settings["remote_access_password_salt"],
        settings["remote_access_password_hash"],
    )


def test_a_password_disabled_on_purpose_is_left_alone(settings_file, monkeypatch):
    # NOTE: distinguishes "never set up" (must fail loudly) from "was set up,
    # then deliberately turned off" (a real user choice, not a missing setup
    # step) - only the former should ever refuse to start.
    salt, password_hash = auth.hash_password("was-set-then-disabled")
    store.save_settings(
        remote_access_enabled=False, remote_access_password_salt=salt, remote_access_password_hash=password_hash
    )
    monkeypatch.delenv("MEDIAGRAB_INITIAL_PASSWORD", raising=False)

    app_module._ensure_docker_has_a_password()  # must not raise

    settings = store.get_settings()
    assert settings["remote_access_enabled"] is False
    assert settings["remote_access_password_hash"] == password_hash


# --- lifespan wiring: only runs the check when actually in Docker -----------


@pytest.fixture
def client_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setattr(store, "STORE_PATH", str(tmp_path / "channels.json"))
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: None)


def test_lifespan_does_not_run_the_docker_check_outside_docker(client_settings, monkeypatch):
    monkeypatch.setattr(app_module, "is_docker", lambda: False)
    calls = []
    monkeypatch.setattr(app_module, "_ensure_docker_has_a_password", lambda: calls.append(1))

    with TestClient(app_module.app):
        pass

    assert calls == []


def test_lifespan_runs_the_docker_check_when_in_docker(client_settings, monkeypatch):
    monkeypatch.setattr(app_module, "is_docker", lambda: True)
    calls = []
    monkeypatch.setattr(app_module, "_ensure_docker_has_a_password", lambda: calls.append(1))

    with TestClient(app_module.app):
        pass

    assert calls == [1]


def test_lifespan_propagates_the_docker_startup_failure(client_settings, monkeypatch):
    # NOTE: TestClient's __enter__ triggers lifespan and re-raises whatever it
    # raises - confirms a failed check genuinely stops the app from starting,
    # not just that the function was called.
    monkeypatch.setattr(app_module, "is_docker", lambda: True)

    def _fail():
        raise RuntimeError("no password configured")

    monkeypatch.setattr(app_module, "_ensure_docker_has_a_password", _fail)

    with pytest.raises(RuntimeError):
        with TestClient(app_module.app):
            pass


# --- yt-dlp update uses --user (PYTHONUSERBASE) only in Docker ---------------


def test_ytdlp_update_uses_plain_pip_outside_docker(monkeypatch):
    monkeypatch.setattr(downloader_module, "is_docker", lambda: False)
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(downloader_module.subprocess, "run", fake_run)

    downloader_module.update_ytdlp()

    assert "--user" not in captured["cmd"]


def test_ytdlp_update_uses_user_install_in_docker(monkeypatch):
    # NOTE: --user is what makes this land in PYTHONUSERBASE (a volume-mounted
    # path, set in the Dockerfile) instead of the container's own ephemeral
    # filesystem - see downloader.update_ytdlp's own comment for why that
    # distinction matters.
    monkeypatch.setattr(downloader_module, "is_docker", lambda: True)
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(downloader_module.subprocess, "run", fake_run)

    downloader_module.update_ytdlp()

    assert "--user" in captured["cmd"]


# --- the dependency-update route is Docker-aware ------------------------------


@pytest.fixture
def dep_client_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setattr(store, "STORE_PATH", str(tmp_path / "channels.json"))
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: None)


def test_dependencies_route_reports_is_docker(dep_client_settings, monkeypatch):
    monkeypatch.setattr(app_module, "is_docker", lambda: True)
    # NOTE: not what this test is about - avoids also triggering the
    # mandatory-first-password check (see the tests above) just because
    # is_docker() is mocked True for the whole module.
    monkeypatch.setattr(app_module, "_ensure_docker_has_a_password", lambda: None)
    monkeypatch.setattr(
        app_module.deps, "check_dependencies", lambda: {"reachable": True, "packages": [], "update_count": 0}
    )
    with TestClient(app_module.app) as client:
        body = client.get("/api/dependencies").json()
    assert body["is_docker"] is True


def test_dependencies_update_is_refused_in_docker(dep_client_settings, monkeypatch):
    monkeypatch.setattr(app_module, "is_docker", lambda: True)
    monkeypatch.setattr(app_module, "_ensure_docker_has_a_password", lambda: None)
    update_calls = []
    monkeypatch.setattr(app_module.deps, "update_dependencies", lambda: update_calls.append(1))

    with TestClient(app_module.app) as client:
        res = client.post("/api/dependencies-update")

    assert res.status_code == 400
    # NOTE: refused before ever touching pip - not "tried and failed".
    assert update_calls == []


def test_dependencies_update_still_works_outside_docker(dep_client_settings, monkeypatch):
    monkeypatch.setattr(app_module, "is_docker", lambda: False)
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: None)
    monkeypatch.setattr(app_module.threading, "Thread", lambda target, daemon: type("T", (), {"start": lambda self: None})())
    monkeypatch.setattr(app_module.deps, "update_dependencies", lambda: {"ok": True, "output": ""})

    with TestClient(app_module.app) as client:
        res = client.post("/api/dependencies-update")

    assert res.status_code == 200
    assert res.json()["ok"] is True
