"""The Inno Setup installer's own logic, run through real ISCC.

NOTE: Windows + Inno Setup 6 only (skipped elsewhere, e.g. Linux CI). A tiny
harness setup includes packaging/settings_json.iss, runs one function in
InitializeSetup, writes the result and exits before any wizard is shown -
nothing is installed. Set MEDIAGRAB_ISCC to point at another ISCC.exe.
"""

import json
import re
import threading
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


def _iscc():
    candidates = [
        os.environ.get("MEDIAGRAB_ISCC", ""),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Inno Setup 6", "ISCC.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Inno Setup 6", "ISCC.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Inno Setup 6", "ISCC.exe"),
    ]
    return next((c for c in candidates if c and os.path.isfile(c)), None)


pytestmark = pytest.mark.skipif(os.name != "nt" or not _iscc(), reason="needs Windows and Inno Setup 6")

HARNESS = r"""
[Setup]
AppName=MediaGrab settings_json harness
AppVersion=1
CreateAppDir=no
Uninstallable=no
PrivilegesRequired=lowest
OutputDir={out}
OutputBaseFilename=harness

[Code]
#include "{include}"

function InitializeSetup(): Boolean;
var
  Lines: TArrayOfString;
begin
  SetArrayLength(Lines, 1);
  Lines[0] := '[' + ReadDownloadDirSetting(ExpandConstant('{param:in}')) + ']';
  SaveStringsToUTF8File(ExpandConstant('{param:out}'), Lines, False);
  Result := False;
end;
"""


@pytest.fixture(scope="module")
def harness(tmp_path_factory):
    folder = tmp_path_factory.mktemp("iss")
    script = folder / "harness.iss"
    script.write_text(
        HARNESS.replace("{out}", str(folder)).replace("{include}", str(ROOT / "packaging" / "settings_json.iss")),
        encoding="utf-8-sig",
    )
    subprocess.run([_iscc(), "-Q", str(script)], check=True, capture_output=True)
    exe = folder / "harness.exe"

    def read(settings_path):
        out = folder / "result.txt"
        if out.exists():
            out.unlink()
        subprocess.run([str(exe), "/VERYSILENT", "/SUPPRESSMSGBOXES", f"/in={settings_path}", f"/out={out}"], timeout=60)
        return out.read_text(encoding="utf-8-sig").strip()[1:-1]

    return read


def _settings(tmp_path, data, **dump):
    path = tmp_path / "settings.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, **dump)
    return path


@pytest.mark.parametrize(
    "folder",
    [
        r"D:\MediaGrab Deneme Ü",
        r"C:\Users\Şule\Videolar/Çocuk ✓",
        "\\\\nas\\share\\Video",
    ],
)
def test_reads_the_folder_store_py_writes(tmp_path, harness, folder):
    # NOTE: written exactly the way store.save_settings writes it.
    path = _settings(tmp_path, {"theme": "dark", "download_dir": folder, "speed": 0}, ensure_ascii=False, indent=2)
    assert harness(path) == folder


def test_reads_ascii_escaped_json_too(tmp_path, harness):
    path = _settings(tmp_path, {"download_dir": r"D:\Müzik Ü"}, ensure_ascii=True)
    assert harness(path) == r"D:\Müzik Ü"


def test_a_lookalike_key_or_value_is_not_the_setting(tmp_path, harness):
    path = _settings(
        tmp_path,
        {"last_download_dir": r"C:\wrong", "note": '"download_dir": "C:\\also wrong"', "download_dir": r"E:\right"},
        ensure_ascii=False,
        indent=2,
    )
    assert harness(path) == r"E:\right"


@pytest.mark.parametrize(
    "content",
    [None, "", "{}", '{"download_dir": ""}', '{"download_dir": null}', '{"download_dir": "C:\\\\a\\nb"}', '{"download_dir": "C:\\\\unterminated'],
)
def test_anything_else_means_no_previous_folder(tmp_path, harness, content):
    path = tmp_path / "settings.json"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    assert harness(path) == ""



# --- closing a running MediaGrab (packaging/close_mediagrab.iss) -------------------

