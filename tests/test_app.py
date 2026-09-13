"""Tests for app.py's helpers: path safety, cleanup, language resolution.

NOTE: the HTTP layer isn't exercised here - these cover the plain functions
where a mistake is silent and dangerous (serving a file outside the download
folder, deleting the wrong thing, losing a restored backup).
"""

import os

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from mediagrab import app as app_module
from mediagrab import downloader
from mediagrab import store


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


# --- _asset_version -----------------------------------------------------------


def test_asset_version_changes_when_the_file_is_touched(tmp_path, monkeypatch):
    # NOTE: this is the whole point of the cache-buster - a browser that
    # already cached an old app.js/style.css must see a new URL once the
    # file actually changes, or a shipped fix can look like it never landed.
    asset = tmp_path / "app.js"
    asset.write_text("first version", encoding="utf-8")
    monkeypatch.setattr(app_module, "STATIC_DIR", str(tmp_path))
    first = app_module._asset_version("app.js")

    os.utime(asset, (first + 10, first + 10))
    second = app_module._asset_version("app.js")

    assert second != first


def test_asset_version_of_a_missing_file_does_not_raise(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "STATIC_DIR", str(tmp_path))
    assert app_module._asset_version("does-not-exist.js") == 0


# --- _format_speed ----------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [(None, None), (0, None), (512, "512.0 B/s"), (1024, "1.0 KB/s"), (5 * 1024 * 1024, "5.0 MB/s")],
)
def test_format_speed(value, expected):
    assert app_module._format_speed(value) == expected


# --- _format_eta --------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        (-1, None),  # NOTE: yt-dlp can report a negative eta before it has enough data to estimate
        (0, "0:00"),
        (5, "0:05"),
        (75, "1:15"),
        (3661, "1:01:01"),
    ],
)
def test_format_eta(value, expected):
    assert app_module._format_eta(value) == expected


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


def test_unmerged_streams_are_removed_once_the_merge_landed(download_dir):
    """The reported case: 11 stream files left beside a finished episode."""
    # NOTE: yt-dlp names the pre-merge streams "<stem>.f<id>.<ext>" and deletes
    # them itself after ffmpeg merges. When the merge never runs they survive,
    # and they carry neither ".part" nor ".ytdl" - so nothing used to collect
    # them and they piled up, hundreds of MB at a time.
    folder = download_dir / "Kanal"
    folder.mkdir()
    for fmt in (616, 617, 251):
        (folder / f"Bolum.f{fmt}.mp4").write_bytes(b"stream")
    merged = folder / "Bolum.mp4"
    merged.write_bytes(b"finished")
    sidecar = folder / "Bolum.json"
    sidecar.write_text("{}", encoding="utf-8")

    app_module._sweep_orphaned_parts()

    assert merged.exists()
    assert sidecar.exists()
    assert sorted(p.name for p in folder.iterdir()) == ["Bolum.json", "Bolum.mp4"]


def test_unmerged_streams_survive_when_nothing_proves_them_stale(download_dir):
    # NOTE: with no merged output beside them these cannot be shown to be
    # debris, and they are the only copy of a download that did finish
    # fetching. Deleting on a guess would be worse than leaving them.
    folder = download_dir / "Kanal"
    folder.mkdir()
    (folder / "Bolum.f616.mp4").write_bytes(b"stream")
    (folder / "Bolum.f251.webm").write_bytes(b"stream")

    app_module._sweep_orphaned_parts()

    assert len(list(folder.iterdir())) == 2


def test_a_title_that_merely_looks_like_a_stream_is_left_alone(download_dir):
    # NOTE: a video actually called "Test.f616" produces "Test.f616.mp4",
    # which matches the stream pattern exactly. Its sidecars carry the same
    # infix, so no plain sibling exists - which is what saves it.
    folder = download_dir / "Kanal"
    folder.mkdir()
    (folder / "Test.f616.mp4").write_bytes(b"the user's video")
    (folder / "Test.f616.json").write_text("{}", encoding="utf-8")

    app_module._sweep_orphaned_parts()

    assert sorted(p.name for p in folder.iterdir()) == ["Test.f616.json", "Test.f616.mp4"]


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


