"""Tests for app.py's helpers: path safety, cleanup, language resolution.

NOTE: the HTTP layer isn't exercised here - these cover the plain functions
where a mistake is silent and dangerous (serving a file outside the download
folder, deleting the wrong thing, losing a restored backup).
"""

import os

import pytest
from fastapi import HTTPException

from mediagrab import app as app_module
from mediagrab import downloader


@pytest.fixture
def download_dir(tmp_path, monkeypatch):
    """Point DOWNLOAD_DIR at a throwaway folder for the whole test."""
    monkeypatch.setattr(downloader, "DOWNLOAD_DIR", str(tmp_path))
    return tmp_path


# --- _history_path (path traversal) -----------------------------------------


def test_serves_a_file_inside_the_download_folder(download_dir):
    (download_dir / "Kanal").mkdir()
    media = download_dir / "Kanal" / "v.mp4"
    media.write_bytes(b"x")
    assert app_module._history_path("Kanal/v.mp4") == str(media)


@pytest.mark.parametrize(
    "attack",
    [
        "../secret.txt",
        "../../secret.txt",
        "Kanal/../../secret.txt",
        "./../secret.txt",
    ],
)
def test_refuses_to_escape_the_download_folder(download_dir, attack):
    # NOTE: this guard is the only thing standing between a path in a URL and
    # arbitrary files on disk, so it gets explicit coverage.
    (download_dir.parent / "secret.txt").write_text("do not serve me", encoding="utf-8")
    with pytest.raises(HTTPException) as excinfo:
        app_module._history_path(attack)
    assert excinfo.value.status_code == 404


def test_missing_file_is_a_404(download_dir):
    with pytest.raises(HTTPException):
        app_module._history_path("nope.mp4")


def test_directory_is_not_servable(download_dir):
    (download_dir / "Kanal").mkdir()
    with pytest.raises(HTTPException):
        app_module._history_path("Kanal")


# --- _url_path_quote --------------------------------------------------------


def test_slashes_stay_separators_but_the_rest_is_escaped():
    # NOTE: quoting the whole string would turn "/" into %2F and stop the
    # {filename:path} route from matching.
    assert app_module._url_path_quote("Kanal Adi/Video #1.mp4") == "Kanal%20Adi/Video%20%231.mp4"


# --- _format_speed ----------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [(None, None), (0, None), (512, "512.0 B/s"), (1024, "1.0 KB/s"), (5 * 1024 * 1024, "5.0 MB/s")],
)
def test_format_speed(value, expected):
    assert app_module._format_speed(value) == expected


# --- _guess_image_mime ------------------------------------------------------


@pytest.mark.parametrize(
    "magic,expected",
    [
        (b"\xff\xd8\xff\xe0", "image/jpeg"),
        (b"\x89PNG\r\n\x1a\n", "image/png"),
        (b"GIF89a...", "image/gif"),
        (b"unknown-bytes", "image/jpeg"),
    ],
)
def test_guess_image_mime(magic, expected):
    assert app_module._guess_image_mime(magic) == expected


# --- _resolve_lang ----------------------------------------------------------


class _FakeRequest:
    def __init__(self, cookies=None):
        self.cookies = cookies or {}


def test_query_parameter_wins_over_cookie():
    assert app_module._resolve_lang("en", _FakeRequest({app_module.LANG_COOKIE: "tr"})) == "en"


def test_cookie_is_used_when_there_is_no_query_parameter():
    # NOTE: this is what makes a bare bookmark/PWA launch render in the right
    # language on the FIRST paint instead of flashing the wrong one.
    assert app_module._resolve_lang(None, _FakeRequest({app_module.LANG_COOKIE: "en"})) == "en"


def test_invalid_values_fall_through_to_system_detection():
    result = app_module._resolve_lang("klingon", _FakeRequest({app_module.LANG_COOKIE: "klingon"}))
    assert result in ("tr", "en")


# --- _sweep_orphaned_parts --------------------------------------------------