CLOSE_HARNESS = r"""
[Setup]
AppName=MediaGrab close harness
AppVersion=1
CreateAppDir=no
Uninstallable=no
PrivilegesRequired=lowest
OutputDir={out}
OutputBaseFilename=close-harness

[CustomMessages]
MediaGrabRunning=running

[Code]
#include "{include}"

function InitializeSetup(): Boolean;
var
  Lines: TArrayOfString;
begin
  SetArrayLength(Lines, 1);
  if CloseMediaGrab(True) then
    Lines[0] := 'closed'
  else
    Lines[0] := 'still running';
  SaveStringsToUTF8File(ExpandConstant('{param:out}'), Lines, False);
  Result := False;
end;
"""


@pytest.fixture(scope="module")
def close_harness(tmp_path_factory):
    # NOTE: the harness finds MediaGrab by window class, exactly like the
    # installer - with the developer's own MediaGrab running it would close
    # THAT one. Never.
    from mediagrab import tray

    if tray.other_process_window():
        pytest.skip("a real MediaGrab is running on this machine - quit it to run these")
    folder = tmp_path_factory.mktemp("iss-close")
    script = folder / "close.iss"
    script.write_text(
        CLOSE_HARNESS.replace("{out}", str(folder)).replace("{include}", str(ROOT / "packaging" / "close_mediagrab.iss")),
        encoding="utf-8-sig",
    )
    subprocess.run([_iscc(), "-Q", str(script)], check=True, capture_output=True)

    def run():
        out = folder / "result.txt"
        if out.exists():
            out.unlink()
        subprocess.run([str(folder / "close-harness.exe"), "/VERYSILENT", "/SUPPRESSMSGBOXES", f"/out={out}"], timeout=60)
        return out.read_text(encoding="utf-8-sig").strip()

    return run


def test_closes_a_running_mediagrab_through_its_tray_window(close_harness):
    # NOTE: a real tray icon; its on_quit does what run.py does once the
    # server has stopped - removes the icon (and with it the window).
    from mediagrab import tray

    asked = []
    icon = tray.TrayIcon("t", "o", "q", lambda: None, lambda: (asked.append(1), threading.Thread(target=icon.stop).start()))
    assert icon.start()
    try:
        assert close_harness() == "closed"
        assert asked == [1]
    finally:
        icon.stop()


def test_nothing_running_is_nothing_to_close(close_harness):
    assert close_harness() == "closed"


# --- the uninstaller's video clean-up (packaging/uninstall_options.iss) --------------

UNINSTALL_HARNESS = r"""
[Setup]
AppName=MediaGrab uninstall harness
AppVersion=1
CreateAppDir=no
Uninstallable=no
PrivilegesRequired=lowest
OutputDir={out}
OutputBaseFilename=uninstall-harness

[Code]
#include "{include}"

function InitializeSetup(): Boolean;
var
  Lines: TArrayOfString;
  Helper: String;
begin
  SetArrayLength(Lines, 1);
  Helper := ExpandConstant('{param:helperout}');
  if ExpandConstant('{param:cmd}') = 'delete' then
  begin
    if RunUninstallHelper(ExpandConstant('{param:python}'), ExpandConstant('{param:appdir}'), 'delete-downloads', Helper) then
      Lines[0] := 'deleted'
    else
      Lines[0] := 'failed';
  end
  else if ReadDownloadsSummary(ExpandConstant('{param:python}'), ExpandConstant('{param:appdir}'), Helper) then
    Lines[0] := DownloadsFolder + '|' + IntToStr(DownloadsCount) + '|' + SizeText(DownloadsMB)
  else
    Lines[0] := 'no summary';
  SaveStringsToUTF8File(ExpandConstant('{param:out}'), Lines, False);
  Result := False;
end;
"""


@pytest.fixture(scope="module")
def uninstall_harness(tmp_path_factory):
    folder = tmp_path_factory.mktemp("iss-uninstall")
    script = folder / "uninstall.iss"
    script.write_text(
        UNINSTALL_HARNESS.replace("{out}", str(folder)).replace(
            "{include}", str(ROOT / "packaging" / "uninstall_options.iss")
        ),
        encoding="utf-8-sig",
    )
    subprocess.run([_iscc(), "-Q", str(script)], check=True, capture_output=True)

    def run(cmd, data_dir, python=sys.executable):
        out = folder / "result.txt"
        if out.exists():
            out.unlink()
        # NOTE: the real helper (python -m mediagrab.uninstall) run by the
        # Pascal code, against an isolated data folder.
        env = {**os.environ, "MEDIAGRAB_DATA_DIR": str(data_dir)}
        subprocess.run(
            [
                str(folder / "uninstall-harness.exe"), "/VERYSILENT", "/SUPPRESSMSGBOXES",
                f"/cmd={cmd}", f"/python={python}", f"/appdir={ROOT}",
                f"/helperout={folder / 'helper.txt'}", f"/out={out}",
            ],
            timeout=120,
            env=env,
        )
        return out.read_text(encoding="utf-8-sig").strip()

    return run


