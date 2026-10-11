"""Tests for the data folder and the configurable downloads folder (v2.4.0).

NOTE: paths are the isolated ones from conftest.py; nothing here touches the
developer's real folders. "Windows installer layout" is simulated by
pointing paths.app_dir at a temp <install>\\app next to <install>\\python.
"""

import json
import os
import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mediagrab import app as app_module
from mediagrab import downloader, paths, store

LOCAL = ("127.0.0.1", 50000)
LAN = ("192.168.1.50", 50000)


def _installer_layout(tmp_path, monkeypatch):
    app = tmp_path / "Programs" / "MediaGrab" / "app"
    app.mkdir(parents=True)
    (tmp_path / "Programs" / "MediaGrab" / "python").mkdir()
    monkeypatch.setattr(paths, "app_dir", lambda: str(app))
    return app


# --- paths: where things live -------------------------------------------------


def test_source_and_docker_keep_data_next_to_the_app(monkeypatch, tmp_path):
    monkeypatch.delenv("MEDIAGRAB_DATA_DIR", raising=False)
    monkeypatch.setattr(paths, "app_dir", lambda: str(tmp_path))
    assert paths.windows_install_dir() is None
    assert paths.data_dir() == str(tmp_path)
    assert paths.default_download_dir() == str(tmp_path / "indirilenler")


def test_the_windows_installer_keeps_data_in_localappdata(monkeypatch, tmp_path):
    # NOTE: apart from the program files, so an update or uninstall of the
    # app never touches settings, followed channels, cookies or statistics.
    monkeypatch.delenv("MEDIAGRAB_DATA_DIR", raising=False)
    _installer_layout(tmp_path, monkeypatch)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    assert paths.data_dir() == str(tmp_path / "Local" / "MediaGrab")


def test_the_windows_installer_downloads_into_the_users_downloads_folder(monkeypatch, tmp_path):
    _installer_layout(tmp_path, monkeypatch)
    monkeypatch.setattr(paths, "_windows_downloads_folder", lambda: str(tmp_path / "D" / "Downloads"))
    assert paths.default_download_dir() == str(tmp_path / "D" / "Downloads" / "MediaGrab")


def test_a_folder_merely_called_app_is_not_the_installer(monkeypatch, tmp_path):
    app = tmp_path / "app"
    app.mkdir()
    monkeypatch.setattr(paths, "app_dir", lambda: str(app))
    assert paths.windows_install_dir() is None


def test_mediagrab_data_dir_overrides_everything(monkeypatch, tmp_path):
    _installer_layout(tmp_path, monkeypatch)
    monkeypatch.setenv("MEDIAGRAB_DATA_DIR", str(tmp_path / "elsewhere"))
    assert paths.data_dir() == str(tmp_path / "elsewhere")


@pytest.mark.skipif(os.name != "nt", reason="Windows Known Folders")
def test_the_real_downloads_folder_is_found():
    folder = paths._windows_downloads_folder()
    assert folder and os.path.isabs(folder)


# --- downloader: the setting is what counts --------------------------------------


def test_download_dir_is_the_default_until_set(tmp_path):
    assert downloader.download_dir() == downloader.DOWNLOAD_DIR


def test_download_dir_follows_the_setting_and_creates_it(tmp_path):
    target = tmp_path / "New Folder" / "Videolar"
    store.save_settings(download_dir=str(target))
    assert downloader.download_dir() == str(target)
    assert target.is_dir()
    assert downloader.outtmpl().startswith(str(target))


def test_docker_ignores_a_download_dir_setting(monkeypatch, tmp_path):
    # NOTE: e.g. an old settings file carrying a Windows path - the compose
    # volume decides in Docker.
    store.save_settings(download_dir=str(tmp_path / "C-drive-path"))
    monkeypatch.setattr(downloader, "is_docker", lambda: True)
    assert downloader.download_dir() == downloader.DOWNLOAD_DIR


def test_history_lists_the_configured_folder(tmp_path):
    target = tmp_path / "Videolar"
    (target / "Kanal").mkdir(parents=True)
    (target / "Kanal" / "Yeni.mp4").write_bytes(b"x")
    store.save_settings(download_dir=str(target))
    with TestClient(app_module.app) as c:
        names = [item["filename"] for item in c.get("/api/history").json()]
    assert names == ["Kanal/Yeni.mp4"]


