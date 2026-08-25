"""Tests for setup_mediagrab.py's pure helpers.

NOTE: the installer is a standalone script at the repo root (it has to run
BEFORE the mediagrab package exists on disk), so it's loaded by path here
rather than imported as part of the package. Only logic that doesn't build a
Tk window is exercised.
"""

import importlib.util
import os
import sys
from pathlib import Path

import pytest

SETUP_PY = Path(__file__).resolve().parent.parent / "setup_mediagrab.py"


@pytest.fixture(scope="module")
def setup_mod():
    spec = importlib.util.spec_from_file_location("setup_mediagrab_under_test", SETUP_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- the installer must stay dependency-free ---------------------------------


@pytest.mark.skipif(
    not hasattr(sys, "stdlib_module_names"),
    reason="sys.stdlib_module_names needs Python 3.10+",
)
def test_installer_imports_only_the_standard_library():
    # NOTE: this is a licensing guarantee, not just tidiness - the README
    # states the built exe bundles no third-party code, and that only holds
    # while this file imports nothing outside the stdlib.
    import ast

    tree = ast.parse(SETUP_PY.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    assert not (imported - set(sys.stdlib_module_names))


def test_installer_never_imports_the_app_package():
    # NOTE: it runs before MediaGrab is on disk, so any such import would
    # crash the installer for the very users who need it most.
    source = SETUP_PY.read_text(encoding="utf-8")
    assert "from mediagrab" not in source
    assert "import mediagrab" not in source


# --- translations ------------------------------------------------------------


def test_both_languages_define_the_same_keys(setup_mod):
    tr, en = set(setup_mod.STRINGS["tr"]), set(setup_mod.STRINGS["en"])
    assert tr == en, f"mismatch: {sorted(tr ^ en)}"


def test_no_string_is_empty(setup_mod):
    for lang, table in setup_mod.STRINGS.items():
        for key, value in table.items():
            assert value.strip(), f"{lang}.{key} is empty"


def test_format_placeholders_match_between_languages(setup_mod):
    # NOTE: a placeholder present in one language but not the other raises
    # KeyError at runtime - in the middle of an install, in the log.
    import re

    for key, tr_text in setup_mod.STRINGS["tr"].items():
        tr_fields = set(re.findall(r"\{(\w+)\}", tr_text))
        en_fields = set(re.findall(r"\{(\w+)\}", setup_mod.STRINGS["en"][key]))
        assert tr_fields == en_fields, f"{key}: {tr_fields} vs {en_fields}"


def test_detect_lang_returns_a_supported_language(setup_mod):
    assert setup_mod.detect_lang() in setup_mod.STRINGS


# --- version probing ---------------------------------------------------------


def test_python_version_reads_the_running_interpreter(setup_mod):
    assert setup_mod.python_version(sys.executable) == sys.version_info[:2]


def test_python_version_of_a_missing_interpreter_is_none(setup_mod):
    assert setup_mod.python_version("definitely-not-a-real-python") is None


def test_the_running_interpreter_satisfies_the_minimum(setup_mod):
    # NOTE: guards MIN_PYTHON against drifting above what the project's own
    # venv actually runs on.
    assert sys.version_info[:2] >= setup_mod.MIN_PYTHON


def test_minimum_matches_what_the_code_actually_needs(setup_mod):
    # NOTE: list[dict] style annotations are evaluated at import time and need
    # 3.9; if anything 3.10-only creeps in, MIN_PYTHON has to move with it.
    import ast

    root = SETUP_PY.parent
    for path in list((root / "mediagrab").glob("*.py")) + [root / "run.py"]:
        ast.parse(path.read_text(encoding="utf-8"), feature_version=setup_mod.MIN_PYTHON)


@pytest.mark.parametrize(
    "line,expected",
    [
        ("ffmpeg version 9.0-full_build-www.gyan.dev Copyright", "9.0-full_build-www.gyan.dev"),
        ("ffmpeg version n7.1 Copyright (c)", "7.1"),
        ("ffprobe version 6.1.1-3ubuntu5 Copyright", "6.1.1-3ubuntu5"),
    ],
)
def test_ffmpeg_banner_parsing(setup_mod, line, expected):
    match = setup_mod._FFMPEG_VERSION_RE.match(line)
    assert match and match.group(1) == expected


def test_missing_tool_reports_none(setup_mod):
    assert setup_mod.tool_version("definitely-not-a-real-tool") is None


def test_install_command_is_offered_for_this_platform(setup_mod):
    assert setup_mod.ffmpeg_install_command().strip()


# --- launcher / paths --------------------------------------------------------


def test_launcher_name_matches_the_platform(setup_mod):
    expected = "MediaGrab Baslat.bat" if os.name == "nt" else "mediagrab-baslat.sh"
    assert setup_mod._launcher_name() == expected


def test_user_data_is_on_the_keep_list(setup_mod):
    # NOTE: Remove/Repair wipe the folder - anything missing from this tuple
    # is data the user permanently loses.
    assert "indirilenler" in setup_mod.USER_DATA_ENTRIES
    assert "channels.json" in setup_mod.USER_DATA_ENTRIES


def test_is_installed_needs_both_markers(setup_mod, tmp_path):
    assert not setup_mod.is_installed(str(tmp_path))
    (tmp_path / "run.py").write_text("", encoding="utf-8")
    assert not setup_mod.is_installed(str(tmp_path))
    (tmp_path / "mediagrab").mkdir()
    assert setup_mod.is_installed(str(tmp_path))


# --- install-folder safety ---------------------------------------------------


def test_cloud_folders_are_recognised(setup_mod):
    assert setup_mod.cloud_service_in_path(r"C:\Users\me\OneDrive\Masaüstü\tmp") == "onedrive"
    assert setup_mod.cloud_service_in_path("/home/me/Dropbox/apps") == "dropbox"
    assert setup_mod.cloud_service_in_path(r"C:\Users\me\Google Drive\x") == "google drive"


def test_a_plain_folder_is_not_flagged_as_cloud(setup_mod):
    assert setup_mod.cloud_service_in_path(r"C:\MediaGrab") is None


def test_drive_root_is_refused(setup_mod):
    # NOTE: Remove wipes the install folder - allowing a drive root here would
    # let one click delete the whole disk's contents.
    assert setup_mod.is_unsafe_target("C:\\") if os.name == "nt" else setup_mod.is_unsafe_target("/")


def test_home_and_personal_folders_are_refused(setup_mod):
    home = os.path.expanduser("~")
    assert setup_mod.is_unsafe_target(home)
    assert setup_mod.is_unsafe_target(os.path.join(home, "Desktop"))
    assert setup_mod.is_unsafe_target(os.path.join(home, "Documents"))


def test_a_dedicated_folder_is_allowed(setup_mod, tmp_path):
    assert not setup_mod.is_unsafe_target(str(tmp_path / "MediaGrab"))


def test_powershell_quoting_escapes_single_quotes(setup_mod):
    # NOTE: shortcut creation passes paths into a PowerShell command; a folder
    # named "Ali's Videos" would otherwise break out of the quoted string.
    assert setup_mod._ps_quote("C:\\Ali's Videos") == "'C:\\Ali''s Videos'"
