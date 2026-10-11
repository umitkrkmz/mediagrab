"""Tests for the pure logic in downloader.py.

NOTE: nothing here touches the network or spawns yt-dlp - these cover the
parsing and file-shuffling code where the real bugs have actually been, so
the suite stays fast and runs offline. The one exception to "no ffmpeg" is
test_stream_info_reads_a_real_file (a 1-second local clip, skipped when
ffmpeg isn't installed).
"""

import os
import re
import shutil
import subprocess
from types import SimpleNamespace

import pytest

from mediagrab import downloader


# --- strip_ansi_codes -------------------------------------------------------


def test_strips_ytdlp_colour_codes():
    # NOTE: yt-dlp colours its own errors; shown raw in the UI those escape
    # sequences looked like garbled text.
    raw = "\x1b[0;31mERROR:\x1b[0m unable to download video data"
    assert downloader.strip_ansi_codes(raw) == "ERROR: unable to download video data"


def test_leaves_plain_text_alone():
    assert downloader.strip_ansi_codes("plain error") == "plain error"


# --- human_size -------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [(None, "?"), (0, "?"), (512, "512 B"), (1024, "1 KB"), (1536 * 1024, "2 MB")],
)
def test_human_size(value, expected):
    assert downloader.human_size(value) == expected


# --- _dedupe_video_formats --------------------------------------------------


def test_keeps_only_highest_bitrate_per_height():
    formats = [
        {"format_id": "a", "height": 720, "tbr": 500, "vcodec": "avc1.4d401f", "ext": "mp4"},
        {"format_id": "b", "height": 720, "tbr": 900, "vcodec": "avc1.4d401f", "ext": "mp4"},
        {"format_id": "c", "height": 360, "tbr": 200, "vcodec": "vp9", "ext": "webm"},
    ]
    result = downloader._dedupe_video_formats(formats)
    assert [f["format_id"] for f in result] == ["b", "c"]
    assert [f["label"] for f in result] == ["720p", "360p"]


def test_audio_only_formats_are_excluded():
    formats = [
        {"format_id": "audio", "height": None, "tbr": 128, "vcodec": "none", "ext": "m4a"},
        {"format_id": "video", "height": 480, "tbr": 700, "vcodec": "vp9", "ext": "webm"},
    ]
    assert [f["format_id"] for f in downloader._dedupe_video_formats(formats)] == ["video"]


def test_unset_vcodec_still_counts_as_video():
    # NOTE: regression guard. Only the explicit "none" marker means "no video
    # track" - plenty of non-YouTube extractors (archive.org) just leave vcodec
    # unset on real video formats, and treating that as audio-only hid every
    # quality option on those sites.
    formats = [{"format_id": "x", "height": 480, "tbr": 700, "vcodec": None, "ext": "mp4"}]
    result = downloader._dedupe_video_formats(formats)
    assert len(result) == 1
    assert result[0]["vcodec"] == "?"


def test_size_is_estimated_from_bitrate_when_filesize_is_missing():
    # NOTE: real numbers from an actual 1080p YouTube DASH stream that reports
    # neither filesize nor filesize_approx at all - tbr is all there is.
    formats = [{"format_id": "x", "height": 1080, "tbr": 6463.92, "vcodec": "vp09", "ext": "mp4"}]
    result = downloader._dedupe_video_formats(formats, duration=2398)
    estimate = 6463.92 * 1000 / 8 * 2398
    expected = downloader.human_size(estimate)
    assert result[0]["size"] == f"~{expected}"
    # NOTE: the raw byte count behind the label above - app.py's disk-space
    # check (see /api/download) needs this as a number, not a "~512 MB" string.
    assert result[0]["size_bytes"] == int(estimate)


def test_a_real_filesize_is_shown_without_the_estimate_prefix():
    # NOTE: when yt-dlp DOES report a real filesize, it must win outright -
    # never overwritten by a guess, and never carry the "~" that would wrongly
    # imply it's not a reported fact.
    formats = [{"format_id": "x", "height": 720, "tbr": 900, "filesize": 50_000_000, "vcodec": "avc1", "ext": "mp4"}]
    result = downloader._dedupe_video_formats(formats, duration=600)
    assert result[0]["size"] == downloader.human_size(50_000_000)
    assert "~" not in result[0]["size"]
    assert result[0]["size_bytes"] == 50_000_000


