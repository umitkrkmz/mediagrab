"""Shared pytest setup: keep every test away from the developer's real data.

NOTE: store.py and downloader.py build their paths from app_dir() at import
time - which, when running from source, is the project folder itself, i.e.
the developer's own channels.json, settings.json and indirilenler/. Most
tests redirect the one path they care about, but any `with TestClient(app)`
also runs the app's lifespan, which touches ALL of them (see
test_isolation.py for what that actually did). This redirects every
user-data path for every test, so a test can only ever opt IN to a path
(by monkeypatching it again itself), never accidentally fall through to the
real one.
"""

import pytest

from mediagrab import app as app_module
from mediagrab import downloader, store


@pytest.fixture(autouse=True)
def _isolate_user_data(tmp_path_factory, monkeypatch):
    # NOTE: its own directory rather than the test's tmp_path, so it can never
    # collide with files a test creates there for its own purposes.
    data_dir = tmp_path_factory.mktemp("user-data")
    monkeypatch.setattr(store, "STORE_PATH", str(data_dir / "channels.json"))
    monkeypatch.setattr(store, "SETTINGS_PATH", str(data_dir / "settings.json"))
    monkeypatch.setattr(downloader, "DOWNLOAD_DIR", str(data_dir / "indirilenler"))
    monkeypatch.setattr(downloader, "COOKIES_PATH", str(data_dir / "cookies" / "cookies.txt"))
    # NOTE: lifespan starts this on a daemon thread that can outlive the test
    # (a real channel check is a network call taking seconds) - by then
    # monkeypatch has restored the real STORE_PATH, so redirecting paths alone
    # isn't enough. Tests that exercise it call _check_channel directly, or
    # patch this again with their own recorder (test_home_server_mode).
    monkeypatch.setattr(app_module, "_check_all_channels", lambda: None)
