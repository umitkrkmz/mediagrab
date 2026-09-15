"""Tests for run.py's main() - specifically the bind-host decision.

NOTE: this is the single line the whole Docker chicken-and-egg fix (see
V2_PLANNING.md / app.py's _ensure_docker_has_a_password) hangs on, and it had
no test coverage at all before this file. uvicorn.run() itself blocks
forever serving requests, so every test here replaces it with a fake that
just records what it was called with instead of actually starting a server.
"""

import os

import pytest

import run


@pytest.fixture
def clean_port_env(monkeypatch):
    # NOTE: main() writes MEDIAGRAB_PORT directly to os.environ (not via
    # monkeypatch), so a test run's value could otherwise leak into whichever
    # test happens to run next. Establishing this as monkeypatch's restore
    # point undoes that mutation at teardown regardless of what main() did.
    monkeypatch.delenv("MEDIAGRAB_PORT", raising=False)


@pytest.fixture
def uvicorn_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(run.uvicorn, "run", lambda app, host, port: calls.append({"host": host, "port": port}))
    return calls


@pytest.fixture
def thread_calls(monkeypatch):
    calls = []

    class FakeThread:
        def __init__(self, target, args=(), daemon=None):
            calls.append({"target": target, "args": args})

        def start(self):
            pass

    monkeypatch.setattr(run.threading, "Thread", FakeThread)
    return calls


@pytest.fixture
def base_env(monkeypatch, clean_port_env, uvicorn_calls, thread_calls):
    """Port free, not in Docker, remote access off - the common case."""
    monkeypatch.setattr(run, "_port_in_use", lambda port: False)
    monkeypatch.setattr(run, "is_docker", lambda: False)
    monkeypatch.setattr(run, "remote_access_active", lambda settings: False)
    monkeypatch.setattr(run, "get_settings", lambda: {})
    return {"uvicorn": uvicorn_calls, "threads": thread_calls}


def test_binds_to_loopback_by_default(base_env):
    run.main()
    assert base_env["uvicorn"] == [{"host": run.HOST, "port": run.PORT}]


def test_binds_to_all_interfaces_when_remote_access_is_active(base_env, monkeypatch):
    monkeypatch.setattr(run, "remote_access_active", lambda settings: True)
    run.main()
    assert base_env["uvicorn"][0]["host"] == "0.0.0.0"


def test_binds_to_all_interfaces_in_docker_even_without_remote_access(base_env, monkeypatch):
    # NOTE: this is the exact fix from Faz 3 - a fresh container has no
    # password yet, so gating on remote_access_active() alone would make
    # Settings itself unreachable. is_docker() must override it on its own.
    monkeypatch.setattr(run, "is_docker", lambda: True)
    monkeypatch.setattr(run, "remote_access_active", lambda settings: False)
    run.main()
    assert base_env["uvicorn"][0]["host"] == "0.0.0.0"


def test_does_not_open_a_browser_in_docker(base_env, monkeypatch):
    monkeypatch.setattr(run, "is_docker", lambda: True)
    run.main()
    assert base_env["threads"] == []


def test_opens_a_browser_outside_docker(base_env):
    run.main()
    assert len(base_env["threads"]) == 1
    assert base_env["threads"][0]["target"] is run._open_browser
    assert base_env["threads"][0]["args"] == (run.PORT,)


def test_sets_the_port_env_var_before_starting_uvicorn(base_env):
    run.main()
    assert os.environ["MEDIAGRAB_PORT"] == str(run.PORT)


def test_falls_back_to_a_free_port_when_the_default_is_taken_by_another_app(base_env, monkeypatch):
    monkeypatch.setattr(run, "_port_in_use", lambda port: True)
    monkeypatch.setattr(run, "_is_mediagrab_running", lambda port: False)
    monkeypatch.setattr(run, "_find_free_port", lambda: 55123)

    run.main()

    assert base_env["uvicorn"] == [{"host": run.HOST, "port": 55123}]
    assert os.environ["MEDIAGRAB_PORT"] == "55123"


def test_opens_the_existing_instance_instead_of_starting_a_second_one(base_env, monkeypatch):
    monkeypatch.setattr(run, "_port_in_use", lambda port: True)
    monkeypatch.setattr(run, "_is_mediagrab_running", lambda port: True)
    monkeypatch.setattr(run, "time", type("T", (), {"sleep": staticmethod(lambda s: None)})())
    opened = []
    monkeypatch.setattr(run.webbrowser, "open", lambda url: opened.append(url))

    run.main()

    assert opened == [f"http://{run.HOST}:{run.PORT}"]
    assert base_env["uvicorn"] == [], "must not start a second server on top of the running one"