def test_size_is_unknown_without_enough_data_to_estimate():
    no_tbr = [{"format_id": "x", "height": 480, "vcodec": "vp9", "ext": "webm"}]
    result_no_tbr = downloader._dedupe_video_formats(no_tbr, duration=600)
    assert result_no_tbr[0]["size"] == "?"
    assert result_no_tbr[0]["size_bytes"] is None

    no_duration = [{"format_id": "y", "height": 480, "tbr": 700, "vcodec": "vp9", "ext": "webm"}]
    result_no_duration = downloader._dedupe_video_formats(no_duration, duration=0)
    assert result_no_duration[0]["size"] == "?"
    assert result_no_duration[0]["size_bytes"] is None


def test_a_wildly_inflated_tbr_is_capped_by_a_same_height_sibling():
    # NOTE: real case, from an actual video - the format with no confirmed
    # filesize (the one _dedupe_video_formats picks, since it wins on raw tbr)
    # reported a tbr ~3x every OTHER 1080p format's, despite same codec family
    # and framerate. Uncapped, its estimate came out bigger than the video's
    # ENTIRE downloaded file (video+audio+thumbnail) - a logical impossibility
    # that's what this guards against.
    formats = [
        # wins the height slot on tbr, but has no confirmed size of its own
        {"format_id": "617", "height": 1080, "tbr": 8467.119, "vcodec": "vp09", "ext": "mp4"},
        # a real sibling at the same height whose filesize IS confirmed
        {"format_id": "299", "height": 1080, "tbr": 3969.469, "vcodec": "avc1",
         "ext": "mp4", "filesize": 1_189_581_036},
    ]
    result = downloader._dedupe_video_formats(formats, duration=2398)
    assert result[0]["format_id"] == "617"  # selection itself is unchanged
    # NOTE: capped at the sibling's real size, not the raw (much bigger) tbr
    # estimate - human_size(1_189_581_036) is "1135 MB" / "1 GB" territory,
    # nowhere near the ~2.4 GB the uncapped formula would have produced.
    assert result[0]["size"] == f"~{downloader.human_size(1_189_581_036)}"


def test_the_cap_never_makes_the_estimate_bigger():
    # NOTE: the cap is a ceiling, not a floor - if the raw tbr estimate is
    # already smaller than the biggest confirmed sibling, leave it alone.
    formats = [
        {"format_id": "x", "height": 480, "tbr": 100, "vcodec": "vp9", "ext": "webm"},
        {"format_id": "y", "height": 480, "tbr": 90, "vcodec": "avc1", "ext": "mp4", "filesize": 999_999_999_999},
    ]
    result = downloader._dedupe_video_formats(formats, duration=600)
    uncapped = 100 * 1000 / 8 * 600
    assert result[0]["size"] == f"~{downloader.human_size(uncapped)}"


def test_no_cap_applies_when_no_sibling_has_a_confirmed_size():
    # NOTE: regression guard - a video where NOTHING at that height has a
    # real filesize must fall back to the plain, uncapped tbr estimate
    # exactly as before this fix, not silently disappear.
    formats = [{"format_id": "x", "height": 1080, "tbr": 8467.119, "vcodec": "vp09", "ext": "mp4"}]
    result = downloader._dedupe_video_formats(formats, duration=2398)
    uncapped = 8467.119 * 1000 / 8 * 2398
    assert result[0]["size"] == f"~{downloader.human_size(uncapped)}"


# --- _audio_track_list -------------------------------------------------------


def test_no_chips_when_there_is_only_one_audio_language():
    # NOTE: this is the common case (almost every video) - no point showing a
    # single-option chip row.
    formats = [{"vcodec": "none", "language": "en", "language_preference": 10}]
    assert downloader._audio_track_list(formats) == []


def test_original_track_is_flagged_by_the_highest_language_preference():
    # NOTE: mirrors a real 18-language video - yt-dlp marked the original
    # English track pref=10 and every dub -1.
    formats = [
        {"vcodec": "none", "language": "en", "language_preference": 10},
        {"vcodec": "none", "language": "tr", "language_preference": -1},
        {"vcodec": "none", "language": "de", "language_preference": -1},
    ]
    assert downloader._audio_track_list(formats) == [
        {"code": "de", "is_default": False},
        {"code": "en", "is_default": True},
        {"code": "tr", "is_default": False},
    ]


def test_video_formats_and_storyboards_are_not_languages():
    formats = [
        {"vcodec": "avc1", "acodec": "none", "language": "en"},
        {"vcodec": "none", "format_note": "storyboard", "language": "en"},
        {"vcodec": "none", "language": "en", "language_preference": 10},
        {"vcodec": "none", "language": "tr", "language_preference": -1},
    ]
    assert downloader._audio_track_list(formats) == [
        {"code": "en", "is_default": True},
        {"code": "tr", "is_default": False},
    ]


