"""Bringing an old (pre-v2.4.0 Tk installer) MediaGrab's data over on first start.

NOTE: the Windows installer only leaves the old folder's path in
install-migrate-from.txt (packaging/mediagrab.iss); app.py's
_apply_installer_migration does the rest. Isolated folders from conftest.py.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from mediagrab import app as app_module
from mediagrab import downloader, store

ROOT = Path(__file__).parent.parent


def _old_install(tmp_path, **settings) -> Path:
    """A folder the way the old installer left it: app + data side by side."""
    old = tmp_path / "Eski MediaGrab Ç"
    (old / "indirilenler" / "Kanal").mkdir(parents=True)
    (old / "MediaGrab Baslat.bat").write_text("@echo off", encoding="utf-8")
    (old / "settings.json").write_text(json.dumps({"cookie_mode": "file", **settings}), encoding="utf-8")
    (old / "channels.json").write_text(json.dumps({"channels": [{"url": "https://x"}], "pending": []}), encoding="utf-8")
    (old / "cookies.txt").write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    (old / "stats.json").write_text('{"version":1,"backfilled":true,"hours":{}}', encoding="utf-8")
    (old / "indirilenler" / "Kanal" / "Eski.mp4").write_bytes(b"video")
    return old


def _handoff(name, text):
    path = Path(store.SETTINGS_PATH).parent / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig")  # Inno writes a BOM
    return path


def _start():
    with TestClient(app_module.app):
        pass


def test_brings_over_settings_channels_cookies_and_statistics(tmp_path):
    old = _old_install(tmp_path, default_audio_lang="tr")
    handoff = _handoff(app_module.INSTALLER_MIGRATE_FILE, str(old))
    _start()
    assert store.get_settings()["default_audio_lang"] == "tr"
    assert [c["url"] for c in store.list_channels()] == ["https://x"]
    assert Path(downloader.COOKIES_PATH).read_text(encoding="utf-8").startswith("# Netscape")
    assert json.loads(Path(store.STATS_PATH).read_text(encoding="utf-8"))["backfilled"] is True
    assert not handoff.exists()
    assert (old / "settings.json").exists(), "copied, never moved - the old install keeps working"


def test_never_overwrites_what_is_already_here(tmp_path):
    old = _old_install(tmp_path, default_audio_lang="tr")
    store.save_settings(default_audio_lang="en")
    _handoff(app_module.INSTALLER_MIGRATE_FILE, str(old))
    _start()
    assert store.get_settings()["default_audio_lang"] == "en"


def test_an_uploaded_cookie_file_follows_its_copy(tmp_path):
    old = _old_install(tmp_path)
    settings = json.loads((old / "settings.json").read_text(encoding="utf-8"))
    settings["cookie_file"] = str(old / "cookies.txt")
    (old / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    _handoff(app_module.INSTALLER_MIGRATE_FILE, str(old))
    _start()
    assert store.get_settings()["cookie_file"] == downloader.COOKIES_PATH


def test_a_cookie_file_the_user_picked_elsewhere_is_left_alone(tmp_path):
    own = tmp_path / "Belgeler" / "my-cookies.txt"
    own.parent.mkdir()
    own.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    old = _old_install(tmp_path, cookie_file=str(own))
    _handoff(app_module.INSTALLER_MIGRATE_FILE, str(old))
    _start()
    assert store.get_settings()["cookie_file"] == str(own)


def test_old_videos_are_offered_to_move_here(tmp_path):
    old = _old_install(tmp_path)
    _handoff(app_module.INSTALLER_MIGRATE_FILE, str(old))
    with TestClient(app_module.app, client=("127.0.0.1", 50000)) as c:
        previous = c.get("/api/download-dir").json()["previous"]
    assert previous == [{"path": str(old / "indirilenler"), "available": True, "files": 1, "bytes": 5}]
    assert (old / "indirilenler" / "Kanal" / "Eski.mp4").exists(), "nothing moved without asking"


def test_choosing_the_old_folder_in_the_installer_means_nothing_to_move(tmp_path):
    old = _old_install(tmp_path)
    _handoff(app_module.INSTALLER_MIGRATE_FILE, str(old))
    _handoff(app_module.INSTALLER_DOWNLOAD_DIR_FILE, str(old / "indirilenler"))
    with TestClient(app_module.app, client=("127.0.0.1", 50000)) as c:
        info = c.get("/api/download-dir").json()
        history = [i["filename"] for i in c.get("/api/history").json()]
    assert info["path"] == str(old / "indirilenler")
    assert info["previous"] == []
    assert history == ["Kanal/Eski.mp4"]


def test_a_missing_old_folder_is_ignored(tmp_path):
    handoff = _handoff(app_module.INSTALLER_MIGRATE_FILE, str(tmp_path / "gone"))
    _start()
    assert not handoff.exists()
    assert store.get_settings()["previous_download_dirs"] == []


def test_the_installer_names_the_file_the_app_reads():
    iss = (ROOT / "packaging" / "mediagrab.iss").read_text(encoding="utf-8-sig")
    assert "\\" + app_module.INSTALLER_MIGRATE_FILE + "'" in iss


def test_the_copied_files_are_the_old_installers_user_data():
    # NOTE: what the old Tk installer (setup_mediagrab.py, removed in v2.4.0)
    # kept as user data - its USER_DATA_ENTRIES, a fixed fact now. Everything
    # but the videos is brought over.
    old_user_data = ("indirilenler", "channels.json", "settings.json", "cookies.txt", "stats.json")
    assert set(app_module._migrated_targets()) == set(old_user_data) - {"indirilenler"}