def test_history_lists_several_channel_folders(tmp_path):
    # NOTE: a regression - history() once reused one variable for both the
    # downloads folder and an item's channel folder, so every file after the
    # first one in a subfolder got a wrong path (or a crash across drives).
    target = tmp_path / "Videolar"
    for rel in ("Kanal A/Bir.mp4", "Kanal A/İki.mp4", "Kanal B/Üç.mp3", "Dört.mp4"):
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        (target / rel).write_bytes(b"x")
    store.save_settings(download_dir=str(target))
    with TestClient(app_module.app) as c:
        items = c.get("/api/history").json()
    assert sorted(i["filename"] for i in items) == ["Dört.mp4", "Kanal A/Bir.mp4", "Kanal A/İki.mp4", "Kanal B/Üç.mp3"]
    assert {i["filename"]: i["folder"] for i in items}["Kanal B/Üç.mp3"] == "Kanal B"


# --- API -----------------------------------------------------------------------


def test_the_host_can_edit_a_phone_cannot(client_ip=None):
    with TestClient(app_module.app, client=LOCAL) as c:
        assert c.get("/api/download-dir").json()["editable"] is True
    with TestClient(app_module.app, client=LAN) as c:
        info = c.get("/api/download-dir").json()
        assert info["editable"] is False
        assert c.post("/api/download-dir", json={"path": "C:/x"}).status_code == 403


def test_docker_cannot_change_it(monkeypatch):
    with TestClient(app_module.app, client=LOCAL) as c:
        monkeypatch.setattr(app_module, "is_docker", lambda: True)
        assert c.get("/api/download-dir").json()["editable"] is False
        assert c.post("/api/download-dir", json={"path": "C:/x"}).status_code == 403


def test_changing_it_saves_creates_and_reports(tmp_path):
    target = tmp_path / "Yeni Klasör"
    with TestClient(app_module.app, client=LOCAL) as c:
        res = c.post("/api/download-dir", json={"path": str(target)})
    assert res.status_code == 200
    assert res.json()["path"] == str(target)
    assert res.json()["is_default"] is False
    assert target.is_dir()
    assert not any(target.iterdir()), "the write probe must be cleaned up"
    assert store.get_settings()["download_dir"] == str(target)


def test_an_empty_path_goes_back_to_the_default(tmp_path):
    store.save_settings(download_dir=str(tmp_path / "x"))
    with TestClient(app_module.app, client=LOCAL) as c:
        res = c.post("/api/download-dir", json={"path": ""})
    assert res.json()["is_default"] is True
    assert store.get_settings()["download_dir"] == ""


@pytest.mark.parametrize(
    "make_path, code",
    [
        (lambda tmp: "relative/folder", "relative"),
        (lambda tmp: os.path.join(os.path.dirname(app_module.__file__), "downloads"), "inside_app"),
        (lambda tmp: str(tmp / "a-file.txt"), "not_a_folder"),
    ],
)
def test_bad_folders_are_rejected_and_nothing_changes(tmp_path, make_path, code):
    (tmp_path / "a-file.txt").write_text("x", encoding="utf-8")
    with TestClient(app_module.app, client=LOCAL) as c:
        res = c.post("/api/download-dir", json={"path": make_path(tmp_path)})
    assert res.status_code == 400
    assert res.json()["detail"] == code
    assert store.get_settings()["download_dir"] == ""


def test_a_folder_inside_the_windows_install_is_rejected(monkeypatch, tmp_path):
    # NOTE: an update replaces those files and an uninstall deletes them.
    app = _installer_layout(tmp_path, monkeypatch)
    monkeypatch.setattr(app_module, "windows_install_dir", lambda: str(app.parent))
    with TestClient(app_module.app, client=LOCAL) as c:
        res = c.post("/api/download-dir", json={"path": str(app.parent / "Videolar")})
    assert res.json()["detail"] == "inside_app"


def test_an_unwritable_folder_is_rejected(monkeypatch, tmp_path):
    real_open = open

    def refuse(path, *args, **kwargs):
        if ".mediagrab-write-test-" in str(path):
            raise PermissionError("read-only")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", refuse)
    with TestClient(app_module.app, client=LOCAL) as c:
        res = c.post("/api/download-dir", json={"path": str(tmp_path / "ro")})
    assert res.json()["detail"] == "not_writable"


