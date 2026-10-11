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


class FakeServer:
    """Stands in for uvicorn.Server: records what it was asked to serve."""

    calls: list = []
    crash: "Exception | None" = None

    def __init__(self, config):
        self.config = config
        self.started = False
        self.should_exit = False

    def run(self):
        if FakeServer.crash:
            raise FakeServer.crash
        FakeServer.calls.append({"host": self.config.host, "port": self.config.port})
        self.started = True


@pytest.fixture
def uvicorn_calls(monkeypatch):
    FakeServer.calls = []
    FakeServer.crash = None
    monkeypatch.setattr(run.uvicorn, "Server", FakeServer)
    # NOTE: never the real tray icon in these tests (test_tray.py has those).
    monkeypatch.setattr(run, "_tray_wanted", lambda: False)
    return FakeServer.calls


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


# --- no console (pythonw.exe, the Windows installer's shortcut) ----------------
# NOTE: regression. Under pythonw sys.stdout/sys.stderr/sys.stdin are None:
# uvicorn's log setup called sys.stdout.isatty() and crashed, then the
# "press Enter" input() in the error handler raised "lost sys.stdin" - the app
# died with nothing on screen (found in the first installer build).


def test_without_a_console_output_goes_to_a_log_file(monkeypatch, tmp_path):
    monkeypatch.setattr(run.sys, "stdout", None)
    monkeypatch.setattr(run.sys, "stderr", None)
    path = run._ensure_output_streams(str(tmp_path))
    try:
        assert path == str(tmp_path / run.LOG_NAME)
        assert run.sys.stdout is run.sys.stderr
        assert run.sys.stdout.isatty() is False  # what uvicorn asks
        print("hello from pythonw")
    finally:
        run.sys.stdout.close()
    assert "hello from pythonw" in (tmp_path / run.LOG_NAME).read_text(encoding="utf-8")


def test_with_a_console_nothing_is_redirected(monkeypatch, tmp_path):
    before = (run.sys.stdout, run.sys.stderr)
    assert run._ensure_output_streams(str(tmp_path)) is None
    assert (run.sys.stdout, run.sys.stderr) == before
    assert not (tmp_path / run.LOG_NAME).exists()


def test_a_large_log_is_kept_once_as_old(monkeypatch, tmp_path):
    log = tmp_path / run.LOG_NAME
    log.write_bytes(b"x" * (run.LOG_MAX_BYTES + 1))
    monkeypatch.setattr(run.sys, "stdout", None)
    monkeypatch.setattr(run.sys, "stderr", None)
    run._ensure_output_streams(str(tmp_path))
    run.sys.stdout.close()
    assert (tmp_path / (run.LOG_NAME + ".old")).stat().st_size == run.LOG_MAX_BYTES + 1
    assert log.stat().st_size == 0


@pytest.mark.skipif(os.name != "nt", reason="the message box is Windows-only")
def test_a_startup_crash_without_a_console_shows_a_message_box(base_env, monkeypatch, tmp_path):
    import ctypes

    boxes = []
    monkeypatch.setattr(ctypes.windll.user32, "MessageBoxW", lambda *a: boxes.append(a[1]) or 1)
    monkeypatch.setattr("builtins.input", lambda *a: pytest.fail("input() needs a console"))
    monkeypatch.setattr(run.sys, "stdin", None)

    FakeServer.crash = RuntimeError("boom")
    with pytest.raises(SystemExit) as exit_info:
        run.main()
    assert exit_info.value.code == 1
    assert len(boxes) == 1
    assert "MediaGrab" in boxes[0]


