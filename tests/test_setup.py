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


def test_every_translation_key_used_in_the_source_exists(setup_mod):
    # NOTE: a typo in a key only blows up when that page is shown - in the
    # middle of a real install. Cheap to catch here instead.
    source = SETUP_PY.read_text(encoding="utf-8")
    used = set(re.findall(r'self\.t\(\s*"([A-Za-z0-9_]+)"', source))
    used |= set(re.findall(r'"(progress_title_[a-z]+)"', source))
    missing = used - set(setup_mod.STRINGS["tr"])
    assert not missing, f"unknown translation keys: {sorted(missing)}"


# --- remembered install folder -----------------------------------------------


@pytest.fixture
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    return tmp_path


def test_state_file_lives_under_the_user_profile_not_beside_the_exe(setup_mod, isolated_state):
    # NOTE: people run the installer from Downloads and then delete or move
    # it - anything stored next to the exe would be lost with it.
    path = Path(setup_mod.installer_state_path())
    assert isolated_state in path.parents
    assert Path(setup_mod.base_dir()) not in path.parents


def test_last_install_dir_round_trips(setup_mod, isolated_state, tmp_path):
    assert setup_mod.load_last_install_dir() is None
    target = str(tmp_path / "MediaGrab")
    setup_mod.save_last_install_dir(target)
    assert setup_mod.load_last_install_dir() == os.path.abspath(target)
    setup_mod.forget_last_install_dir()
    assert setup_mod.load_last_install_dir() is None


