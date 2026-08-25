"""Tests for the pure logic in downloader.py.

NOTE: nothing here touches the network or spawns yt-dlp/ffmpeg - these cover
the parsing and file-shuffling code where the real bugs have actually been,
so the suite stays fast and runs offline.
"""

import os

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