def test_a_synced_folder_gets_a_warning(tmp_path):
    target = tmp_path / "OneDrive" / "Videolar"
    with TestClient(app_module.app, client=LOCAL) as c:
        res = c.post("/api/download-dir", json={"path": str(target)})
    assert res.status_code == 200
    assert res.json()["cloud"] == "onedrive"


def test_a_settings_backup_never_carries_the_folder(tmp_path):
    # NOTE: a path on this machine - restored elsewhere it would point at
    # nothing (or break Docker).
    store.save_settings(download_dir=str(tmp_path / "Videolar"))
    with TestClient(app_module.app, client=LOCAL) as c:
        exported = json.loads(c.get("/api/settings/export").content)
        assert "download_dir" not in exported["settings"]
        store.save_settings(download_dir="")
        c.post(
            "/api/settings/import",
            json={"settings": {"download_dir": "C:/someone/else"}, "channels": [], "pending": []},
        )
    assert store.get_settings()["download_dir"] == ""


def test_the_folder_picker_is_host_only(monkeypatch):
    called = []
    monkeypatch.setattr(app_module.subprocess, "run", lambda *a, **k: called.append(a))
    with TestClient(app_module.app, client=LAN) as c:
        assert c.post("/api/download-dir/browse").status_code == 403
    assert called == [], "a phone must never pop a dialog on the host"


@pytest.mark.skipif(os.name != "nt", reason="the picker is Windows-only")
def test_the_folder_picker_returns_the_chosen_folder(monkeypatch):
    class Result:
        stdout = "D:\\Videolar\\Müzik"

    seen = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        seen["env"] = kwargs["env"]
        return Result()

    monkeypatch.setattr(app_module.subprocess, "run", fake_run)
    with TestClient(app_module.app, client=LOCAL) as c:
        res = c.post("/api/download-dir/browse?lang=tr")
    assert res.json() == {"path": "D:\\Videolar\\Müzik"}
    assert "nereye" in seen["env"]["MEDIAGRAB_PICKER_TITLE"]
    # NOTE: the modern dialog, run by MediaGrab's own Python - not
    # PowerShell's old tree-view FolderBrowserDialog.
    assert seen["cmd"] == [sys.executable, "-I", app_module.FOLDER_PICKER_SCRIPT]
    assert os.path.isfile(app_module.FOLDER_PICKER_SCRIPT)


def test_the_folder_picker_stands_alone():
    # NOTE: it runs as `python -I folder_picker.py`, where the mediagrab
    # package isn't importable.
    import ast

    tree = ast.parse(Path(app_module.FOLDER_PICKER_SCRIPT).read_text(encoding="utf-8"))
    modules = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    modules |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert modules <= {"ctypes", "os", "sys"}


# --- the installer's "where should videos be saved?" page --------------------------


def _handoff(text):
    path = Path(store.SETTINGS_PATH).parent / app_module.INSTALLER_DOWNLOAD_DIR_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig")  # Inno may write a BOM
    return path


def test_the_installers_choice_is_applied_once_on_start(tmp_path):
    target = tmp_path / "D" / "Videolarım"
    handoff = _handoff(str(target))
    with TestClient(app_module.app):
        pass
    assert store.get_settings()["download_dir"] == str(target)
    assert target.is_dir()
    assert not handoff.exists()


def test_a_reinstall_applies_what_the_installer_page_showed(tmp_path):
    # NOTE: uninstalled with data kept, installed again: the page started
    # from the old setting, the user picked something else - that counts.
    store.save_settings(download_dir=str(tmp_path / "old-setting"))
    handoff = _handoff(str(tmp_path / "picked-on-reinstall"))
    with TestClient(app_module.app):
        pass
    assert store.get_settings()["download_dir"] == str(tmp_path / "picked-on-reinstall")
    assert not handoff.exists()


def test_picking_the_default_on_a_reinstall_clears_the_old_setting(tmp_path):
    store.save_settings(download_dir=str(tmp_path / "old-setting"))
    _handoff(downloader.DOWNLOAD_DIR)
    with TestClient(app_module.app):
        pass
    assert store.get_settings()["download_dir"] == ""