def test_a_corrupt_state_file_is_ignored(setup_mod, isolated_state):
    path = Path(setup_mod.installer_state_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", encoding="utf-8")
    assert setup_mod.load_last_install_dir() is None
    path.write_text('{"last_install_dir": 42}', encoding="utf-8")
    assert setup_mod.load_last_install_dir() is None


def test_forgetting_when_nothing_is_remembered_is_not_an_error(setup_mod, isolated_state):
    setup_mod.forget_last_install_dir()


def test_same_folder_ignores_trailing_separators_and_case_rules(setup_mod, tmp_path):
    folder = str(tmp_path / "MediaGrab")
    assert setup_mod.same_folder(folder, folder + os.sep)
    if os.name == "nt":
        assert setup_mod.same_folder(folder, folder.upper())
    assert not setup_mod.same_folder(folder, str(tmp_path / "Other"))


# --- the wizard itself -------------------------------------------------------


@pytest.fixture(scope="module")
def wizard(setup_mod):
    # NOTE: ONE Tk interpreter for the whole module, shared by every test.
    # Creating a fresh Tk root after a previous one was destroyed hit a rare,
    # timing-dependent Tcl bootstrap failure here ("Can't find a usable
    # init.tcl" / "invalid command name tcl_findLibrary") - only ever on the
    # SECOND interpreter in a process, never the first. The installer itself
    # opens exactly one root per process (the language toggle rebuilds the
    # widgets on the same root), so users are never in that situation; the
    # tests simply mirror that by never re-creating the root either.
    import tkinter as tk

    try:
        app = setup_mod.SetupApp()
    except tk.TclError:
        pytest.skip("no display available for Tk")
    app.withdraw()  # keep it off-screen; widget state is unaffected
    yield app
    app.destroy()


@pytest.fixture
def app(wizard, setup_mod, isolated_state):
    """The shared wizard, reset to a known state before every test."""
    wizard.mode = None
    wizard.base_dir = setup_mod.base_dir()
    wizard.folder_prefilled = False
    wizard.desktop_shortcut_var.set(False)
    wizard.start_shortcut_var.set(False)
    wizard._set_lang("tr")
    wizard._show_page("welcome")
    return wizard


def _fake_install(folder):
    (folder / "mediagrab").mkdir(parents=True)
    (folder / "run.py").write_text("", encoding="utf-8")
    return str(folder)


def test_every_wizard_page_renders_in_both_languages_and_modes(setup_mod, app, tmp_path):
    # NOTE: the release smoke test only proves the exe starts. This walks
    # every page in every mode and language, so a page that only breaks when
    # it is shown (a missing widget, a bad key) can't slip through.
    installed = _fake_install(tmp_path / "Installed")
    setup_mod.save_last_install_dir(installed)

    for lang in ("tr", "en"):
        app._set_lang(lang)
        app._show_page("welcome")
        assert app.remembered_label.cget("text").endswith(installed)
        for mode in (setup_mod.MODE_INSTALL, setup_mod.MODE_REPAIR, setup_mod.MODE_REMOVE):
            app._start_mode(mode)
            if mode == setup_mod.MODE_REMOVE:
                assert app.current_page == "folder"
            else:
                assert app.current_page == "deps"
                app._show_page("folder")
            if mode != setup_mod.MODE_INSTALL:
                assert app.base_dir == installed, "Repair/Remove should pre-fill the last install"
                assert app.folder_prefilled
            app._show_page("summary")
            app._show_page("progress")
            app.update_idletasks()


def test_the_language_toggle_retranslates_every_page(setup_mod, app):
    app._set_lang("en")
    assert app.title() == setup_mod.STRINGS["en"]["title"]
    assert app.deps_next_btn.cget("text") == setup_mod.STRINGS["en"]["next"]
    app._set_lang("tr")
    assert app.title() == setup_mod.STRINGS["tr"]["title"]
    assert app.deps_next_btn.cget("text") == setup_mod.STRINGS["tr"]["next"]


def test_repair_and_remove_do_not_trust_a_remembered_folder_that_is_gone(setup_mod, app, tmp_path):
    # NOTE: the user may have deleted the install by hand; pre-filling the
    # stale folder would point Remove at something that isn't MediaGrab.
    setup_mod.save_last_install_dir(str(tmp_path / "Deleted"))
    app._start_mode(setup_mod.MODE_REMOVE)
    assert app.base_dir != str(tmp_path / "Deleted")
    assert not app.folder_prefilled


def test_install_next_is_blocked_on_a_folder_that_already_has_an_install(setup_mod, app, tmp_path):
    installed = _fake_install(tmp_path / "Installed")
    app.mode = setup_mod.MODE_INSTALL
    app.base_dir = installed
    app._show_page("folder")
    assert str(app.folder_next_btn.cget("state")) == "disabled"
    assert app.folder_hint_label.cget("text") == app.t("folder_already_installed")

    app.base_dir = str(tmp_path / "Fresh")
    os.makedirs(app.base_dir)
    app._render_folder_page()
    assert str(app.folder_next_btn.cget("state")) == "normal"


def test_remove_next_is_blocked_on_a_folder_with_no_install(setup_mod, app, tmp_path):
    app.mode = setup_mod.MODE_REMOVE
    app.base_dir = str(tmp_path)
    app._show_page("folder")
    assert str(app.folder_next_btn.cget("state")) == "disabled"
    assert app.folder_hint_label.cget("text") == app.t("folder_not_installed")


def test_remove_hides_the_shortcut_boxes_and_install_shows_them(setup_mod, app, tmp_path):
    app.mode = setup_mod.MODE_REMOVE
    app.base_dir = _fake_install(tmp_path / "Installed")
    app._show_page("folder")
    assert not app.desktop_check.winfo_manager(), "Remove has nothing to make a shortcut for"

    app.mode = setup_mod.MODE_INSTALL
    app.base_dir = str(tmp_path / "Fresh")
    os.makedirs(app.base_dir)
    app._show_page("folder")
    assert app.desktop_check.winfo_manager()


def test_a_finished_install_is_remembered_and_a_finished_remove_forgets_it(setup_mod, app, tmp_path):
    installed = _fake_install(tmp_path / "Installed")
    app.mode = setup_mod.MODE_INSTALL
    app.base_dir = installed
    app._show_page("progress")
    app._on_job_done(True)
    assert setup_mod.load_last_install_dir() == installed

    app.mode = setup_mod.MODE_REMOVE
    app._on_job_done(True)
    assert setup_mod.load_last_install_dir() is None


def test_removing_a_different_folder_keeps_the_remembered_one(setup_mod, app, tmp_path):
    remembered = _fake_install(tmp_path / "Main")
    other = _fake_install(tmp_path / "Other")
    setup_mod.save_last_install_dir(remembered)
    app.mode = setup_mod.MODE_REMOVE
    app.base_dir = other
    app._show_page("progress")
    app._on_job_done(True)
    assert setup_mod.load_last_install_dir() == remembered


def test_a_failed_job_remembers_nothing(setup_mod, app, tmp_path):
    app.mode = setup_mod.MODE_INSTALL
    app.base_dir = str(tmp_path)
    app._show_page("progress")
    app._on_job_done(False)
    assert setup_mod.load_last_install_dir() is None


# --- Docker install mode ------------------------------------------------------


def test_docker_status_missing_when_docker_not_on_path(setup_mod, monkeypatch):
    monkeypatch.setattr(setup_mod, "find_tool", lambda *a: None)
    status, path = setup_mod.docker_status()
    assert (status, path) == ("missing", None)


def test_docker_status_no_compose_when_compose_plugin_absent(setup_mod, monkeypatch):
    monkeypatch.setattr(setup_mod, "find_tool", lambda *a: "/usr/bin/docker")
    monkeypatch.setattr(setup_mod, "_run_probe", lambda cmd: "" if cmd[1] == "compose" else "x")
    status, _path = setup_mod.docker_status()
    assert status == "no_compose"


def test_docker_status_not_running_when_daemon_unreachable(setup_mod, monkeypatch):
    monkeypatch.setattr(setup_mod, "find_tool", lambda *a: "/usr/bin/docker")

    def fake_probe(cmd):
        return "Docker Compose version v2.20.0" if cmd[1] == "compose" else ""

    monkeypatch.setattr(setup_mod, "_run_probe", fake_probe)
    status, _path = setup_mod.docker_status()
    assert status == "not_running"


def test_docker_status_ready_when_everything_available(setup_mod, monkeypatch):
    monkeypatch.setattr(setup_mod, "find_tool", lambda *a: "/usr/bin/docker")
    monkeypatch.setattr(setup_mod, "_run_probe", lambda cmd: "ok")
    status, path = setup_mod.docker_status()
    assert (status, path) == ("ready", "/usr/bin/docker")


def test_docker_compose_yaml_references_the_published_image(setup_mod):
    yaml_text = setup_mod.docker_compose_yaml("a-real-password")
    assert setup_mod.DOCKER_IMAGE in yaml_text
    assert "build:" not in yaml_text


def test_docker_compose_yaml_uses_bridge_networking_not_host(setup_mod):
    # NOTE: unlike the repo's own docker-compose.yml, this installer only ever
    # runs on Windows, where Docker Desktop doesn't support host networking.
    yaml_text = setup_mod.docker_compose_yaml("a-real-password")
    assert "network_mode" not in yaml_text
    assert '"8420:8420"' in yaml_text


def test_docker_compose_yaml_mounts_the_same_volumes_as_the_repo_compose_file(setup_mod):
    yaml_text = setup_mod.docker_compose_yaml("a-real-password")
    for path in ("./data/indirilenler:/app/indirilenler", "./data/settings.json:/app/settings.json",
                 "./data/channels.json:/app/channels.json", "./data/pip-packages:/data/pip-packages"):
        assert path in yaml_text


def test_docker_compose_yaml_quotes_the_whole_environment_item_not_just_the_value(setup_mod):
    # NOTE: regression test for a bug caught via `docker compose config` -
    # quoting only the value (`- KEY="VALUE"`) is an UNQUOTED YAML plain
    # scalar, so compose's KEY=VALUE splitter hands the container a password
    # with literal quote characters baked in. The quotes must wrap the whole
    # "KEY=VALUE" item instead.
    yaml_text = setup_mod.docker_compose_yaml("simple-password-1")
    assert '- "MEDIAGRAB_INITIAL_PASSWORD=simple-password-1"' in yaml_text
    assert 'MEDIAGRAB_INITIAL_PASSWORD="simple-password-1"' not in yaml_text


def test_docker_compose_yaml_escapes_quotes_and_backslashes(setup_mod):
    password = 'pa"ss\\word'
    yaml_text = setup_mod.docker_compose_yaml(password)
    # NOTE: the quotes must wrap the WHOLE "KEY=VALUE" item, not just the
    # value - `- KEY="VALUE"` is an unquoted YAML plain scalar whose literal
    # text includes the quote characters, corrupting the real password (see
    # docker_compose_yaml's own comment for how this was caught).
    match = re.search(r'"MEDIAGRAB_INITIAL_PASSWORD=((?:[^"\\]|\\.)*)"', yaml_text)
    assert match, "password line not found or not a properly-quoted YAML scalar"
    # NOTE: reverses the generator's own escaping (each \X -> X) and checks it
    # round-trips back to the exact original password.
    restored = re.sub(r"\\(.)", r"\1", match.group(1))
    assert restored == password


def test_docker_install_creates_data_files_without_clobbering_existing(setup_mod, app, tmp_path):
    app.docker_folder = str(tmp_path / "DockerInstall")
    app._run_cmd = lambda cmd, cwd: True
    app._wait_for_docker_container = lambda: True

    # NOTE: a real followed-channels file already sitting there (e.g. a
    # second run of Docker install) must survive untouched.
    data_dir = os.path.join(app.docker_folder, "data")
    os.makedirs(data_dir)
    existing_channels = os.path.join(data_dir, "channels.json")
    with open(existing_channels, "w", encoding="utf-8") as f:
        f.write('{"channels": [{"id": "keep-me"}]}')

    assert app._do_docker_install("a-real-password") is True

    # bind-mount sources must be real FILES, never directories (Docker
    # creates a missing one as a directory, which breaks every future read).
    assert os.path.isdir(os.path.join(data_dir, "indirilenler"))
    assert os.path.isfile(os.path.join(data_dir, "settings.json"))
    with open(existing_channels, encoding="utf-8") as f:
        assert "keep-me" in f.read()

    compose_path = os.path.join(app.docker_folder, "docker-compose.yml")
    with open(compose_path, encoding="utf-8") as f:
        assert "a-real-password" in f.read()


def test_docker_install_fails_when_compose_up_fails(setup_mod, app, tmp_path):
    app.docker_folder = str(tmp_path / "Fail")
    app._run_cmd = lambda cmd, cwd: False
    app._wait_for_docker_container = lambda: True
    assert app._do_docker_install("a-real-password") is False


def test_docker_install_fails_when_container_never_responds(setup_mod, app, tmp_path):
    app.docker_folder = str(tmp_path / "NoResponse")
    app._run_cmd = lambda cmd, cwd: True
    app._wait_for_docker_container = lambda: False
    assert app._do_docker_install("a-real-password") is False


def test_docker_job_rejects_a_short_password_without_starting(setup_mod, app, monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(setup_mod.messagebox, "showerror", lambda *a, **k: calls.append(a))
    app.mode = setup_mod.MODE_DOCKER
    app.docker_folder = str(tmp_path)
    app.docker_password_var.set("short")
    app._start_docker_job()
    assert calls, "expected a password-too-short dialog"
    assert not app._job_running


def test_docker_job_rejects_an_unsafe_folder_without_starting(setup_mod, app, monkeypatch):
    calls = []
    monkeypatch.setattr(setup_mod.messagebox, "showerror", lambda *a, **k: calls.append(a))
    app.mode = setup_mod.MODE_DOCKER
    app.docker_folder = os.path.expanduser("~")
    app.docker_password_var.set("a-real-password")
    app._start_docker_job()
    assert calls, "expected an unsafe-folder dialog"
    assert not app._job_running


def test_docker_install_button_disabled_until_docker_is_ready(setup_mod, app, monkeypatch):
    monkeypatch.setattr(setup_mod, "docker_status", lambda: ("missing", None))
    app._start_docker_mode()
    assert str(app.docker_install_btn.cget("state")) == "disabled"

    monkeypatch.setattr(setup_mod, "docker_status", lambda: ("ready", "docker"))
    app._refresh_docker_status()
    assert str(app.docker_install_btn.cget("state")) == "normal"


def test_docker_page_renders_in_both_languages(setup_mod, app, monkeypatch):
    monkeypatch.setattr(setup_mod, "docker_status", lambda: ("ready", "docker"))
    for lang in ("tr", "en"):
        app._set_lang(lang)
        app._start_docker_mode()
        assert app.current_page == "docker"
        app.update_idletasks()


def test_finishing_docker_install_offers_to_open_the_browser_not_the_launcher(setup_mod, app):
    app.mode = setup_mod.MODE_DOCKER
    app._show_page("progress")
    app._on_job_done(True)
    assert app.launch_btn.cget("text") == app.t("open_browser")


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
