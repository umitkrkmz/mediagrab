"""Tests for the disk-space guard (app.py's _has_enough_disk_space and its
two call sites: the /api/download route, and again inside _run_job right
before a queued job actually starts).

NOTE: a Raspberry Pi or any small-SSD host is exactly the case this protects -
without it, a large video/playlist can fill the disk mid-download and leave
yt-dlp/ffmpeg failing confusingly, or (on a constrained host) destabilize the
whole machine. See V2_PLANNING.md's "Disk Alani Kalkani" note.
"""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import mediagrab.app as app_module
from mediagrab import store


def _usage(free_bytes: int) -> SimpleNamespace:
    return SimpleNamespace(total=0, used=0, free=free_bytes)


@pytest.fixture
def download_dir(tmp_path, monkeypatch):
    from mediagrab import downloader

    monkeypatch.setattr(downloader, "DOWNLOAD_DIR", str(tmp_path))
    return tmp_path


# --- _has_enough_disk_space ---------------------------------------------------


def test_no_estimate_passes_when_above_the_absolute_floor(download_dir, monkeypatch):
    monkeypatch.setattr(app_module.shutil, "disk_usage", lambda path: _usage(app_module._MIN_FREE_DISK_BYTES + 1))
    assert app_module._has_enough_disk_space(None) is True


def test_no_estimate_fails_when_at_or_below_the_absolute_floor(download_dir, monkeypatch):
    monkeypatch.setattr(app_module.shutil, "disk_usage", lambda path: _usage(app_module._MIN_FREE_DISK_BYTES - 1))
    assert app_module._has_enough_disk_space(None) is False


def test_an_estimate_requires_headroom_beyond_an_exact_fit(download_dir, monkeypatch):
    # NOTE: exactly enough for the file itself, with nothing left over for the
    # safety margin - must be refused, not just barely accepted.
    estimate = 500_000_000
    monkeypatch.setattr(app_module.shutil, "disk_usage", lambda path: _usage(estimate))
    assert app_module._has_enough_disk_space(estimate) is False


def test_an_estimate_passes_with_enough_headroom(download_dir, monkeypatch):
    estimate = 500_000_000
    monkeypatch.setattr(app_module.shutil, "disk_usage", lambda path: _usage(int(estimate * 1.5)))
    assert app_module._has_enough_disk_space(estimate) is True


def test_a_tiny_estimate_still_uses_the_margin_not_the_absolute_floor(download_dir, monkeypatch):
    # NOTE: a real estimate - even a small one - is more informative than the
    # generic 1 GB floor, so it must be what's actually compared against.
    estimate = 1000
    monkeypatch.setattr(app_module.shutil, "disk_usage", lambda path: _usage(2000))
    assert app_module._has_enough_disk_space(estimate) is True


# --- the /api/download route ---------------------------------------------------


@pytest.fixture
def client_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setattr(store, "STORE_PATH", str(tmp_path / "channels.json"))
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: None)


def test_the_download_route_refuses_to_queue_a_job_when_disk_is_full(download_dir, client_settings, monkeypatch):
    monkeypatch.setattr(app_module.shutil, "disk_usage", lambda path: _usage(0))
    jobs_before = dict(app_module.jobs)
    with TestClient(app_module.app) as client:
        res = client.post(
            "/api/download",
            json={"url": "https://example.com/x", "kind": "video", "choice": "137", "estimated_size_bytes": 500_000_000},
        )
    assert res.status_code == 507
    # NOTE: a request that's already doomed must never get a job_id / queue
    # slot at all - not "queued then immediately failed".
    assert app_module.jobs == jobs_before


def test_the_download_route_accepts_a_request_with_plenty_of_free_space(
    download_dir, client_settings, monkeypatch
):
    monkeypatch.setattr(app_module.shutil, "disk_usage", lambda path: _usage(100 * 1024**3))
    # NOTE: the job still runs (in a real thread) after this - not awaited or
    # verified here, only that the route itself accepted and queued it.
    monkeypatch.setattr(app_module, "_run_job", lambda *a, **k: None)
    with TestClient(app_module.app) as client:
        res = client.post(
            "/api/download",
            json={"url": "https://example.com/x", "kind": "video", "choice": "137", "estimated_size_bytes": 500_000_000},
        )
    assert res.status_code == 200
    assert "job_id" in res.json()


# --- re-checked inside _run_job, right before the download actually starts ---


def test_run_job_fails_the_job_if_disk_filled_up_while_it_was_queued(download_dir, monkeypatch):
    # NOTE: simulates the exact scenario this whole feature is for - a
    # playlist bulk download where an EARLIER file filled the disk before a
    # LATER one's turn came up. The /api/download-time check alone can't catch
    # this; only a re-check right before the download itself starts can.
    monkeypatch.setattr(app_module.shutil, "disk_usage", lambda path: _usage(0))

    download_calls = []
    # NOTE: mocked (not just relied on the disk check to short-circuit before
    # this) and tracked via a plain list rather than a raised exception - an
    # exception here would land in _run_job's own `except Exception` handler
    # and get turned into a job["error"] string, which could accidentally
    # still contain the word "disk" and make the assertion below pass for the
    # wrong reason even if the disk check regressed. A call-count check can't
    # be fooled that way.
    monkeypatch.setattr(app_module.downloader, "download", lambda *a, **k: download_calls.append(1))

    job_id = "test-disk-full-job"
    with app_module.jobs_lock:
        app_module.jobs[job_id] = app_module._new_job_record()
    try:
        app_module._run_job(job_id, "https://example.com/x", "video", "137", [], estimated_size_bytes=500_000_000)
        assert download_calls == [], "downloader.download() must never run once the disk-space check has failed"
        job = app_module.jobs[job_id]
        assert job["state"] == "hata"
        assert "disk" in job["error"].lower()
    finally:
        app_module.jobs.pop(job_id, None)