def test_an_unusable_installer_choice_keeps_the_current_folder(tmp_path):
    store.save_settings(download_dir=str(tmp_path / "old-setting"))
    handoff = _handoff("relative/path")
    with TestClient(app_module.app):
        pass
    assert store.get_settings()["download_dir"] == str(tmp_path / "old-setting")
    assert not handoff.exists()


def test_the_installer_writes_the_file_the_app_reads():
    # NOTE: two sides of one handoff (packaging/mediagrab.iss and app.py) -
    # a renamed file on either side would silently drop the user's choice.
    iss = (Path(__file__).parent.parent / "packaging" / "mediagrab.iss").read_text(encoding="utf-8-sig")
    assert "\\" + app_module.INSTALLER_DOWNLOAD_DIR_FILE + "'" in iss
    assert r"{localappdata}\MediaGrab" in iss


def test_the_installer_reads_the_settings_the_app_writes():
    # NOTE: a reinstall (data kept) pre-fills the installer page from this
    # file (packaging/settings_json.iss) - renamed on either side, the page
    # would quietly offer the default instead.
    iss = (Path(__file__).parent.parent / "packaging" / "mediagrab.iss").read_text(encoding="utf-8-sig")
    assert '#include "settings_json.iss"' in iss
    assert "{localappdata}\\MediaGrab\\" + os.path.basename(store.SETTINGS_PATH) in iss
    assert "download_dir" in store.DEFAULT_SETTINGS


# --- 2b: "Move here" / "Leave them there" ----------------------------------------


def _wait_for_move():
    import time

    for _ in range(200):
        if not app_module._move_status()["running"]:
            return app_module._move_status()
        time.sleep(0.02)
    raise AssertionError("the move never finished")


def _old_folder_with_a_video():
    old = Path(downloader.DOWNLOAD_DIR)
    (old / "Kanal").mkdir(parents=True, exist_ok=True)
    (old / "Kanal" / "Eski.mp4").write_bytes(b"video")
    (old / "Kanal" / "Eski.json").write_bytes(b"{}")
    return old


def test_changing_the_folder_remembers_the_old_one_with_downloads(tmp_path):
    old = _old_folder_with_a_video()
    with TestClient(app_module.app, client=LOCAL) as c:
        info = c.post("/api/download-dir", json={"path": str(tmp_path / "Yeni")}).json()
    # NOTE: 1 - the video; its .json info file moves too but isn't "a file" to a person.
    assert info["previous"] == [{"path": str(old), "available": True, "files": 1, "bytes": 7}]


def test_an_empty_old_folder_is_not_offered(tmp_path):
    with TestClient(app_module.app, client=LOCAL) as c:
        info = c.post("/api/download-dir", json={"path": str(tmp_path / "Yeni")}).json()
    assert info["previous"] == []


def test_going_back_to_the_old_folder_drops_the_offer(tmp_path):
    _old_folder_with_a_video()
    with TestClient(app_module.app, client=LOCAL) as c:
        c.post("/api/download-dir", json={"path": str(tmp_path / "Yeni")})
        info = c.post("/api/download-dir", json={"path": ""}).json()
    assert info["previous"] == []


def test_move_here_moves_them_and_history_shows_them(tmp_path):
    old = _old_folder_with_a_video()
    new = tmp_path / "Yeni"
    with TestClient(app_module.app, client=LOCAL) as c:
        c.post("/api/download-dir", json={"path": str(new)})
        assert c.post("/api/download-dir/move", json={"path": str(old)}).status_code == 200
        state = _wait_for_move()
        assert state["result"]["moved"] == 2 and state["error"] is None
        assert [i["filename"] for i in c.get("/api/history").json()] == ["Kanal/Eski.mp4"]
        assert c.get("/api/download-dir").json()["previous"] == []
    assert (new / "Kanal" / "Eski.json").exists()
    assert not old.exists()


def test_leave_them_there_deletes_nothing(tmp_path):
    old = _old_folder_with_a_video()
    with TestClient(app_module.app, client=LOCAL) as c:
        c.post("/api/download-dir", json={"path": str(tmp_path / "Yeni")})
        info = c.post("/api/download-dir/forget", json={"path": str(old)}).json()
    assert info["previous"] == []
    assert (old / "Kanal" / "Eski.mp4").read_bytes() == b"video"


