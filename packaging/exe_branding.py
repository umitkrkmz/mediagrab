"""Makes MediaGrab.exe out of the embedded Python's pythonw.exe (build time, Windows).

    python packaging/exe_branding.py <pythonw.exe> <MediaGrab.exe> <icon.ico> <version>

Why: Task Manager names a process by its exe's version info - "Python" for
pythonw.exe - so MediaGrab showed up there as "Python" with the Python logo.
The copy gets MediaGrab's name and icon; it is otherwise the same program.

What changes in the copy, and only there (pythonw.exe stays as it was):
  - the version info: FileDescription/ProductName "MediaGrab"; the original
    copyright line is kept and Comments says what the file really is;
  - the icons: MediaGrab's instead of Python's;
  - the Authenticode signature is REMOVED - any edit would break the
    python.org signature, and a broken one looks worse to antivirus than
    none at all. (Checked on VirusTotal before shipping, see ROADMAP.)
Every other resource - above all the manifest (DPI awareness, long paths,
supported Windows versions) - is copied over unchanged.

Uses only the Win32 resource API through ctypes (BeginUpdateResourceW ...);
no rcedit or other tool to download.
"""

import ctypes
import os
import shutil
import struct
import sys
from ctypes import wintypes

RT_ICON, RT_GROUP_ICON, RT_VERSION = 3, 14, 16
LANG_EN_US = 0x0409
LOAD_LIBRARY_AS_DATAFILE = 0x2
LOAD_LIBRARY_AS_IMAGE_RESOURCE = 0x20

_k32 = ctypes.WinDLL("kernel32", use_last_error=True) if os.name == "nt" else None


def _setup_api():
    k = _k32
    k.LoadLibraryExW.argtypes = [wintypes.LPCWSTR, wintypes.HANDLE, wintypes.DWORD]
    k.LoadLibraryExW.restype = wintypes.HMODULE
    k.FreeLibrary.argtypes = [wintypes.HMODULE]
    k.FindResourceExW.argtypes = [wintypes.HMODULE, ctypes.c_void_p, ctypes.c_void_p, wintypes.WORD]
    k.FindResourceExW.restype = wintypes.HRSRC
    k.LoadResource.argtypes = [wintypes.HMODULE, wintypes.HRSRC]
    k.LoadResource.restype = wintypes.HGLOBAL
    k.LockResource.argtypes = [wintypes.HGLOBAL]
    k.LockResource.restype = ctypes.c_void_p
    k.SizeofResource.argtypes = [wintypes.HMODULE, wintypes.HRSRC]
    k.SizeofResource.restype = wintypes.DWORD
    k.EnumResourceTypesW.argtypes = [wintypes.HMODULE, ctypes.c_void_p, ctypes.c_ssize_t]
    k.EnumResourceNamesW.argtypes = [wintypes.HMODULE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ssize_t]
    k.EnumResourceLanguagesW.argtypes = [wintypes.HMODULE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ssize_t]
    k.BeginUpdateResourceW.argtypes = [wintypes.LPCWSTR, wintypes.BOOL]
    k.BeginUpdateResourceW.restype = wintypes.HANDLE
    k.UpdateResourceW.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, wintypes.WORD, ctypes.c_void_p, wintypes.DWORD]
    k.EndUpdateResourceW.argtypes = [wintypes.HANDLE, wintypes.BOOL]


_TYPEPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMODULE, ctypes.c_void_p, ctypes.c_ssize_t) if os.name == "nt" else None
_NAMEPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMODULE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ssize_t) if os.name == "nt" else None
_LANGPROC = (
    ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMODULE, ctypes.c_void_p, ctypes.c_void_p, wintypes.WORD, ctypes.c_ssize_t)
    if os.name == "nt"
    else None
)


def _resource_id(value):
    """An integer resource ID stays an int; a named one becomes its string."""
    return value if value < 0x10000 else ctypes.wstring_at(value)