def test_formats_without_a_language_tag_are_ignored():
    formats = [
        {"vcodec": "none", "language": None},
        {"vcodec": "none", "language": "en", "language_preference": 10},
        {"vcodec": "none", "language": "tr", "language_preference": -1},
    ]
    assert downloader._audio_track_list(formats) == [
        {"code": "en", "is_default": True},
        {"code": "tr", "is_default": False},
    ]


# --- audio_lang wired into the format selector -------------------------------


@pytest.mark.parametrize("choice", ["opus", "m4a", "mp3"])
def test_no_audio_lang_leaves_the_selector_untouched(choice):
    # NOTE: byte-for-byte the same string as before this feature existed -
    # the regression guard for "no dub requested, nothing should change".
    with_lang_support = downloader._audio_opts(choice, audio_lang="")
    assert with_lang_support["format"] == downloader._audio_opts(choice)["format"]


@pytest.mark.parametrize("choice", ["opus", "m4a", "mp3"])
def test_audio_lang_is_tried_before_falling_back(choice):
    opts = downloader._audio_opts(choice, audio_lang="tr")
    fmt = opts["format"]
    assert "[language=tr]" in fmt
    # NOTE: the original, language-agnostic chain must still be there at the
    # end - an unavailable dub should degrade to "best audio", not fail.
    assert fmt.endswith(downloader._audio_opts(choice)["format"])


def test_video_opts_without_audio_langs_is_unchanged():
    assert downloader._video_opts("617")["format"] == downloader._video_opts("617", audio_langs=[])["format"]
    assert downloader._video_opts("617")["format"] == "617+bestaudio/best"
    assert downloader._video_opts("617")["merge_output_format"] == "mp4"
    assert "allow_multiple_audio_streams" not in downloader._video_opts("617")


def test_video_opts_with_one_audio_lang_falls_back_to_default_audio():
    opts = downloader._video_opts("617", audio_langs=["tr"])
    assert opts["format"] == "617+bestaudio[language=tr]/bestaudio/best"
    # NOTE: a single language is exactly the pre-multi-track behaviour - still
    # mp4, still no multistreams flag.
    assert opts["merge_output_format"] == "mp4"
    assert "allow_multiple_audio_streams" not in opts


def test_video_opts_best_sentinel_also_respects_audio_langs():
    fmt = downloader._video_opts("best", audio_langs=["tr"])["format"]
    assert fmt == "bestvideo+bestaudio[language=tr]/bestaudio/best"


def test_the_final_fallback_never_settles_for_a_silent_video():
    # NOTE: regression guard for a real bug - the fallback used to be the
    # bare format id ("617"), which ALWAYS resolves (it matches itself) even
    # when every "+bestaudio" alternative failed to find an audio stream to
    # merge with, so a transient audio-format hiccup between probe() and
    # download() (each re-extracts formats independently) could silently
    # ship a picture with no sound. Every alternative in the chain must
    # require an audio track - none may be the bare video-only format id on
    # its own.
    for audio_langs in (None, ["tr"], ["tr", ""]):
        fmt = downloader._video_opts("617", audio_langs=audio_langs)["format"]
        alternatives = fmt.split("/")
        assert "617" not in alternatives, f"a silent-video alternative slipped back in: {fmt!r}"
        assert alternatives[-1] == "best", f"must end in a fallback that still requires audio: {fmt!r}"


# --- multiple audio tracks in one file ---------------------------------------


def test_two_audio_langs_chains_both_into_one_selector():
    opts = downloader._video_opts("617", audio_langs=["tr", "en"])
    assert opts["format"] == "617+bestaudio[language=tr]+bestaudio[language=en]/617+bestaudio"


def test_two_audio_langs_switches_the_container_to_mkv():
    # NOTE: mp4 CAN hold multiple audio tracks, but mkv is what multi-dub
    # releases and players actually expect - and this must never leak into
    # the single-track path (asserted separately above).
    assert downloader._video_opts("617", audio_langs=["tr", "en"])["merge_output_format"] == "mkv"


def test_two_audio_langs_turns_on_multistreams():
    # NOTE: yt-dlp collapses a "+"-joined multi-audio selector down to one
    # stream unless this is explicitly set - confirmed against a real
    # download: without it, only one of the two requested tracks survived.
    assert downloader._video_opts("617", audio_langs=["tr", "en"])["allow_multiple_audio_streams"] is True