def test_only_a_remembered_folder_can_be_moved(tmp_path):
    # NOTE: never an arbitrary path from a request - that would let any
    # page that reaches the API sweep files out of any folder.
    elsewhere = tmp_path / "Belgeler"
    (elsewhere).mkdir()
    (elsewhere / "film.mp4").write_bytes(b"x")
    with TestClient(app_module.app, client=LOCAL) as c:
        assert c.post("/api/download-dir/move", json={"path": str(elsewhere)}).status_code == 404
        assert c.post("/api/download-dir/forget", json={"path": str(elsewhere)}).status_code == 404
    assert (elsewhere / "film.mp4").exists()


def test_a_phone_cannot_move_or_forget(tmp_path):
    old = _old_folder_with_a_video()
    with TestClient(app_module.app, client=LOCAL) as c:
        c.post("/api/download-dir", json={"path": str(tmp_path / "Yeni")})
    with TestClient(app_module.app, client=LAN) as c:
        assert c.post("/api/download-dir/move", json={"path": str(old)}).status_code == 403
        assert c.post("/api/download-dir/forget", json={"path": str(old)}).status_code == 403


def test_no_move_while_a_download_runs(tmp_path, monkeypatch):
    old = _old_folder_with_a_video()
    with TestClient(app_module.app, client=LOCAL) as c:
        c.post("/api/download-dir", json={"path": str(tmp_path / "Yeni")})
        monkeypatch.setattr(app_module, "_running_downloads", 1)
        res = c.post("/api/download-dir/move", json={"path": str(old)})
    assert res.status_code == 409 and res.json()["detail"] == "downloads_running"
    assert (old / "Kanal" / "Eski.mp4").exists()


def test_downloads_wait_while_a_move_runs():
    import threading

    started = threading.Event()

    def download():
        with app_module._download_slot():
            started.set()

    with app_module._move_cond:
        app_module._move_state["running"] = True
    try:
        worker = threading.Thread(target=download, daemon=True)
        worker.start()
        assert not started.wait(0.3), "a download must not start during a move"
    finally:
        with app_module._move_cond:
            app_module._move_state["running"] = False
            app_module._move_cond.notify_all()
    assert started.wait(2), "and it starts as soon as the move is over"
    worker.join(2)
    assert app_module._running_downloads == 0


def test_the_folder_cant_change_during_a_move(tmp_path, monkeypatch):
    monkeypatch.setitem(app_module._move_state, "running", True)
    with TestClient(app_module.app, client=LOCAL) as c:
        res = c.post("/api/download-dir", json={"path": str(tmp_path / "Yeni")})
    assert res.status_code == 409
    assert store.get_settings()["download_dir"] == ""


def test_an_unplugged_old_drive_stays_on_offer(tmp_path):
    gone = tmp_path / "USB" / "MediaGrab"
    store.save_settings(previous_download_dirs=[str(gone)])
    with TestClient(app_module.app, client=LOCAL) as c:
        info = c.get("/api/download-dir").json()
        assert c.post("/api/download-dir/move", json={"path": str(gone)}).json()["detail"] == "unavailable"
    assert info["previous"] == [{"path": str(gone), "available": False, "files": 0, "bytes": 0}]


def test_an_old_folder_emptied_by_hand_is_dropped(tmp_path):
    old = _old_folder_with_a_video()
    with TestClient(app_module.app, client=LOCAL) as c:
        c.post("/api/download-dir", json={"path": str(tmp_path / "Yeni")})
        shutil.rmtree(old / "Kanal")
        assert c.get("/api/download-dir").json()["previous"] == []
    assert store.get_settings()["previous_download_dirs"] == []


def test_an_installer_choice_offers_the_old_folder_too(tmp_path):
    old = _old_folder_with_a_video()
    _handoff(str(tmp_path / "Kurulumda Seçilen"))
    with TestClient(app_module.app, client=LOCAL) as c:
        assert [p["path"] for p in c.get("/api/download-dir").json()["previous"]] == [str(old)]


def test_a_backup_never_carries_old_folders(tmp_path):
    store.save_settings(previous_download_dirs=[str(tmp_path)])
    with TestClient(app_module.app, client=LOCAL) as c:
        exported = json.loads(c.get("/api/settings/export").content)
    assert "previous_download_dirs" not in exported["settings"]