def _videos(tmp_path):
    videos = tmp_path / "Videolarım Ş"
    (videos / "Kanal").mkdir(parents=True)
    (videos / "Kanal" / "Bir.mp4").write_bytes(b"x" * (3 * 1024 * 1024 + 1))
    (videos / "Kanal" / "Bir.json").write_bytes(b"{}")
    (videos / "kendi-dosyam.docx").write_bytes(b"d")
    data = tmp_path / "data"
    data.mkdir()
    (data / "settings.json").write_text(json.dumps({"download_dir": str(videos)}, ensure_ascii=False), encoding="utf-8")
    return videos, data


def test_the_uninstaller_reads_the_helpers_summary(tmp_path, uninstall_harness):
    videos, data = _videos(tmp_path)
    assert uninstall_harness("summary", data) == f"{videos}|2|4 MB"


def test_the_uninstaller_has_the_helper_delete_only_mediagrabs_files(tmp_path, uninstall_harness):
    videos, data = _videos(tmp_path)
    assert uninstall_harness("delete", data) == "deleted"
    assert not (videos / "Kanal").exists()
    assert (videos / "kendi-dosyam.docx").exists()


def test_no_python_means_no_offer_to_delete_videos(tmp_path, uninstall_harness):
    _videos_dir, data = _videos(tmp_path)
    assert uninstall_harness("summary", data, python=str(tmp_path / "missing" / "python.exe")) == "no summary"


# --- "Install with Docker": docker-compose.yml (packaging/docker_mode.iss) ----------

DOCKER_HARNESS = r"""
[Setup]
AppName=MediaGrab docker harness
AppVersion=1
CreateAppDir=no
Uninstallable=no
PrivilegesRequired=lowest
OutputDir={out}
OutputBaseFilename=docker-harness

[Code]
#include "{include}"

function InitializeSetup(): Boolean;
var
  Secret, Done: TArrayOfString;
begin
  SetArrayLength(Done, 1);
  if ExpandConstant('{param:mode}') = 'new' then
  begin
    LoadStringsFromFile(ExpandConstant('{param:pwfile}'), Secret);
    SaveStringsToUTF8File(ExpandConstant('{param:compose}'),
      DockerComposeLines(ExpandConstant('{param:image}'), Secret[0], ExpandConstant('{param:lanip}')), False);
    Done[0] := 'written';
  end
  else if SetComposeImage(ExpandConstant('{param:compose}'), ExpandConstant('{param:image}')) then
    Done[0] := 'updated'
  else
    Done[0] := 'no image line';
  SaveStringsToUTF8File(ExpandConstant('{param:out}'), Done, False);
  Result := False;
end;
"""

# NOTE: what the old Tk installer (setup_mediagrab.py) wrote - v2.4.0's
# installer has to find and update these in place.
LEGACY_COMPOSE = """services:
  mediagrab:
    image: ghcr.io/umitkrkmz/mediagrab:latest
    container_name: mediagrab
    restart: unless-stopped
    ports:
      - "8420:8420"
    environment:
      - "MEDIAGRAB_INITIAL_PASSWORD=eski parola"
      - "MEDIAGRAB_HOST_LAN_IP=192.168.1.20"
    volumes:
      - ./data/indirilenler:/app/indirilenler
      - ./data/settings.json:/app/settings.json
"""


def _docker_cli():
    return shutil.which("docker")