def test_cancel_removes_a_stream_that_had_already_finished(download_dir):
    # NOTE: a stream that finished downloading has lost its ".part" suffix, so
    # the glob on tmpfilename never names it - it has to be derived. Cancelling
    # between "streams done" and "merge done" is exactly when this happens.
    tmp = download_dir / "v.f616.mp4.part"
    tmp.write_bytes(b"partial")
    finished_stream = download_dir / "v.f616.mp4"
    finished_stream.write_bytes(b"a whole video stream")
    unrelated = download_dir / "other.mp4"
    unrelated.write_bytes(b"keep me")

    job_id = "job-3"
    with app_module.jobs_lock:
        app_module.jobs[job_id] = app_module._new_job_record()
        app_module.jobs[job_id]["tmpfile"] = str(tmp)
    try:
        app_module._cleanup_partial_download(job_id)
    finally:
        with app_module.jobs_lock:
            app_module.jobs.pop(job_id, None)

    assert not finished_stream.exists()
    assert unrelated.exists()


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
    # mkv is the multi-audio-track output (see downloader.py's _video_opts) -
    # it shipped once already without this, making those files disappear.
    assert {"mp4", "mkv", "mp3", "m4a", "opus", "srt", "txt"} <= app_module.HISTORY_EXTS


def test_backups_and_partials_never_show_up_in_history():
    for junk in ("part", "ytdl", "mediagrab-bak", "webp"):
        assert junk not in app_module.HISTORY_EXTS


# --- _check_channel auto-download -------------------------------------------


class _FakeExecutor:
    """Captures submit() calls instead of actually running them."""

    def __init__(self):
        self.calls = []

    def submit(self, fn, *args):
        self.calls.append(args)


def test_auto_download_uses_the_saved_default_audio_lang(tmp_path, monkeypatch):
    # NOTE: this is the case the setting exists for - a channel with mode
    # "auto" downloads with no user interaction at all, so it's the ONE path
    # that can't rely on the chip UI pre-selecting anything. Without this
    # wiring the setting would silently do nothing for auto-downloaded videos.
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    store.save_settings(default_audio_lang="tr")

    monkeypatch.setattr(
        downloader,
        "check_channel_new_videos",
        lambda url, last_id, limit=15: [{"id": "abc123", "title": "Yeni Bolum", "url": "https://example.com/abc123"}],
    )
    monkeypatch.setattr(store, "update_channel", lambda *a, **k: None)
    fake_executor = _FakeExecutor()
    monkeypatch.setattr(app_module, "executor", fake_executor)

    channel = {
        "id": "chan1",
        "url": "https://example.com/channel",
        "name": "Test Kanali",
        "mode": "auto",
        "choice_kind": "video",
        "choice": "best",
        "last_video_id": None,
    }
    try:
        app_module._check_channel(channel)
        assert len(fake_executor.calls) == 1
        submitted_args = fake_executor.calls[0]
        assert submitted_args[-1] == ["tr"]  # audio_langs is the last positional argument, wrapped in a list
    finally:
        for call in fake_executor.calls:
            with app_module.jobs_lock:
                app_module.jobs.pop(call[0], None)


def test_auto_download_with_no_saved_default_behaves_as_before(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))

    monkeypatch.setattr(
        downloader,
        "check_channel_new_videos",
        lambda url, last_id, limit=15: [{"id": "abc123", "title": "Yeni Bolum", "url": "https://example.com/abc123"}],
    )
    monkeypatch.setattr(store, "update_channel", lambda *a, **k: None)
    fake_executor = _FakeExecutor()
    monkeypatch.setattr(app_module, "executor", fake_executor)

    channel = {
        "id": "chan1",
        "url": "https://example.com/channel",
        "name": "Test Kanali",
        "mode": "auto",
        "choice_kind": "video",
        "choice": "best",
        "last_video_id": None,
    }
    try:
        app_module._check_channel(channel)
        assert fake_executor.calls[0][-1] == []
    finally:
        for call in fake_executor.calls:
            with app_module.jobs_lock:
                app_module.jobs.pop(call[0], None)


# --- _delayed_restart ---------------------------------------------------------