def test_partial_downloads_are_removed_at_startup(download_dir, capsys):
    (download_dir / "Kanal").mkdir()
    (download_dir / "Kanal" / "v.mp4.part").write_bytes(b"junk")
    (download_dir / "Kanal" / "v.mp4.part-Frag12").write_bytes(b"junk")
    (download_dir / "Kanal" / "v.mp4.ytdl").write_text("{}", encoding="utf-8")
    keep = download_dir / "Kanal" / "v.mp4"
    keep.write_bytes(b"finished")

    app_module._sweep_orphaned_parts()

    assert keep.exists()
    assert sorted(p.name for p in (download_dir / "Kanal").iterdir()) == ["v.mp4"]


def test_orphaned_backup_is_restored(download_dir):
    # NOTE: the process died before downloader could put the file back itself.
    # The backup IS the user's file, so it has to come home.
    backup = download_dir / ("v.mp4" + downloader.BACKUP_SUFFIX)
    backup.write_bytes(b"the user's original")

    app_module._sweep_orphaned_parts()

    restored = download_dir / "v.mp4"
    assert restored.read_bytes() == b"the user's original"
    assert not backup.exists()


def test_redundant_backup_is_discarded(download_dir):
    # NOTE: the download DID finish - only the cleanup was missed - so the
    # backup must not clobber the newer file.
    real = download_dir / "v.mp4"
    real.write_bytes(b"new download")
    backup = download_dir / ("v.mp4" + downloader.BACKUP_SUFFIX)
    backup.write_bytes(b"stale backup")

    app_module._sweep_orphaned_parts()

    assert real.read_bytes() == b"new download"
    assert not backup.exists()


def test_sweep_leaves_normal_files_alone(download_dir):
    for name in ("a.mp4", "b.mp3", "c.tr.srt", "d.json", "e.webp"):
        (download_dir / name).write_bytes(b"x")

    app_module._sweep_orphaned_parts()

    assert len(list(download_dir.iterdir())) == 5


# --- _cleanup_partial_download ----------------------------------------------


def test_cancel_cleans_fragments_but_not_the_finished_file(download_dir):
    tmp = download_dir / "v.mp4.part"
    tmp.write_bytes(b"partial")
    (download_dir / "v.mp4.part-Frag3").write_bytes(b"partial")
    (download_dir / "v.mp4.part-Frag4.part").write_bytes(b"partial")
    (download_dir / "v.mp4.ytdl").write_text("{}", encoding="utf-8")
    unrelated = download_dir / "other.mp4"
    unrelated.write_bytes(b"keep me")

    job_id = "job-1"
    with app_module.jobs_lock:
        app_module.jobs[job_id] = app_module._new_job_record()
        app_module.jobs[job_id]["tmpfile"] = str(tmp)
    try:
        app_module._cleanup_partial_download(job_id)
    finally:
        with app_module.jobs_lock:
            app_module.jobs.pop(job_id, None)

    assert unrelated.exists()
    assert sorted(p.name for p in download_dir.iterdir()) == ["other.mp4"]


def test_cleanup_without_a_recorded_tmpfile_does_nothing(download_dir):
    (download_dir / "v.mp4").write_bytes(b"x")
    job_id = "job-2"
    with app_module.jobs_lock:
        app_module.jobs[job_id] = app_module._new_job_record()
    try:
        app_module._cleanup_partial_download(job_id)
    finally:
        with app_module.jobs_lock:
            app_module.jobs.pop(job_id, None)
    assert (download_dir / "v.mp4").exists()


# --- history extensions -----------------------------------------------------


def test_transcripts_and_subtitles_show_up_in_history():
    # NOTE: guards against a new download kind being added without its
    # extension being registered, which would make it invisible in the UI.
    assert {"mp4", "mp3", "m4a", "opus", "srt", "txt"} <= app_module.HISTORY_EXTS


def test_backups_and_partials_never_show_up_in_history():
    for junk in ("part", "ytdl", "mediagrab-bak", "webp"):
        assert junk not in app_module.HISTORY_EXTS