def test_a_blank_entry_does_not_count_toward_multi_track():
    # NOTE: defensive - the UI should never send an empty string in the list,
    # but if it did, this must not accidentally trip the two-or-more path.
    opts = downloader._video_opts("617", audio_langs=["tr", ""])
    assert opts["format"] == "617+bestaudio[language=tr]/bestaudio/best"
    assert opts["merge_output_format"] == "mp4"


def test_three_audio_langs_chains_all_three():
    fmt = downloader._video_opts("617", audio_langs=["tr", "en", "de"])["format"]
    assert fmt == "617+bestaudio[language=tr]+bestaudio[language=en]+bestaudio[language=de]/617+bestaudio"


# --- _subtitle_list / _transcript_language ----------------------------------


def test_manual_subtitles_are_listed_alphabetically():
    info = {"subtitles": {"tr": [{}], "en": [{}]}, "automatic_captions": {"de": [{}]}}
    assert downloader._subtitle_list(info) == [
        {"code": "en", "source": "manual"},
        {"code": "tr", "source": "manual"},
    ]


def test_falls_back_to_one_auto_caption_when_no_manual_subtitles():
    # NOTE: only ONE auto caption is offered - automatic_captions carries the
    # whole machine-translated language list, which would bloat the UI.
    info = {"subtitles": {}, "automatic_captions": {"tr": [{}], "en": [{}]}, "language": "tr"}
    assert downloader._subtitle_list(info) == [{"code": "tr", "source": "auto"}]


def test_no_subtitles_at_all():
    assert downloader._subtitle_list({}) == []
    assert downloader._transcript_language({}) is None


def test_transcript_prefers_manual_over_auto():
    info = {"subtitles": {"en": [{}]}, "automatic_captions": {"en": [{}]}, "language": "en"}
    assert downloader._transcript_language(info) == {"code": "en", "source": "manual"}


def test_transcript_uses_auto_when_that_is_all_there_is():
    info = {"subtitles": {}, "automatic_captions": {"tr": [{}]}, "language": "tr"}
    assert downloader._transcript_language(info) == {"code": "tr", "source": "auto"}


# --- _vtt_to_text -----------------------------------------------------------

# NOTE: this is the shape YouTube's auto-generated ("rolling") captions really
# have - each cue repeats the previous line, then a near-zero-duration
# transition cue repeats the new line on its own. A cue-level de-dupe pass
# produced roughly double the text; the fix works line-by-line instead.
ROLLING_VTT = """WEBVTT
Kind: captions
Language: tr

00:00:04.160 --> 00:00:07.110
Gunaydin herkese

00:00:07.110 --> 00:00:07.120
Gunaydin herkese

00:00:07.120 --> 00:00:09.790
Gunaydin herkese
bugun vlog cekiyorum

00:00:09.790 --> 00:00:09.800
bugun vlog cekiyorum

00:00:09.800 --> 00:00:11.470
bugun vlog cekiyorum
hazir misiniz
"""


def _write(tmp_path, text):
    path = tmp_path / "sub.vtt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_rolling_captions_are_not_duplicated(tmp_path):
    text = downloader._vtt_to_text(_write(tmp_path, ROLLING_VTT))
    assert text == "Gunaydin herkese bugun vlog cekiyorum hazir misiniz"


def test_timestamped_output_keeps_each_line_once(tmp_path):
    text = downloader._vtt_to_text(_write(tmp_path, ROLLING_VTT), timestamps=True)
    assert text.splitlines() == [
        "[00:00:04] Gunaydin herkese",
        "[00:00:07] bugun vlog cekiyorum",
        "[00:00:09] hazir misiniz",
    ]


def test_word_level_timing_tags_are_stripped(tmp_path):
    vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n<00:00:01.500><c>merhaba</c> dunya\n"
    assert downloader._vtt_to_text(_write(tmp_path, vtt)) == "merhaba dunya"


def test_headers_and_cue_numbers_are_skipped(tmp_path):
    vtt = "WEBVTT\nKind: captions\nNOTE something\n\n1\n00:00:01.000 --> 00:00:02.000\nsadece bu\n"
    assert downloader._vtt_to_text(_write(tmp_path, vtt)) == "sadece bu"


# --- audio options ----------------------------------------------------------