def test_restart_prefers_the_original_command_line(monkeypatch):
    # NOTE: regression test - reproduced live. Launched as
    # `python -m uvicorn mediagrab.app:app ...`, the old code
    # (os.execv(sys.executable, [sys.executable] + sys.argv)) re-executed
    # uvicorn's own __main__.py directly instead of through "-m", which
    # changes sys.path[0] to uvicorn's OWN package directory - letting its
    # uvicorn/logging.py shadow the stdlib `logging` module and crashing the
    # restarted process with "module 'logging' has no attribute 'Formatter'".
    # sys.orig_argv preserves the exact original invocation (including "-m")
    # and must be used whenever it's available.
    calls = []
    monkeypatch.setattr(app_module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(app_module.os, "execv", lambda exe, argv: calls.append((exe, argv)))
    original = ["/usr/bin/python", "-m", "uvicorn", "mediagrab.app:app", "--port", "8420"]
    monkeypatch.setattr(app_module.sys, "orig_argv", original, raising=False)

    app_module._delayed_restart()

    assert calls == [(app_module.sys.executable, original)]


def test_restart_falls_back_to_argv_when_orig_argv_is_unavailable(monkeypatch):
    # NOTE: sys.orig_argv only exists on Python 3.10+ - older interpreters
    # keep the previous behaviour, which is correct for the primary
    # `python run.py` flow (no third-party package sits next to run.py to
    # collide with).
    calls = []
    monkeypatch.setattr(app_module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(app_module.os, "execv", lambda exe, argv: calls.append((exe, argv)))
    monkeypatch.delattr(app_module.sys, "orig_argv", raising=False)
    monkeypatch.setattr(app_module.sys, "argv", ["run.py"])

    app_module._delayed_restart()

    assert calls == [(app_module.sys.executable, [app_module.sys.executable, "run.py"])]


# --- local vs. remote client detection, and "download to this device" ------


@pytest.fixture
def client_settings(tmp_path, monkeypatch):
    # NOTE: isolates settings.json/channels.json so these TestClient-driven
    # tests can't touch (or be confused by) whatever's really on disk.
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setattr(store, "STORE_PATH", str(tmp_path / "channels.json"))
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: None)


def test_client_info_reports_local_for_loopback(client_settings):
    with TestClient(app_module.app, client=("127.0.0.1", 12345)) as c:
        assert c.get("/api/client-info").json() == {"is_local": True}


def test_client_info_reports_ipv6_loopback_as_local(client_settings):
    with TestClient(app_module.app, client=("::1", 12345)) as c:
        assert c.get("/api/client-info").json() == {"is_local": True}


def test_client_info_reports_a_lan_address_as_not_local(client_settings):
    with TestClient(app_module.app, client=("192.168.1.50", 12345)) as c:
        assert c.get("/api/client-info").json() == {"is_local": False}


def test_the_download_route_is_tried_before_the_greedy_reveal_route(download_dir, client_settings, monkeypatch):
    # NOTE: regression test, reproduced directly. `{filename:path}` matches
    # slashes, so ".../file/{filename:path}" is greedy enough to ALSO match
    # a URL ending in the literal segment "/download" (capturing it as part
    # of `filename`) if that route is registered first. FastAPI/Starlette
    # tries routes in registration order, so the more specific
    # ".../file/{filename:path}/download" route MUST be declared first in
    # app.py - this proves it still is, independent of reading the source.
    folder = download_dir / "Kanal Adi"
    folder.mkdir()
    media = folder / "Video.mp4"
    media.write_bytes(b"fake video bytes")

    reveal_calls = []
    monkeypatch.setattr(app_module.downloader, "reveal_in_explorer", lambda path: reveal_calls.append(path))

    with TestClient(app_module.app) as c:
        download_res = c.get("/api/history/file/Kanal Adi/Video.mp4/download")
        assert download_res.status_code == 200
        assert download_res.content == b"fake video bytes"
        assert not reveal_calls, "the /download URL must never reach the reveal-in-explorer handler"

        reveal_res = c.get("/api/history/file/Kanal Adi/Video.mp4")
        assert reveal_res.status_code == 200
        assert reveal_res.json() == {"ok": True}
        assert reveal_calls == [str(media)]


def test_history_download_sets_content_disposition_attachment(download_dir, client_settings):
    folder = download_dir / "Kanal Adi"
    folder.mkdir()
    media = folder / "Video.mp4"
    media.write_bytes(b"fake video bytes")

    with TestClient(app_module.app) as c:
        res = c.get("/api/history/file/Kanal Adi/Video.mp4/download")
    assert res.status_code == 200
    assert 'attachment; filename="Video.mp4"' in res.headers["content-disposition"]
    assert res.content == b"fake video bytes"


def test_job_download_sets_content_disposition_attachment(download_dir, client_settings):
    media = download_dir / "Video.mp4"
    media.write_bytes(b"fake video bytes")
    job_id = "test-download-job"
    with app_module.jobs_lock:
        app_module.jobs[job_id] = {"state": "bitti", "ready": True, "filepath": str(media)}
    try:
        with TestClient(app_module.app) as c:
            res = c.get(f"/api/file/{job_id}/download")
        assert res.status_code == 200
        assert 'attachment; filename="Video.mp4"' in res.headers["content-disposition"]
        assert res.content == b"fake video bytes"
    finally:
        with app_module.jobs_lock:
            app_module.jobs.pop(job_id, None)


def test_job_download_404s_before_the_job_is_ready(client_settings):
    job_id = "test-not-ready-job"
    with app_module.jobs_lock:
        app_module.jobs[job_id] = {"state": "indiriliyor", "ready": False}
    try:
        with TestClient(app_module.app) as c:
            res = c.get(f"/api/file/{job_id}/download")
        assert res.status_code == 404
    finally:
        with app_module.jobs_lock:
            app_module.jobs.pop(job_id, None)


# --- keep vs. relay: deleting a remote device's file after it's fully sent ---


def test_relay_delete_background_is_none_for_local_requests_regardless_of_mode(client_settings):
    store.save_settings(remote_download_mode="relay")
    assert app_module._relay_delete_background("C:/whatever.mp4", is_local=True) is None


def test_relay_delete_background_is_none_in_keep_mode_regardless_of_locality(client_settings):
    # NOTE: "keep" is also the default, so this doubles as "a fresh install
    # with no settings.json at all never auto-deletes anything".
    assert store.get_settings()["remote_download_mode"] == "keep"
    assert app_module._relay_delete_background("C:/whatever.mp4", is_local=False) is None


def test_relay_delete_background_returns_a_task_only_for_a_remote_relay_download(client_settings):
    store.save_settings(remote_download_mode="relay")
    background = app_module._relay_delete_background("C:/whatever.mp4", is_local=False)
    assert isinstance(background, app_module.BackgroundTask)


def test_a_remote_relay_download_deletes_the_file_after_it_is_fully_sent(download_dir, client_settings):
    store.save_settings(remote_download_mode="relay")
    media = download_dir / "Video.mp4"
    media.write_bytes(b"fake video bytes")

    with TestClient(app_module.app, client=("192.168.1.50", 12345)) as c:
        res = c.get("/api/history/file/Video.mp4/download")
    assert res.status_code == 200
    assert res.content == b"fake video bytes"
    assert not media.exists(), "relay mode must delete the host's copy once a remote device has it"


def test_a_remote_keep_download_never_deletes_the_file(download_dir, client_settings):
    media = download_dir / "Video.mp4"
    media.write_bytes(b"fake video bytes")

    with TestClient(app_module.app, client=("192.168.1.50", 12345)) as c:
        res = c.get("/api/history/file/Video.mp4/download")
    assert res.status_code == 200
    assert media.exists(), "keep mode must never delete anything, regardless of who downloads it"


def test_a_local_relay_download_never_deletes_the_file(download_dir, client_settings):
    # NOTE: relay mode only ever applies to a REMOTE device's transfer - the
    # host's own "reveal/download" of its own file is never the thing being
    # relayed anywhere, so there is no second copy to justify deleting this one.
    store.save_settings(remote_download_mode="relay")
    media = download_dir / "Video.mp4"
    media.write_bytes(b"fake video bytes")

    with TestClient(app_module.app, client=("127.0.0.1", 12345)) as c:
        res = c.get("/api/history/file/Video.mp4/download")
    assert res.status_code == 200
    assert media.exists(), "the host's own download must never be auto-deleted"


def test_a_remote_relay_job_download_deletes_the_file_after_it_is_fully_sent(download_dir, client_settings):
    store.save_settings(remote_download_mode="relay")
    media = download_dir / "Video.mp4"
    media.write_bytes(b"fake video bytes")
    job_id = "test-relay-job"
    with app_module.jobs_lock:
        app_module.jobs[job_id] = {"state": "bitti", "ready": True, "filepath": str(media)}
    try:
        with TestClient(app_module.app, client=("192.168.1.50", 12345)) as c:
            res = c.get(f"/api/file/{job_id}/download")
        assert res.status_code == 200
        assert not media.exists()
    finally:
        with app_module.jobs_lock:
            app_module.jobs.pop(job_id, None)
