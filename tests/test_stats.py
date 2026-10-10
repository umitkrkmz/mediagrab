"""Tests for download statistics: what's counted, how it's stored and grouped.

NOTE: no network, no yt-dlp. ffprobe is stubbed (downloader.get_stream_info)
except where a test says otherwise; every path is the isolated one from
conftest.py.
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mediagrab import app as app_module
from mediagrab import downloader, stats, store

# NOTE: conftest replaces this with a no-op for every test (it starts a
# thread); the real one is kept here, captured at import time - before any
# fixture runs - for the two tests that exercise it.
REAL_START_STATS_BACKFILL = app_module._start_stats_backfill


def _entry(site="YouTube", kind="video", fmt="1080p", size=100):
    return {"site": site, "kind": kind, "format": fmt, "bytes": size}


# --- store: persistence ---------------------------------------------------------


def test_the_same_site_kind_and_format_in_one_hour_are_merged():
    store.record_downloads([("2026-10-10T18", _entry(size=100)), ("2026-10-10T18", _entry(size=50))])
    rows = store.get_stats()["hours"]["2026-10-10T18"]
    assert rows == [{"site": "YouTube", "kind": "video", "format": "1080p", "count": 2, "bytes": 150}]


def test_different_formats_stay_apart():
    store.record_downloads([("2026-10-10T18", _entry(fmt="1080p")), ("2026-10-10T18", _entry(fmt="720p"))])
    assert len(store.get_stats()["hours"]["2026-10-10T18"]) == 2


def test_only_numbers_are_stored():
    # NOTE: the privacy promise in the UI - nothing that names WHAT was
    # downloaded ever reaches stats.json.
    store.record_downloads([("2026-10-10T18", _entry())])
    with open(store.STATS_PATH, encoding="utf-8") as f:
        stored = json.load(f)
    row = stored["hours"]["2026-10-10T18"][0]
    assert set(row) == {"site", "kind", "format", "count", "bytes"}


def test_a_corrupt_stats_file_starts_over_instead_of_failing():
    os.makedirs(os.path.dirname(store.STATS_PATH), exist_ok=True)
    with open(store.STATS_PATH, "w", encoding="utf-8") as f:
        f.write("{not json")
    assert store.get_stats() == {"version": 1, "backfilled": False, "hours": {}}
    store.record_downloads([("2026-10-10T18", _entry())])
    assert store.get_stats()["hours"]["2026-10-10T18"][0]["count"] == 1


def test_saving_leaves_no_temp_file_behind():
    store.record_downloads([("2026-10-10T18", _entry())])
    assert not os.path.exists(store.STATS_PATH + ".tmp")


def test_reset_empties_but_stays_marked_as_imported():
    # NOTE: otherwise the next start would re-import every file on disk and
    # "reset" would undo itself.
    store.record_downloads([("2026-10-10T18", _entry())])
    store.reset_stats()
    data = store.get_stats()
    assert data["hours"] == {}
    assert data["backfilled"] is True


# --- stats: classifying a finished file -----------------------------------------


@pytest.mark.parametrize(
    "extractor, expected",
    [
        ("Youtube", "YouTube"),
        ("YoutubeTab", "YouTube"),
        ("Soundcloud", "SoundCloud"),
        ("TwitchVod", "Twitch"),
        ("Vimeo", "Vimeo"),
        ("Generic", "Generic"),
        ("SomeNewSite", "SomeNewSite"),
        (None, ""),
    ],
)
def test_site_names(extractor, expected):
    assert stats.site_name(extractor) == expected


def _write_media(folder, name, size=1000, extractor="Youtube"):
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    if extractor:
        with open(downloader.metadata_sidecar_path(str(path)), "w", encoding="utf-8") as f:
            json.dump({"extractor": extractor, "title": "not stored"}, f)
    return path


def test_an_audio_file_counts_by_its_extension(tmp_path):
    path = _write_media(tmp_path, "Song.opus", size=1234)
    assert stats.classify(str(path)) == {"site": "YouTube", "kind": "audio", "format": "opus", "bytes": 1234}


def test_a_video_counts_by_the_resolution_actually_in_the_file(tmp_path, monkeypatch):
    path = _write_media(tmp_path, "Clip.mp4", extractor="Soundcloud")
    monkeypatch.setattr(downloader, "get_stream_info", lambda p: {"video": {"quality": "720p"}, "audio": None})
    assert stats.classify(str(path))["format"] == "720p"
    assert stats.classify(str(path))["site"] == "SoundCloud"


def test_subtitles_and_transcripts_are_not_counted(tmp_path):
    assert stats.classify(str(_write_media(tmp_path, "Clip.tr.srt"))) is None
    assert stats.classify(str(_write_media(tmp_path, "Clip.txt"))) is None


def test_a_file_without_a_sidecar_has_an_unknown_site(tmp_path):
    path = _write_media(tmp_path, "Old.mp3", extractor=None)
    assert stats.classify(str(path))["site"] == ""


def test_record_finished_never_raises(monkeypatch):
    monkeypatch.setattr(stats, "classify", lambda path: 1 / 0)
    stats.record_finished("whatever.mp4")


# --- stats: one-time import of what's already on disk ---------------------------


def test_backfill_counts_existing_files_once_and_marks_it_done(monkeypatch):
    folder = Path(downloader.DOWNLOAD_DIR)
    old = _write_media(folder / "Kanal", "Old.m4a", size=10)
    new = _write_media(folder / "Kanal", "New.m4a", size=20)
    os.utime(old, (1_000_000_000, 1_000_000_000))  # 2001-09-09
    os.utime(new, (2_000_000_000, 2_000_000_000))  # after the cutoff below

    assert stats.backfill(cutoff=1_500_000_000) == 1
    data = store.get_stats()
    assert data["backfilled"] is True
    assert list(data["hours"]) == ["2001-09-09T01"]
    assert data["hours"]["2001-09-09T01"][0]["bytes"] == 10


def test_backfill_is_not_started_again_once_done(monkeypatch):
    calls = []
    monkeypatch.setattr(app_module.stats, "backfill", lambda cutoff: calls.append(cutoff))
    store.reset_stats()  # marks the import as done
    REAL_START_STATS_BACKFILL()
    assert calls == []


def test_backfill_runs_on_first_start(monkeypatch):
    done = threading.Event()
    monkeypatch.setattr(app_module.stats, "backfill", lambda cutoff: done.set())
    REAL_START_STATS_BACKFILL()
    assert done.wait(timeout=5)


# --- stats: grouping into the viewer's days/weeks/months ------------------------

NOW = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)  # a Wednesday


def _data(*items):
    hours: dict = {}
    for hour, entry in items:
        store._add_stat(hours, hour, entry)
    return {"hours": hours}


def test_a_late_evening_download_lands_on_the_viewers_next_day():
    # NOTE: 22:30 UTC on the 13th is 01:30 on the 14th in Turkey (UTC+3) -
    # the reason hours are stored in UTC and grouped with the browser's offset.
    data = _data(("2026-10-13T22", _entry()))
    turkey = stats.summarize(data, "day", 180, NOW)
    utc = stats.summarize(data, "day", 0, NOW)
    assert turkey["buckets"][-1] == {"start": "2026-10-14", "count": 1, "bytes": 100}
    assert utc["buckets"][-2] == {"start": "2026-10-13", "count": 1, "bytes": 100}


def test_day_view_has_fourteen_days_ending_today():
    summary = stats.summarize(_data(), "day", 0, NOW)
    assert len(summary["buckets"]) == 14
    assert summary["buckets"][0]["start"] == "2026-10-01"
    assert summary["buckets"][-1]["start"] == "2026-10-14"


def test_weeks_start_on_monday():
    summary = stats.summarize(_data(("2026-10-12T08", _entry())), "week", 0, NOW)
    assert len(summary["buckets"]) == 12
    assert summary["buckets"][-1] == {"start": "2026-10-12", "count": 1, "bytes": 100}


def test_month_view_crosses_the_year_boundary():
    summary = stats.summarize(_data(), "month", 0, NOW)
    starts = [b["start"] for b in summary["buckets"]]
    assert starts[0] == "2025-11-01"
    assert starts[-1] == "2026-10-01"
    assert "2026-01-01" in starts


def test_breakdowns_cover_the_window_and_totals_cover_everything():
    data = _data(
        ("2026-10-14T09", _entry(site="YouTube", kind="audio", fmt="opus", size=5)),
        ("2026-10-14T09", _entry(site="YouTube", kind="audio", fmt="opus", size=5)),
        ("2026-10-13T09", _entry(site="SoundCloud", kind="audio", fmt="mp3", size=7)),
        ("2026-10-12T09", _entry(site="YouTube", kind="video", fmt="1080p", size=100)),
        ("2025-01-01T09", _entry(site="Vimeo", kind="video", fmt="720p", size=1000)),
    )
    summary = stats.summarize(data, "day", 0, NOW)
    window = summary["window"]
    assert window["count"] == 4
    assert window["bytes"] == 117
    assert [row["name"] for row in window["sites"]] == ["YouTube", "SoundCloud"]
    assert window["audio_formats"] == [
        {"name": "opus", "count": 2, "bytes": 10},
        {"name": "mp3", "count": 1, "bytes": 7},
    ]
    assert window["video_formats"] == [{"name": "1080p", "count": 1, "bytes": 100}]
    assert summary["total"] == {"count": 5, "bytes": 1117, "since": "2025-01-01"}


def test_hours_in_the_future_are_left_out_of_the_window():
    # NOTE: a clock that moved backwards - the bars and the breakdowns must
    # still agree with each other.
    summary = stats.summarize(_data(("2026-12-01T09", _entry())), "day", 0, NOW)
    assert summary["window"]["count"] == 0
    assert summary["window"]["sites"] == []


def test_an_unknown_period_falls_back_to_days():
    assert stats.summarize(_data(), "decade", 0, NOW)["period"] == "day"


# --- app: recording and the API -------------------------------------------------


@pytest.mark.parametrize("kind, recorded", [("audio", True), ("video", True), ("subtitle", False), ("transcript", False)])
def test_a_finished_job_is_recorded_only_for_audio_and_video(monkeypatch, tmp_path, kind, recorded):
    path = str(tmp_path / "file.bin")
    calls = []
    monkeypatch.setattr(app_module.downloader, "download", lambda *a, **k: path)
    monkeypatch.setattr(app_module, "_has_enough_disk_space", lambda size: True)
    monkeypatch.setattr(app_module.stats, "record_finished", lambda p: calls.append(p))
    job_id = f"test-stats-{kind}"
    with app_module.jobs_lock:
        app_module.jobs[job_id] = app_module._new_job_record()
    try:
        app_module._run_job(job_id, "https://example.com/v", kind, "best", [])
        assert app_module.jobs[job_id]["state"] == "bitti"
    finally:
        with app_module.jobs_lock:
            app_module.jobs.pop(job_id, None)
    assert calls == ([path] if recorded else [])


def test_stats_api_returns_the_summary_and_disk():
    store.record_downloads([(stats.utc_hour(), _entry(kind="audio", fmt="mp3", size=42))])
    with TestClient(app_module.app) as c:
        data = c.get("/api/stats?period=week&tz=180").json()
    assert data["period"] == "week"
    assert len(data["buckets"]) == 12
    assert data["window"]["audio_formats"] == [{"name": "mp3", "count": 1, "bytes": 42}]
    assert data["backfilling"] is False
    assert data["disk"]["total"] > 0
    assert data["disk"]["free"] >= 0


def test_stats_api_rejects_an_unknown_period():
    with TestClient(app_module.app) as c:
        assert c.get("/api/stats?period=decade").status_code == 400


def test_stats_reset_api_keeps_the_files():
    media = _write_media(Path(downloader.DOWNLOAD_DIR), "Keep.mp3")
    store.record_downloads([(stats.utc_hour(), _entry())])
    with TestClient(app_module.app) as c:
        assert c.post("/api/stats/reset").json() == {"ok": True}
    assert store.get_stats()["hours"] == {}
    assert media.exists()