@pytest.mark.parametrize("choice", ["opus", "m4a", "mp3"])
def test_every_audio_format_embeds_a_cover(choice):
    # NOTE: the cover is what the history grid shows as a thumbnail, so losing
    # it would quietly turn every audio download into a placeholder icon.
    opts = downloader._audio_opts(choice)
    keys = [p["key"] for p in opts["postprocessors"]]
    assert "EmbedThumbnail" in keys
    assert opts["writethumbnail"] is True


@pytest.mark.parametrize("choice", ["opus", "m4a", "mp3"])
def test_metadata_is_written_after_the_container_is_settled(choice):
    # NOTE: order matters - EmbedThumbnail must run after the remux/extract
    # step, otherwise it hits an unsupported container like webm.
    keys = [p["key"] for p in downloader._audio_opts(choice)["postprocessors"]]
    converter = next(i for i, k in enumerate(keys) if k.startswith("FFmpeg") and k != "FFmpegMetadata")
    assert converter < keys.index("EmbedThumbnail")


def test_unknown_audio_choice_is_rejected():
    with pytest.raises(downloader.ProbeError):
        downloader._audio_opts("flac")


# --- _parse_version ---------------------------------------------------------


def test_zero_padded_and_normalised_versions_compare_equal():
    # NOTE: yt-dlp ships "2026.07.04" while PyPI normalises it to "2026.7.4".
    # Compared as plain strings those look different and every up-to-date
    # install was reported as outdated.
    assert downloader._parse_version("2026.07.04") == downloader._parse_version("2026.7.4")


def test_newer_version_sorts_above_older():
    assert downloader._parse_version("2026.8.19") > downloader._parse_version("2026.7.4")


def test_unparseable_version_is_not_treated_as_newer():
    assert downloader._parse_version("not-a-version") == ()


# --- _normalize_channel_url -------------------------------------------------


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://youtube.com/@TED", "https://youtube.com/@TED/videos"),
        ("https://youtube.com/@TED/", "https://youtube.com/@TED/videos"),
        ("https://youtube.com/@TED/videos", "https://youtube.com/@TED/videos"),
        ("https://youtube.com/@TED/streams", "https://youtube.com/@TED/streams"),
    ],
)
def test_channel_url_points_at_the_uploads_feed(url, expected):
    assert downloader._normalize_channel_url(url) == expected


# --- metadata_sidecar_path --------------------------------------------------


def test_sidecar_sits_next_to_the_media_file():
    assert downloader.metadata_sidecar_path(os.path.join("a", "b", "v.mp4")) == os.path.join("a", "b", "v.json")


# --- backup / restore -------------------------------------------------------


class _FakeYdl:
    """Minimal stand-in for YoutubeDL: just resolves a filename."""

    def __init__(self, filename, info=None):
        self._filename = filename
        self._info = info if info is not None else {"title": "x"}

    def extract_info(self, url, download=False):
        return self._info

    def prepare_filename(self, info):
        return self._filename


def test_existing_outputs_are_moved_aside_and_restored(tmp_path):
    stem = tmp_path / "Video"
    media = stem.with_suffix(".mp4")
    sidecar = stem.with_suffix(".json")
    media.write_bytes(b"original media")
    sidecar.write_text("{}", encoding="utf-8")

    ydl = _FakeYdl(str(media))
    backups = downloader._backup_existing_outputs(ydl, "http://example/v")

    # NOTE: the real filename has to be free for yt-dlp to write into.
    assert not media.exists()
    assert not sidecar.exists()
    assert len(backups) == 2

    downloader._restore_backups(backups)
    assert media.read_bytes() == b"original media"
    assert sidecar.exists()
    assert not list(tmp_path.glob("*" + downloader.BACKUP_SUFFIX))


def test_backups_are_deleted_after_a_successful_download(tmp_path):
    media = tmp_path / "Video.mp4"
    media.write_bytes(b"old")

    backups = downloader._backup_existing_outputs(_FakeYdl(str(media)), "http://example/v")
    assert backups

    # the "new" download writes its own file at the real name
    media.write_bytes(b"new")
    downloader._discard_backups(backups)

    assert media.read_bytes() == b"new"
    assert not list(tmp_path.glob("*" + downloader.BACKUP_SUFFIX))


def test_transient_files_are_never_backed_up(tmp_path):
    media = tmp_path / "Video.mp4"
    media.write_bytes(b"x")
    (tmp_path / "Video.mp4.part").write_bytes(b"junk")
    (tmp_path / "Video.mp4.ytdl").write_text("{}", encoding="utf-8")

    backups = downloader._backup_existing_outputs(_FakeYdl(str(media)), "http://example/v")

    assert [os.path.basename(orig) for _bak, orig in backups] == ["Video.mp4"]


