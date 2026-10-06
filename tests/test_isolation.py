"""Guards conftest.py's user-data isolation.

NOTE: these exist because the suite used to touch the developer's REAL data:
every `with TestClient(app)` runs the app's lifespan, which walks the real
indirilenler/ (deleting leftover .part files) and starts a background check
of every followed channel - reading the real channels.json, calling YouTube,
and writing last_checked_at back into it. Reproduced: one full run changed
the first channel's last_checked_at in the project's own channels.json.
"""

import os
import threading

from fastapi.testclient import TestClient

from mediagrab import app as app_module
from mediagrab import downloader, store
from mediagrab.paths import app_dir


def test_user_data_paths_point_away_from_the_project():
    project = os.path.normcase(os.path.abspath(app_dir()))
    for path in (store.STORE_PATH, store.SETTINGS_PATH, downloader.DOWNLOAD_DIR, downloader.COOKIES_PATH):
        assert not os.path.normcase(os.path.abspath(path)).startswith(project), path


def test_starting_the_app_does_not_check_channels(monkeypatch):
    # NOTE: a followed channel exists (in the isolated store), and the real
    # network call is replaced by a recorder - so if lifespan's background
    # channel check still runs, this sees it instead of YouTube seeing it.
    store.add_channel("https://www.youtube.com/@example", "Example", None, "notify", "audio", "mp3", None)
    called = threading.Event()
    monkeypatch.setattr(downloader, "check_channel_new_videos", lambda *a, **k: called.set() or [])

    with TestClient(app_module.app):
        pass

    assert not called.wait(timeout=1.0)
