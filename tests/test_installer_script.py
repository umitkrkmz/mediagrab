"""The Inno Setup installer's own logic, run through real ISCC.

NOTE: Windows + Inno Setup 6 only (skipped elsewhere, e.g. Linux CI). A tiny
harness setup includes packaging/settings_json.iss, runs one function in
InitializeSetup, writes the result and exits before any wizard is shown -
nothing is installed. Set MEDIAGRAB_ISCC to point at another ISCC.exe.
"""

import json
import threading
import os
import subprocess
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