def test_nothing_to_back_up_is_not_an_error(tmp_path):
    assert downloader._backup_existing_outputs(_FakeYdl(str(tmp_path / "Absent.mp4")), "u") == []


def test_playlist_is_skipped(tmp_path):
    # NOTE: a playlist has no single output file to protect.
    media = tmp_path / "Video.mp4"
    media.write_bytes(b"x")
    ydl = _FakeYdl(str(media), info={"_type": "playlist"})
    assert downloader._backup_existing_outputs(ydl, "u") == []
    assert media.exists()


# --- YouTube JS runtime (Deno + yt-dlp-ejs) ----------------------------------


def _requirements_ytdlp_spec() -> str:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "requirements.txt")
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line.startswith("yt-dlp"):
                return re.split(r"[<>=!~;]", line, maxsplit=1)[0].strip()
    raise AssertionError("no yt-dlp line in requirements.txt")


def test_requirements_pull_in_deno_and_the_solver_scripts():
    # NOTE: without these two extras YouTube challenge solving silently stops
    # working - formats go missing and age-restricted videos fail even with
    # valid cookies (see the NOTE in requirements.txt).
    spec = _requirements_ytdlp_spec()
    extras = set(spec[spec.index("[") + 1 : spec.index("]")].split(","))
    assert {"default", "deno"} <= extras


def test_in_app_update_installs_the_same_spec_as_requirements():
    # NOTE: a plain "yt-dlp" update would leave yt-dlp-ejs at the old pinned
    # version, which a newer yt-dlp then refuses to use.
    assert downloader.YTDLP_PIP_SPEC == _requirements_ytdlp_spec()


def test_update_ytdlp_runs_pip_with_the_full_spec(monkeypatch):
    monkeypatch.setattr(downloader, "is_docker", lambda: False)
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(downloader.subprocess, "run", fake_run)
    downloader.update_ytdlp()
    assert captured["cmd"][-1] == downloader.YTDLP_PIP_SPEC
    assert "yt-dlp" not in captured["cmd"]


def _fake_ydl_with_runtimes(runtimes):
    class FakeYdl:
        def __init__(self, params):
            self._js_runtimes = runtimes

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    return FakeYdl


def _runtime(version, supported=True):
    return SimpleNamespace(info=SimpleNamespace(version=version, supported=supported))


@pytest.fixture
def solver_installed(monkeypatch):
    import yt_dlp.dependencies

    monkeypatch.setattr(yt_dlp.dependencies, "yt_dlp_ejs", SimpleNamespace(version="0.8.0"))


def test_js_runtime_status_reports_a_usable_runtime(monkeypatch, solver_installed):
    monkeypatch.setattr(downloader, "YoutubeDL", _fake_ydl_with_runtimes({"deno": _runtime("2.9.7")}))
    assert downloader.js_runtime_status() == {
        "js_runtime": "deno",
        "js_runtime_version": "2.9.7",
        "js_solver": "0.8.0",
    }


@pytest.mark.parametrize(
    "runtime",
    [
        None,  # name yt-dlp doesn't know
        SimpleNamespace(info=None),  # executable not found
        _runtime("2.0.0", supported=False),  # too old
    ],
)
def test_js_runtime_status_ignores_unusable_runtimes(monkeypatch, solver_installed, runtime):
    monkeypatch.setattr(downloader, "YoutubeDL", _fake_ydl_with_runtimes({"deno": runtime}))
    status = downloader.js_runtime_status()
    assert status["js_runtime"] is None
    assert status["js_runtime_version"] is None


def test_js_runtime_status_reports_a_missing_solver(monkeypatch):
    import yt_dlp.dependencies

    monkeypatch.setattr(yt_dlp.dependencies, "yt_dlp_ejs", None)
    monkeypatch.setattr(downloader, "YoutubeDL", _fake_ydl_with_runtimes({"deno": _runtime("2.9.7")}))
    status = downloader.js_runtime_status()
    assert status["js_solver"] is None
    assert status["js_runtime"] == "deno"


def test_js_runtime_status_survives_a_yt_dlp_internal_change(monkeypatch, solver_installed):
    # NOTE: _js_runtimes is private yt-dlp API - if it ever disappears the
    # Settings page must still load, just without runtime info.
    class BrokenYdl:
        def __init__(self, params):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(downloader, "YoutubeDL", BrokenYdl)
    assert downloader.js_runtime_status()["js_runtime"] is None


