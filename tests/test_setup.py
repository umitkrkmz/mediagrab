"""Tests for setup_mediagrab.py's pure helpers.

NOTE: the installer is a standalone script at the repo root (it has to run
BEFORE the mediagrab package exists on disk), so it's loaded by path here
rather than imported as part of the package. Only logic that doesn't build a
Tk window is exercised.
"""

import importlib.util
import inspect
import os
import re
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


def test_every_file_the_app_persists_is_kept(setup_mod):
    """Whatever store.py writes beside the app must survive Remove/Repair."""
    # NOTE: derived from store.py rather than listed here, because a hand-kept
    # list is exactly what let settings.json ship unprotected in v1.6.0 - the
    # file was added to the app and nobody thought to update the installer.
    store_py = SETUP_PY.parent / "mediagrab" / "store.py"
    persisted = set(re.findall(r'app_dir\(\),\s*"([^"]+)"', store_py.read_text(encoding="utf-8")))
    assert persisted, "no persisted files found - has store.py been restructured?"
    missing = persisted - set(setup_mod.USER_DATA_ENTRIES)
    assert not missing, f"the installer would delete: {sorted(missing)}"


def test_refreshing_the_path_only_ever_adds_entries(setup_mod, monkeypatch):
    # NOTE: the process is handed a PATH it may genuinely need (PyInstaller
    # adds its own unpack directory), so refreshing must never drop entries.
    marker = os.path.join("Z:" + os.sep, "mediagrab-test-marker")
    monkeypatch.setenv("PATH", marker)
    setup_mod.refresh_path_from_registry()
    assert marker in os.environ["PATH"].split(os.pathsep)


def test_the_refresh_button_actually_rereads_the_path(setup_mod):
    """Refresh must re-read PATH, not just re-probe the stale one."""
    # NOTE: asserted against the source because _refresh_status needs a live Tk
    # window. Without this the helper could sit there fully tested and simply
    # never be wired up - which is the whole bug it was written to fix.
    source = inspect.getsource(setup_mod.SetupApp._refresh_status)
    assert "refresh_path_from_registry()" in source, "Refresh never re-reads PATH"
    assert source.index("refresh_path_from_registry()") < source.index('find_tool("git")'),         "PATH must be refreshed BEFORE the tools are probed"


@pytest.mark.skipif(os.name != "nt", reason="PATH lives in the registry only on Windows")
def test_refreshing_the_path_recovers_a_tool_a_stale_path_hides(setup_mod, monkeypatch):
    """The reported bug: the window was open before the tool was installed."""
    # NOTE: os.environ["PATH"] is frozen at process start, so a tool installed
    # while the window is open stays invisible and "Refresh" can never help.
    # Dropping git's directory reproduces exactly that starting state.
    if not setup_mod.find_tool("git"):
        pytest.skip("git isn't on PATH here, so there is nothing to hide")

    stale = os.pathsep.join(
        entry for entry in os.environ["PATH"].split(os.pathsep) if "git" not in entry.lower()
    )
    monkeypatch.setenv("PATH", stale)
    assert setup_mod.find_tool("git") is None, "the stale PATH should not find git"

    setup_mod.refresh_path_from_registry()
    assert setup_mod.find_tool("git") is not None, "Refresh should have found git again"


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
