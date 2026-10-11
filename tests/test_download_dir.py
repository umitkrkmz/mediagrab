"""Tests for the data folder and the configurable downloads folder (v2.4.0).

NOTE: paths are the isolated ones from conftest.py; nothing here touches the
developer's real folders. "Windows installer layout" is simulated by
pointing paths.app_dir at a temp <install>\\app next to <install>\\python.
"""

import json
import os
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


def test_cloud_markers_match_the_installers_list():
    # NOTE: a deliberate duplicate (setup_mediagrab.py can't import this
    # package) - they must not drift apart.
    import importlib.util

    spec = importlib.util.spec_from_file_location("setup_mediagrab", Path(__file__).parent.parent / "setup_mediagrab.py")
    setup_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(setup_mod)
    assert paths.CLOUD_MARKERS == setup_mod.CLOUD_MARKERS


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
        seen["env"] = kwargs["env"]
        return Result()

    monkeypatch.setattr(app_module.subprocess, "run", fake_run)
    with TestClient(app_module.app, client=LOCAL) as c:
        res = c.post("/api/download-dir/browse?lang=tr")
    assert res.json() == {"path": "D:\\Videolar\\Müzik"}
    assert "nereye" in seen["env"]["MEDIAGRAB_PICKER_TITLE"]


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


def test_a_folder_already_set_in_settings_wins(tmp_path):
    store.save_settings(download_dir=str(tmp_path / "chosen-in-settings"))
    handoff = _handoff(str(tmp_path / "from-installer"))
    with TestClient(app_module.app):
        pass
    assert store.get_settings()["download_dir"] == str(tmp_path / "chosen-in-settings")
    assert not handoff.exists()


def test_an_unusable_installer_choice_keeps_the_default(tmp_path):
    handoff = _handoff("relative/path")
    with TestClient(app_module.app):
        pass
    assert store.get_settings()["download_dir"] == ""
    assert not handoff.exists()


def test_the_installer_writes_the_file_the_app_reads():
    # NOTE: two sides of one handoff (packaging/mediagrab.iss and app.py) -
    # a renamed file on either side would silently drop the user's choice.
    iss = (Path(__file__).parent.parent / "packaging" / "mediagrab.iss").read_text(encoding="utf-8-sig")
    assert "\\" + app_module.INSTALLER_DOWNLOAD_DIR_FILE + "'" in iss
    assert r"{localappdata}\MediaGrab" in iss