def _as_param(rid):
    return ctypes.c_void_p(rid) if isinstance(rid, int) else ctypes.cast(ctypes.c_wchar_p(rid), ctypes.c_void_p)


def read_resources(path: str) -> list[tuple]:
    """Every resource in an exe as (type, name, language, bytes)."""
    _setup_api()
    module = _k32.LoadLibraryExW(path, None, LOAD_LIBRARY_AS_DATAFILE | LOAD_LIBRARY_AS_IMAGE_RESOURCE)
    if not module:
        raise ctypes.WinError(ctypes.get_last_error())
    found = []

    def on_lang(hmod, rtype, rname, lang, _param):
        found.append((_resource_id(rtype), _resource_id(rname), lang))
        return True

    def on_name(hmod, rtype, rname, _param):
        _k32.EnumResourceLanguagesW(hmod, rtype, rname, lang_cb, 0)
        return True

    def on_type(hmod, rtype, _param):
        _k32.EnumResourceNamesW(hmod, rtype, name_cb, 0)
        return True

    lang_cb, name_cb, type_cb = _LANGPROC(on_lang), _NAMEPROC(on_name), _TYPEPROC(on_type)
    try:
        _k32.EnumResourceTypesW(module, type_cb, 0)
        result = []
        for rtype, rname, lang in found:
            handle = _k32.FindResourceExW(module, _as_param(rtype), _as_param(rname), lang)
            data = ctypes.string_at(_k32.LockResource(_k32.LoadResource(module, handle)), _k32.SizeofResource(module, handle))
            result.append((rtype, rname, lang, data))
        return result
    finally:
        _k32.FreeLibrary(module)


# --- VS_VERSIONINFO -------------------------------------------------------------------


def _pad4(data: bytes) -> bytes:
    return data + b"\0" * (-len(data) % 4)


def _node(key: str, value: bytes = b"", text: bool = False, children: bytes = b"") -> bytes:
    """One VS_VERSIONINFO-style block: header, key, value, children (4-byte aligned)."""
    head = _pad4(struct.pack("<HHH", 0, 0, 1 if text else 0) + (key + "\0").encode("utf-16-le"))
    body = _pad4(head + value) + children
    value_length = len(value) // 2 if text else len(value)
    return struct.pack("<HH", len(body), value_length) + body[4:]


def _version_tuple(version: str) -> tuple:
    parts = [int(p) for p in version.split("-")[0].split(".")[:4] if p.isdigit()]
    return tuple((parts + [0, 0, 0, 0])[:4])


def version_info(version: str, strings: dict) -> bytes:
    a, b, c, d = _version_tuple(version)
    fixed = struct.pack(
        "<13I",
        0xFEEF04BD, 0x00010000,
        (a << 16) | b, (c << 16) | d,  # file version
        (a << 16) | b, (c << 16) | d,  # product version
        0x3F, 0, 0x00040004, 1, 0, 0, 0,  # flags mask, flags, VOS_NT_WINDOWS32, VFT_APP
    )
    table = b"".join(_pad4(_node(k, (v + "\0").encode("utf-16-le"), text=True)) for k, v in strings.items())
    string_info = _node("StringFileInfo", text=True, children=_node("040904B0", text=True, children=table))
    var_info = _node("VarFileInfo", text=True, children=_node("Translation", struct.pack("<HH", LANG_EN_US, 1200)))
    return _node("VS_VERSION_INFO", fixed, children=_pad4(string_info) + var_info)


# --- icons ------------------------------------------------------------------------------