@pytest.fixture(scope="module")
def docker_harness(tmp_path_factory):
    if not _docker_cli():
        pytest.skip("needs the docker CLI (only its 'compose config' - Docker itself may be stopped)")
    folder = tmp_path_factory.mktemp("iss-docker")
    script = folder / "docker.iss"
    script.write_text(
        DOCKER_HARNESS.replace("{out}", str(folder)).replace("{include}", str(ROOT / "packaging" / "docker_mode.iss")),
        encoding="utf-8-sig",
    )
    subprocess.run([_iscc(), "-Q", str(script)], check=True, capture_output=True)

    def run(compose, mode, image, password="", lanip=""):
        out = folder / "result.txt"
        pwfile = folder / "pw.txt"
        pwfile.write_text(password + "\n", encoding="utf-8-sig")
        args = [str(folder / "docker-harness.exe"), "/VERYSILENT", "/SUPPRESSMSGBOXES", f"/mode={mode}",
                f"/compose={compose}", f"/image={image}", f"/pwfile={pwfile}", f"/lanip={lanip}", f"/out={out}"]
        subprocess.run(args, timeout=60)
        return out.read_text(encoding="utf-8-sig").strip()

    return run


def _compose_config(compose):
    """docker-compose.yml as Docker itself reads it (no daemon needed)."""
    result = subprocess.run(
        [_docker_cli(), "compose", "-f", str(compose), "config", "--format", "json"],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    assert result.returncode == 0, result.stderr
    service = json.loads(result.stdout)["services"]["mediagrab"]
    # NOTE: config prints a literal "$" in its escaped "$$" form.
    env = {k: (v or "").replace("$$", "$") for k, v in service["environment"].items()}
    return service, env


@pytest.mark.parametrize("password", [r'a"b\c#d: e', "şifre ğüİ çok", "pa$word$HOME ${X}", "  boşluklu  "])
def test_a_new_compose_hands_the_password_over_exactly(tmp_path, docker_harness, password):
    compose = tmp_path / "docker-compose.yml"
    assert docker_harness(compose, "new", "ghcr.io/umitkrkmz/mediagrab:2.4.0", password, "192.168.1.20") == "written"
    service, env = _compose_config(compose)
    assert env["MEDIAGRAB_INITIAL_PASSWORD"] == password
    assert env["MEDIAGRAB_HOST_LAN_IP"] == "192.168.1.20"
    assert env["MEDIAGRAB_INSTALLED_BY"] == "windows-installer"
    assert service["image"] == "ghcr.io/umitkrkmz/mediagrab:2.4.0"
    assert service["ports"][0]["published"] == "8420"
    assert len(service["volumes"]) == 6


def test_no_lan_ip_no_lan_ip_line(tmp_path, docker_harness):
    compose = tmp_path / "docker-compose.yml"
    docker_harness(compose, "new", "ghcr.io/umitkrkmz/mediagrab:2.4.0", "parola123", "")
    assert "MEDIAGRAB_HOST_LAN_IP" not in _compose_config(compose)[1]


def test_an_old_installers_compose_is_updated_in_place(tmp_path, docker_harness):
    compose = tmp_path / "docker-compose.yml"
    compose.write_text(LEGACY_COMPOSE, encoding="utf-8")
    assert docker_harness(compose, "update", "ghcr.io/umitkrkmz/mediagrab:2.4.0") == "updated"
    service, env = _compose_config(compose)
    assert service["image"] == "ghcr.io/umitkrkmz/mediagrab:2.4.0"
    assert env["MEDIAGRAB_INITIAL_PASSWORD"] == "eski parola", "the password stays"
    assert env["MEDIAGRAB_HOST_LAN_IP"] == "192.168.1.20"
    assert env["MEDIAGRAB_INSTALLED_BY"] == "windows-installer"
    # NOTE: and only once, however often it's updated.
    docker_harness(compose, "update", "ghcr.io/umitkrkmz/mediagrab:2.4.1")
    assert compose.read_text(encoding="utf-8-sig").count("MEDIAGRAB_INSTALLED_BY") == 1
    assert _compose_config(compose)[0]["image"] == "ghcr.io/umitkrkmz/mediagrab:2.4.1"


def test_a_compose_without_mediagrab_is_left_alone(tmp_path, docker_harness):
    compose = tmp_path / "docker-compose.yml"
    original = "services:\n  other:\n    image: nginx\n"
    compose.write_text(original, encoding="utf-8")
    assert docker_harness(compose, "update", "ghcr.io/umitkrkmz/mediagrab:2.4.0") == "no image line"
    assert compose.read_text(encoding="utf-8") == original


# --- "Install with Docker": finding an existing install (docker_wizard.iss) ---------

DETECT_HARNESS = r"""
[Setup]
AppName=MediaGrab docker detect harness
AppVersion=1
CreateAppDir=no
Uninstallable=no
PrivilegesRequired=lowest
OutputDir={out}
OutputBaseFilename=detect-harness

[Code]
#include "{settings_json}"
#include "{docker_mode}"
#include "{docker_wizard}"

function InitializeSetup(): Boolean;
var
  Lines: TArrayOfString;
  Status: String;
begin
  SetArrayLength(Lines, 1);
  Status := DockerStatus();
  if Status = 'ready' then
    DetectExistingDocker(ExpandConstant('{param:container}'), ExpandConstant('{param:default}'), '');
  Lines[0] := Status + '|' + ExistingDockerFolder + '|' + ExistingDockerVersion + '|' + ExistingDockerState;
  SaveStringsToUTF8File(ExpandConstant('{param:out}'), Lines, False);
  Result := False;
end;
"""

LOCAL_IMAGE = "ghcr.io/umitkrkmz/mediagrab:latest"


def _docker_ready_with_image():
    docker = _docker_cli()
    if not docker:
        return False
    ok = subprocess.run([docker, "image", "inspect", LOCAL_IMAGE], capture_output=True, timeout=60).returncode == 0
    return ok


@pytest.fixture(scope="module")
def detect_harness(tmp_path_factory):
    if not _docker_ready_with_image():
        pytest.skip(f"needs Docker running with {LOCAL_IMAGE} already pulled")
    folder = tmp_path_factory.mktemp("iss-detect")
    script = folder / "detect.iss"
    text = DETECT_HARNESS.replace("{out}", str(folder))
    for name in ("settings_json", "docker_mode", "docker_wizard"):
        text = text.replace("{" + name + "}", str(ROOT / "packaging" / f"{name}.iss"))
    script.write_text(text, encoding="utf-8-sig")
    subprocess.run([_iscc(), "-Q", str(script)], check=True, capture_output=True)

    def run(container, default_folder):
        out = folder / "result.txt"
        if out.exists():
            out.unlink()
        subprocess.run([str(folder / "detect-harness.exe"), "/VERYSILENT", "/SUPPRESSMSGBOXES",
                        f"/container={container}", f"/default={default_folder}", f"/out={out}"], timeout=180)
        return out.read_text(encoding="utf-8-sig").strip().split("|")

    return run


@pytest.fixture
def test_container(tmp_path):
    """A compose project of our own - never the user's real "mediagrab"."""
    name = f"mediagrab-test-{os.getpid()}"
    project = tmp_path / "Docker Klasörü"
    project.mkdir()
    (project / "docker-compose.yml").write_text(
        "services:\n"
        "  mediagrab:\n"
        f"    image: {LOCAL_IMAGE}\n"
        f"    container_name: {name}\n"
        "    entrypoint: [\"sleep\", \"300\"]\n",
        encoding="utf-8",
    )
    docker = _docker_cli()

    def compose(*args):
        subprocess.run([docker, "compose", *args], cwd=project, capture_output=True, timeout=120, check=True)

    yield name, project, compose
    subprocess.run([docker, "compose", "down"], cwd=project, capture_output=True, timeout=120)


def test_finds_a_stopped_install_its_folder_and_version(detect_harness, test_container, tmp_path):
    name, project, compose = test_container
    compose("create")
    status, folder, version, state = detect_harness(name, tmp_path / "nowhere")
    assert status == "ready"
    assert Path(folder) == project, "the folder comes from compose's own label"
    assert state == "created"
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), version


def test_finds_a_running_install(detect_harness, test_container, tmp_path):
    name, project, compose = test_container
    compose("up", "-d")
    status, folder, version, state = detect_harness(name, tmp_path / "nowhere")
    assert (Path(folder), state) == (project, "running")
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), version


def test_a_compose_file_in_the_default_folder_counts_without_a_container(detect_harness, tmp_path):
    default = tmp_path / "MediaGrab"
    default.mkdir()
    (default / "docker-compose.yml").write_text(LEGACY_COMPOSE, encoding="utf-8")
    status, folder, version, state = detect_harness(f"no-such-container-{os.getpid()}", default)
    assert (Path(folder), version, state) == (default, "", "")


def test_nothing_installed_is_a_new_install(detect_harness, tmp_path):
    assert detect_harness(f"no-such-container-{os.getpid()}", tmp_path / "nowhere")[1:] == ["", "", ""]