def test_version_check_includes_runtime_status_even_offline(monkeypatch):
    def offline(*args, **kwargs):
        raise OSError("no network")

    monkeypatch.setattr(downloader.urllib.request, "urlopen", offline)
    monkeypatch.setattr(
        downloader,
        "js_runtime_status",
        lambda: {"js_runtime": "deno", "js_runtime_version": "2.9.7", "js_solver": "0.8.0"},
    )
    result = downloader.check_ytdlp_update()
    assert result["update_available"] is None
    assert result["js_runtime"] == "deno"
    assert result["js_solver"] == "0.8.0"


# --- probe(): yt-dlp's side messages explaining a sign-in failure -------------


def _probe_failing_with(monkeypatch, side_messages, error):
    """probe() against a fake yt-dlp that logs `side_messages`, then raises `error`."""

    class FakeYdl:
        def __init__(self, params):
            self.params = params

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def extract_info(self, url, download=False):
            logger = self.params["logger"]
            for kind, message in side_messages:
                getattr(logger, kind)(message)
            raise Exception(error)

    monkeypatch.setattr(downloader, "YoutubeDL", FakeYdl)
    with pytest.raises(downloader.ProbeError) as exc:
        downloader.probe("https://www.youtube.com/watch?v=x")
    return str(exc.value)


AGE_ERROR = "ERROR: [youtube] x: Sign in to confirm your age. This video may be inappropriate for some users."


def test_probe_appends_the_expired_cookies_warning(monkeypatch):
    # NOTE: yt-dlp reports this via report_warning -> logger.warning.
    expired = "[youtube] The provided YouTube account cookies are no longer valid. They have likely been rotated"
    message = _probe_failing_with(monkeypatch, [("warning", expired)], AGE_ERROR)
    assert message.startswith(AGE_ERROR)
    assert "account cookies are no longer valid" in message


def test_probe_appends_the_account_age_verification_notice(monkeypatch):
    # NOTE: yt-dlp reports this via to_screen -> logger.debug.
    notice = "[youtube] x: This video is age-restricted and YouTube is requiring account age-verification"
    message = _probe_failing_with(monkeypatch, [("debug", "\x1b[0;33m" + notice + "\x1b[0m")], AGE_ERROR)
    assert message == AGE_ERROR + "\n" + notice


def test_probe_leaves_other_errors_untouched(monkeypatch):
    message = _probe_failing_with(monkeypatch, [("debug", "[youtube] x: Downloading webpage")], AGE_ERROR)
    assert message == AGE_ERROR


# --- probe(): a successful but degraded result --------------------------------


def _probe_returning(monkeypatch, formats, side_messages=()):
    class FakeYdl:
        def __init__(self, params):
            self.params = params

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def extract_info(self, url, download=False):
            for kind, message in side_messages:
                getattr(self.params["logger"], kind)(message)
            return {"id": "x", "title": "t", "duration": 280, "formats": formats}

    monkeypatch.setattr(downloader, "YoutubeDL", FakeYdl)
    return downloader.probe("https://www.youtube.com/watch?v=x")


MUXED_360P = {"format_id": "18", "ext": "mp4", "vcodec": "avc1.42001E", "acodec": "mp4a.40.2", "height": 360}
OPUS_AUDIO = {"format_id": "251", "ext": "webm", "vcodec": "none", "acodec": "opus", "abr": 130}


def test_probe_reports_a_missing_audio_only_stream_and_why(monkeypatch):
    # NOTE: exactly what was seen live - an age-restricted video, cookies of
    # an account YouTube wanted age-verified, and only format 18 left.
    notice = "[youtube] x: This video is age-restricted and YouTube is requiring account age-verification; some formats may be missing"
    result = _probe_returning(monkeypatch, [MUXED_360P], [("debug", notice)])
    assert result["audio_only"] is False
    assert result["notices"] == ["account_age_verification"]


def test_probe_of_a_normal_video_has_audio_only_and_no_notices(monkeypatch):
    result = _probe_returning(monkeypatch, [MUXED_360P, OPUS_AUDIO], [("debug", "[youtube] x: Downloading webpage")])
    assert result["audio_only"] is True
    assert result["notices"] == []


# --- get_stream_info: what's actually inside a downloaded file ----------------