def icon_resources(ico_path: str) -> list[tuple]:
    """An .ico file as RT_ICON entries 1..n plus one RT_GROUP_ICON (ID 1)."""
    with open(ico_path, "rb") as f:
        data = f.read()
    _reserved, _type, count = struct.unpack_from("<HHH", data, 0)
    group = struct.pack("<HHH", 0, 1, count)
    entries = []
    for i in range(count):
        width, height, colors, reserved, planes, bits, size, offset = struct.unpack_from("<BBBBHHII", data, 6 + 16 * i)
        entries.append((RT_ICON, i + 1, LANG_EN_US, data[offset:offset + size]))
        group += struct.pack("<BBBBHHIH", width, height, colors, reserved, planes, bits, size, i + 1)
    return entries + [(RT_GROUP_ICON, 1, LANG_EN_US, group)]


# --- signature ----------------------------------------------------------------------------


def strip_signature(path: str) -> bool:
    """Remove the Authenticode signature (the PE "security" directory)."""
    with open(path, "r+b") as f:
        data = bytearray(f.read())
        pe = struct.unpack_from("<I", data, 0x3C)[0]
        if data[pe:pe + 4] != b"PE\0\0":
            raise ValueError("not a PE file")
        optional = pe + 24
        magic = struct.unpack_from("<H", data, optional)[0]
        directories = optional + (112 if magic == 0x20B else 96)
        security = directories + 4 * 8
        offset, size = struct.unpack_from("<II", data, security)
        if not size:
            return False
        struct.pack_into("<II", data, security, 0, 0)
        # NOTE: the certificate table sits at the very end of a signed file.
        if offset + size >= len(data) - 8:
            del data[offset:]
        f.seek(0)
        f.write(data)
        f.truncate()
    return True


# --- putting it together ---------------------------------------------------------------------


def brand(pythonw: str, target: str, ico: str, version: str) -> None:
    shutil.copy2(pythonw, target)
    strip_signature(target)
    kept = [r for r in read_resources(target) if r[0] not in (RT_ICON, RT_GROUP_ICON, RT_VERSION)]
    original = next((r for r in read_resources(pythonw) if r[0] == RT_VERSION), None)
    copyright_line = _string_from_version(original[3], "LegalCopyright") if original else ""
    python_version = (_string_from_version(original[3], "FileVersion") if original else "") or "3"
    strings = {
        "CompanyName": "umitkrkmz",
        "FileDescription": "MediaGrab",
        "FileVersion": version,
        "InternalName": "MediaGrab",
        "LegalCopyright": copyright_line or "Python Software Foundation",
        "OriginalFilename": "MediaGrab.exe",
        "ProductName": "MediaGrab",
        "ProductVersion": version,
        "Comments": f"pythonw.exe of Python {python_version} (Python Software Foundation), renamed and re-iconed for MediaGrab - github.com/umitkrkmz/mediagrab",
    }
    resources = kept + icon_resources(ico) + [(RT_VERSION, 1, LANG_EN_US, version_info(version, strings))]
    _setup_api()
    handle = _k32.BeginUpdateResourceW(target, True)  # NOTE: True = start from none
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    buffers = []
    for rtype, rname, lang, data in resources:
        buf = ctypes.create_string_buffer(data, len(data))
        buffers.append(buf)
        if not _k32.UpdateResourceW(handle, _as_param(rtype), _as_param(rname), lang, buf, len(data)):
            _k32.EndUpdateResourceW(handle, True)
            raise ctypes.WinError(ctypes.get_last_error())
    if not _k32.EndUpdateResourceW(handle, False):
        raise ctypes.WinError(ctypes.get_last_error())


def _string_from_version(block: bytes, key: str) -> str:
    """One value out of a VS_VERSIONINFO block (good enough for reading one string)."""
    needle = (key + "\0").encode("utf-16-le")
    start = block.find(needle)
    if start < 0:
        return ""
    start += len(needle)
    start += -start % 4
    end = block.find(b"\0\0", start)
    while end != -1 and (end - start) % 2:
        end = block.find(b"\0\0", end + 1)
    return block[start:end].decode("utf-16-le") if end != -1 else ""


if __name__ == "__main__":
    brand(*sys.argv[1:5])
