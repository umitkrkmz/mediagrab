"""MediaGrab.exe built from pythonw.exe (packaging/exe_branding.py).

NOTE: Windows only. Brands a copy of this machine's own pythonw.exe in a temp
folder; the "it still runs" check needs the embedded build staged by
packaging/build_windows.py and is skipped without it.
"""

import ctypes
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows exe resources")

ROOT = Path(__file__).parent.parent
ICON = ROOT / "packaging" / "mediagrab.ico"
STAGED_PYTHON = ROOT / "build" / "windows" / "MediaGrab" / "python"
sys.path.insert(0, str(ROOT / "packaging"))

import exe_branding  # noqa: E402


def _base_pythonw() -> str:
    path = os.path.join(sys.base_prefix, "pythonw.exe")
    if not os.path.isfile(path):
        pytest.skip("no pythonw.exe next to the base interpreter")
    return path


def _version_string(exe: str, key: str) -> str:
    """Read a version string the way Windows itself (and Task Manager) does."""
    version = ctypes.windll.version
    size = version.GetFileVersionInfoSizeW(exe, None)
    assert size, "Windows can't find a version block at all"
    buf = ctypes.create_string_buffer(size)
    assert version.GetFileVersionInfoW(exe, 0, size, buf)
    value, length = ctypes.c_void_p(), ctypes.c_uint()
    # NOTE: the language/codepage the strings are stored under, as listed in
    # \VarFileInfo\Translation - what Explorer and Task Manager look up too.
    assert version.VerQueryValueW(buf, "\\VarFileInfo\\Translation", ctypes.byref(value), ctypes.byref(length))
    lang, codepage = struct.unpack("<HH", ctypes.string_at(value.value, 4))
    if not version.VerQueryValueW(
        buf, f"\\StringFileInfo\\{lang:04X}{codepage:04X}\\{key}", ctypes.byref(value), ctypes.byref(length)
    ):
        return ""
    return ctypes.wstring_at(value.value, length.value).rstrip("\0")


@pytest.fixture
def branded(tmp_path):
    target = tmp_path / "MediaGrab.exe"
    exe_branding.brand(_base_pythonw(), str(target), str(ICON), "2.4.0")
    return str(target)


def test_windows_reads_mediagrabs_name(branded):
    # NOTE: FileDescription is what Task Manager shows as the process name.
    assert _version_string(branded, "FileDescription") == "MediaGrab"
    assert _version_string(branded, "ProductName") == "MediaGrab"
    assert _version_string(branded, "OriginalFilename") == "MediaGrab.exe"
    assert "Python Software Foundation" in _version_string(branded, "LegalCopyright")
    assert "pythonw.exe of Python" in _version_string(branded, "Comments")


def test_the_original_is_untouched(branded):
    assert _version_string(_base_pythonw(), "FileDescription") == "Python"


def test_the_signature_is_removed_not_broken(branded):
    # NOTE: a signature left behind after editing would read as tampered.
    with open(branded, "rb") as f:
        data = f.read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    optional = pe + 24
    directories = optional + (112 if struct.unpack_from("<H", data, optional)[0] == 0x20B else 96)
    assert struct.unpack_from("<II", data, directories + 32) == (0, 0)


def test_mediagrabs_icon_and_the_manifest(branded):
    resources = exe_branding.read_resources(branded)
    icons = [r for r in resources if r[0] == exe_branding.RT_ICON]
    with open(ICON, "rb") as f:
        assert len(icons) == struct.unpack_from("<H", f.read(6), 4)[0]
    original = {(t, n): d for t, n, _l, d in exe_branding.read_resources(_base_pythonw())}
    copy = {(t, n): d for t, n, _l, d in resources}
    manifests = [k for k in original if k[0] == 24]
    assert manifests and all(copy[k] == original[k] for k in manifests), "the manifest must survive unchanged"


@pytest.mark.skipif(not (STAGED_PYTHON / "pythonw.exe").is_file(), reason="needs packaging/build_windows.py's staged build")
def test_the_branded_exe_still_runs_the_embedded_python(tmp_path):
    folder = tmp_path / "python"
    folder.mkdir()
    for item in STAGED_PYTHON.iterdir():
        if item.is_file() and (item.suffix in (".dll", ".zip", "._pth") or item.name == "pythonw.exe"):
            shutil.copy2(item, folder)
    exe_branding.brand(str(folder / "pythonw.exe"), str(folder / "MediaGrab.exe"), str(ICON), "2.4.0")
    result = subprocess.run(
        [str(folder / "MediaGrab.exe"), "-c", "import sys; sys.stdout.write(sys.version.split()[0])"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("3.")
