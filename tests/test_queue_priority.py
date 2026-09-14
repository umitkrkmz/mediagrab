"""Tests for reserving executor slots for manual downloads over channel
auto-downloads (see app.py's _submit_auto_download/_finish_auto_download).

NOTE: the executor itself stays a single, shared ThreadPoolExecutor(3) - the
cap is enforced by never SUBMITTING more than _MAX_CONCURRENT_AUTO_DOWNLOADS
auto-download jobs at once, not by giving auto-downloads their own smaller
pool. A manual download always goes straight to `executor.submit`
(/api/download's own route code, unchanged) and is never affected by this.
"""

import pytest
from fastapi.testclient import TestClient

import mediagrab.app as app_module
from mediagrab import store


@pytest.fixture(autouse=True)
def _reset_auto_download_state():
    # NOTE: _active_auto_downloads/_pending_auto_downloads are module-level
    # globals (mirroring `jobs`) - reset around every test so one test's
    # queued/in-flight state can never leak into the next.
    app_module._active_auto_downloads = 0
    app_module._pending_auto_downloads.clear()
    yield
    app_module._active_auto_downloads = 0
    app_module._pending_auto_downloads.clear()


def _mock_submit(monkeypatch):
    submitted = []
    monkeypatch.setattr(app_module.executor, "submit", lambda fn, *a: submitted.append((fn, a)))
    return submitted


def test_an_auto_download_is_submitted_immediately_when_under_the_limit(monkeypatch):
    submitted = _mock_submit(monkeypatch)

    app_module._submit_auto_download("job1", "url1", "video", "best", [])

    assert app_module._active_auto_downloads == 1
    assert len(submitted) == 1
    assert submitted[0][0] is app_module._run_auto_download_job
    assert app_module._pending_auto_downloads == []


def test_a_third_concurrent_auto_download_is_queued_not_submitted(monkeypatch):
    submitted = _mock_submit(monkeypatch)

    app_module._submit_auto_download("job1", "url1", "video", "best", [])
    app_module._submit_auto_download("job2", "url2", "video", "best", [])
    app_module._submit_auto_download("job3", "url3", "video", "best", [])

    # NOTE: the cap (_MAX_CONCURRENT_AUTO_DOWNLOADS) reserves the executor's
    # 3rd slot for a manual download - only 2 of these 3 auto-downloads may
    # ever be submitted at once.
    assert app_module._active_auto_downloads == app_module._MAX_CONCURRENT_AUTO_DOWNLOADS
    assert len(submitted) == 2
    assert len(app_module._pending_auto_downloads) == 1
    assert app_module._pending_auto_downloads[0][0] == "job3"


def test_finishing_one_starts_the_next_pending_one(monkeypatch):
    submitted = _mock_submit(monkeypatch)
    app_module._submit_auto_download("job1", "url1", "video", "best", [])
    app_module._submit_auto_download("job2", "url2", "video", "best", [])
    app_module._submit_auto_download("job3", "url3", "video", "best", [])
    assert len(submitted) == 2

    app_module._finish_auto_download()

    # NOTE: net unchanged - one finished, the queued one immediately took its
    # place, so the slot count itself doesn't dip below the cap.
    assert app_module._active_auto_downloads == app_module._MAX_CONCURRENT_AUTO_DOWNLOADS
    assert len(submitted) == 3
    assert submitted[2][1][0] == "job3"
    assert app_module._pending_auto_downloads == []


def test_finishing_the_last_one_with_nothing_pending_just_frees_the_slot(monkeypatch):
    submitted = _mock_submit(monkeypatch)
    app_module._submit_auto_download("job1", "url1", "video", "best", [])

    app_module._finish_auto_download()

    assert app_module._active_auto_downloads == 0
    assert len(submitted) == 1  # no second submit triggered


def test_run_auto_download_job_always_frees_its_slot_even_on_failure(monkeypatch):
    # NOTE: _finish_auto_download must run in a `finally`, not just after a
    # successful _run_job - otherwise a channel download that errors out
    # would leak its slot forever, eventually starving every future
    # auto-download without anything visibly wrong in the UI.
    monkeypatch.setattr(
        app_module,
        "_run_job",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    app_module._active_auto_downloads = 1

    with pytest.raises(RuntimeError):
        app_module._run_auto_download_job("job1", "url1", "video", "best", [])

    assert app_module._active_auto_downloads == 0


# --- manual downloads are never subject to the auto-download cap -------------


@pytest.fixture
def download_dir(tmp_path, monkeypatch):
    from mediagrab import downloader

    monkeypatch.setattr(downloader, "DOWNLOAD_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def client_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setattr(store, "STORE_PATH", str(tmp_path / "channels.json"))
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: None)


def test_a_manual_download_is_submitted_directly_even_with_both_auto_slots_busy(
    download_dir, client_settings, monkeypatch
):
    submitted = _mock_submit(monkeypatch)
    # NOTE: simulates the exact scenario this feature exists for - a
    # channel's periodic check (see _periodic_channel_check_loop) already
    # has both auto-download slots busy when the user pastes an urgent link.
    app_module._active_auto_downloads = app_module._MAX_CONCURRENT_AUTO_DOWNLOADS

    with TestClient(app_module.app) as client:
        res = client.post(
            "/api/download", json={"url": "https://example.com/x", "kind": "video", "choice": "137"}
        )

    assert res.status_code == 200
    assert len(submitted) == 1
    # NOTE: goes straight to the real _run_job, never through
    # _run_auto_download_job / the slot-counting machinery at all - a manual
    # download's fate is never tied to how many auto-downloads are running.
    assert submitted[0][0] is app_module._run_job
    assert app_module._active_auto_downloads == app_module._MAX_CONCURRENT_AUTO_DOWNLOADS