@pytest.mark.skipif(os.name != "nt", reason="console windows are a Windows thing")
def test_without_a_console_child_programs_open_no_window(monkeypatch):
    # NOTE: regression. Under pythonw every console child (ffprobe, ffmpeg,
    # Deno, version checks) flashed its own console window open and shut.
    import subprocess

    seen = []
    original = subprocess.Popen.__init__

    def recorder(self, *args, **kwargs):
        seen.append(kwargs.get("creationflags", 0))
        original(self, *args, **kwargs)

    monkeypatch.setattr(subprocess.Popen, "__init__", recorder)
    run._hide_child_console_windows()

    subprocess.run([run.sys.executable, "-c", "pass"], check=True)
    subprocess.run([run.sys.executable, "-c", "pass"], check=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    assert seen[0] & subprocess.CREATE_NO_WINDOW
    assert seen[1] & subprocess.CREATE_NO_WINDOW
    assert seen[1] & subprocess.CREATE_NEW_PROCESS_GROUP, "a caller's own flags must survive"


def test_with_a_console_child_programs_are_left_alone(base_env, monkeypatch):
    import subprocess

    original = subprocess.Popen.__init__
    run.main()
    assert subprocess.Popen.__init__ is original


# --- the Windows tray icon (v2.4.0) ------------------------------------------------


def test_no_tray_from_source_or_in_docker(monkeypatch):
    monkeypatch.delenv("MEDIAGRAB_TRAY", raising=False)
    monkeypatch.setattr(run, "windows_install_dir", lambda: None)
    assert run._tray_wanted() is False
    monkeypatch.setattr(run, "windows_install_dir", lambda: "C:/Programs/MediaGrab")
    monkeypatch.setattr(run, "is_docker", lambda: True)
    assert run._tray_wanted() is False


@pytest.mark.skipif(os.name != "nt", reason="the tray icon is Windows-only")
def test_the_windows_installer_gets_a_tray_icon(monkeypatch):
    monkeypatch.delenv("MEDIAGRAB_TRAY", raising=False)
    monkeypatch.setattr(run, "is_docker", lambda: False)
    monkeypatch.setattr(run, "windows_install_dir", lambda: "C:/Programs/MediaGrab")
    assert run._tray_wanted() is True
    monkeypatch.setenv("MEDIAGRAB_TRAY", "0")
    assert run._tray_wanted() is False


@pytest.mark.skipif(os.name != "nt", reason="the tray icon is Windows-only")
def test_quitting_from_the_tray_stops_mediagrab(monkeypatch, clean_port_env):
    # NOTE: end to end - a real server and a real icon; WM_CLOSE to the
    # icon's window is exactly what the installer/uninstaller sends.
    import ctypes
    import threading

    from mediagrab import tray

    port = run._find_free_port()
    monkeypatch.setattr(run, "PORT", port)
    monkeypatch.setattr(run, "_open_browser", lambda port: None)
    monkeypatch.setattr(run, "_tray_wanted", lambda: True)
    monkeypatch.setattr(run, "remote_access_active", lambda settings: False)
    finished = threading.Event()

    def serve():
        run.main()
        finished.set()

    # NOTE: this process's own icon (tray._running), never a lookup by class
    # name - that could hit the developer's real MediaGrab and close it.
    threading.Thread(target=serve, daemon=True).start()
    for _ in range(300):
        if run._is_mediagrab_running(port) and tray._running is not None and tray._running.added:
            break
        run.time.sleep(0.05)
    else:
        if run._is_mediagrab_running(port) and tray._running is None and os.environ.get("CI"):
            # NOTE: run.py carries on without an icon when there's no
            # notification area (a CI runner) - nothing to send WM_CLOSE to.
            pytest.skip("no notification area on this CI runner")
        pytest.fail("MediaGrab and its tray icon never came up")

    # NOTE: an open MediaGrab tab keeps this live event stream connected - a
    # graceful shutdown must not wait on it forever.
    import http.client

    stream = http.client.HTTPConnection(run.HOST, port, timeout=30)
    stream.request("GET", "/api/events")
    assert stream.getresponse().status == 200

    hwnd = tray._running.hwnd
    ctypes.windll.user32.PostMessageW(ctypes.c_void_p(hwnd), tray.WM_CLOSE, 0, 0)
    assert finished.wait(20), "main() must return once the tray asks it to quit"
    assert not run._port_in_use(port)
    assert not ctypes.windll.user32.IsWindow(ctypes.c_void_p(hwnd)), "the icon and its window are gone too"
    assert tray._running is None