@pytest.mark.parametrize(
    "width, height, expected",
    [
        (1920, 1080, "1080p"),
        (1920, 800, "1080p"),  # cinema ratio - offered as 1080p before downloading too
        (1080, 1920, "1080p"),  # vertical
        (854, 480, "480p"),
        (1918, 1080, "1080p"),  # encoder rounding
        (3840, 2160, "2160p"),
        (200, 112, None),
    ],
)
def test_quality_label(width, height, expected):
    assert downloader.quality_label(width, height) == expected


@pytest.mark.parametrize(
    "rate, expected", [("30/1", 30.0), ("30000/1001", 29.97), ("25", 25.0), ("0/0", None), ("", None), (None, None)]
)
def test_parse_fps(rate, expected):
    assert downloader._parse_fps(rate) == expected


def test_stream_info_skips_embedded_cover_art(monkeypatch):
    # NOTE: an MP3/M4A's thumbnail is a "video" stream (attached_pic) - it
    # must not turn an audio file into a "1280x720 video".
    monkeypatch.setattr(
        downloader,
        "_ffprobe_json",
        lambda path, entries: {
            "streams": [
                {"codec_type": "audio", "codec_name": "mp3", "sample_rate": "44100", "channels": 2, "bit_rate": "320000"},
                {"codec_type": "video", "codec_name": "mjpeg", "width": 1280, "height": 720, "disposition": {"attached_pic": 1}},
            ]
        },
    )
    info = downloader.get_stream_info("x.mp3")
    assert info["video"] is None
    assert info["audio"] == {"codec": "MP3", "sample_rate": 44100, "channels": 2, "bitrate_kbps": 320}


def test_stream_info_names_codecs_and_tolerates_missing_fields(monkeypatch):
    monkeypatch.setattr(
        downloader,
        "_ffprobe_json",
        lambda path, entries: {
            "streams": [
                {"codec_type": "video", "codec_name": "vp9", "width": 854, "height": 480, "avg_frame_rate": "25/1"},
                {"codec_type": "audio", "codec_name": "opus", "sample_rate": "48000", "channels": 2},
            ]
        },
    )
    info = downloader.get_stream_info("x.mp4")
    assert info["video"] == {"width": 854, "height": 480, "quality": "480p", "fps": 25.0, "codec": "VP9"}
    assert info["audio"]["codec"] == "Opus"
    assert info["audio"]["bitrate_kbps"] is None


def test_stream_info_is_empty_when_ffprobe_fails(monkeypatch):
    monkeypatch.setattr(downloader, "_ffprobe_json", lambda path, entries: {})
    assert downloader.get_stream_info("x.mp4") == {"video": None, "audio": None}


@pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None, reason="ffmpeg is not installed")
def test_stream_info_reads_a_real_file(tmp_path):
    # NOTE: the one test here that runs ffmpeg/ffprobe for real - proves the
    # -show_entries query matches what ffprobe actually returns.
    path = tmp_path / "sample.mp4"
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=1:size=640x360:rate=30",
            "-f", "lavfi", "-i", "sine=duration=1:sample_rate=48000", "-ac", "2",
            "-c:v", "libx264", "-c:a", "aac", "-shortest", str(path),
        ],
        check=True,
        timeout=60,
    )
    info = downloader.get_stream_info(str(path))
    assert info["video"]["width"] == 640
    assert info["video"]["height"] == 360
    assert info["video"]["quality"] == "360p"
    assert info["video"]["fps"] == 30.0
    assert info["video"]["codec"] == "H.264"
    assert info["audio"]["codec"] == "AAC"
    assert info["audio"]["sample_rate"] == 48000
    assert info["audio"]["channels"] == 2


@pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None, reason="ffmpeg is not installed")
def test_metadata_keeps_non_ascii_titles(tmp_path):
    # NOTE: regression. ffprobe prints UTF-8, but text=True decoded it with
    # the Windows ANSI code page (cp1254 on Turkish Windows): the detail page
    # showed "YaÅŸ AltÄ±na" for "Yaş Altına" (found trying the installer).
    path = tmp_path / "clip.m4a"
    title = "15 Yaş Altına Sosyal Medya Yasağı Geldi! — ğüşiöç ĞÜŞİÖÇ 日本"
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=duration=1",
            "-metadata", f"title={title}", "-metadata", "artist=Murat Gamsız",
            "-c:a", "aac", str(path),
        ],
        check=True,
        timeout=60,
    )
    meta = downloader.get_metadata(str(path))
    assert meta["title"] == title
    assert meta["artist"] == "Murat Gamsız"
