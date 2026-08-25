"""Tests for the environment checks in deps.py (ffmpeg + Python packages)."""

import pytest

from mediagrab import deps


# --- version parsing --------------------------------------------------------


def test_zero_padding_does_not_change_the_comparison():
    assert deps._parse_version("2026.07.04") == deps._parse_version("2026.7.4")


def test_patch_releases_sort_correctly():
    # NOTE: as plain strings "0.52.10" < "0.52.4", which would hide a real update.
    assert deps._parse_version("0.52.10") > deps._parse_version("0.52.4")


def test_prerelease_suffix_is_ignored_rather_than_guessed_at():
    assert deps._parse_version("1.2.3rc1") == (1, 2, 3)


def test_leading_garbage_stops_parsing():
    assert deps._parse_version("not-a-version") == ()


# --- ffmpeg version line parsing -------------------------------------------


@pytest.mark.parametrize(
    "line,expected",
    [
        ("ffmpeg version 9.0-full_build-www.gyan.dev Copyright (c)", "9.0-full_build-www.gyan.dev"),
        ("ffmpeg version n7.1 Copyright (c) 2000-2024", "7.1"),
        ("ffprobe version 6.1.1-3ubuntu5 Copyright (c)", "6.1.1-3ubuntu5"),
        ("ffmpeg version 5.1.4 Copyright", "5.1.4"),
    ],
)
def test_ffmpeg_version_is_pulled_off_the_banner_line(line, expected):
    match = deps._FFMPEG_VERSION_RE.match(line)
    assert match is not None
    assert match.group(1) == expected


def test_unrecognised_banner_does_not_match():
    assert deps._FFMPEG_VERSION_RE.match("some unrelated output") is None


# --- requirements parsing ---------------------------------------------------


def test_requirement_names_drop_specifiers_and_extras():
    names = deps._requirement_names()
    # NOTE: "uvicorn[standard]>=0.30" has to come back as plain "uvicorn",
    # otherwise importlib.metadata can't find the installed version.
    assert "uvicorn" in names
    assert "yt-dlp" in names
    assert all("[" not in n and ">" not in n and "=" not in n for n in names)


def test_mutagen_is_declared():
    # NOTE: regression guard. MediaGrab's own code doesn't import mutagen, so
    # nothing here fails loudly without it - but yt-dlp needs it to embed cover
    # art into Opus, and Opus is the default audio format. Dropping it in
    # v1.2.0 silently broke every Opus download until v1.5.0.
    assert "mutagen" in deps._requirement_names()


def test_every_declared_requirement_is_actually_installed():
    # NOTE: catches the other half of the same class of bug - a package listed
    # in requirements.txt that nobody ever installed into the environment.
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as installed_version

    missing = []
    for name in deps._requirement_names():
        try:
            installed_version(name)
        except PackageNotFoundError:
            missing.append(name)
    assert not missing, f"declared but not installed: {missing}"


def test_dev_only_packages_are_not_reported_to_the_user():
    # NOTE: pytest lives in requirements-dev.txt on purpose - the Settings page
    # lists whatever requirements.txt contains, and a test runner has no place
    # in an end user's dependency list.
    assert "pytest" not in deps._requirement_names()


# --- ffmpeg install commands ------------------------------------------------


def test_every_platform_gets_an_install_command():
    keys = {entry["key"] for entry in deps.FFMPEG_INSTALL_COMMANDS}
    assert keys == {"windows", "macos", "linux"}
    for entry in deps.FFMPEG_INSTALL_COMMANDS:
        assert entry["label"] and entry["command"]


def test_check_ffmpeg_reports_a_known_platform():
    result = deps.check_ffmpeg()
    assert result["platform"] in {"windows", "macos", "linux"}
    assert result["install_commands"] is deps.FFMPEG_INSTALL_COMMANDS
    # NOTE: "ok" must reflect BOTH binaries - ffprobe missing while ffmpeg is
    # present still breaks duration and cover-art reading.
    assert result["ok"] == bool(result["ffmpeg"] and result["ffprobe"])
