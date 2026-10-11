"""Windows' modern "Select folder" dialog, run as its own small process.

    python -I folder_picker.py      (title/start folder in MEDIAGRAB_PICKER_*)

Prints the chosen folder (UTF-8) on stdout, or nothing if cancelled.

NOTE: this is the Explorer-style IFileOpenDialog in folder mode (address bar,
Quick access, search) - not the old SHBrowseForFolder tree that PowerShell's
FolderBrowserDialog shows. Called through raw COM vtables with ctypes, so no
PowerShell, no C# compiled on the fly and no new dependency.

NOTE: deliberately a separate process (app.py starts it) instead of running
inside the server: COM wants an STA thread with a message loop, and a modal
dialog stuck in a server thread pool would be far harder to get rid of than
a child process. This file must not import mediagrab - it runs on its own.
"""

import ctypes
import os
import sys
from ctypes import wintypes

CLSID_FileOpenDialog = "{DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7}"
IID_IFileOpenDialog = "{D57C7288-D4AD-4768-BE02-9D969532D960}"
IID_IShellItem = "{43826D1E-E718-42EE-BC55-A1E261C37BFE}"

CLSCTX_INPROC_SERVER = 0x1
COINIT_APARTMENTTHREADED = 0x2
FOS_PICKFOLDERS = 0x20
FOS_FORCEFILESYSTEM = 0x40
SIGDN_FILESYSPATH = 0x80058000
WS_POPUP = 0x80000000
WS_EX_TOPMOST = 0x8
WS_EX_TOOLWINDOW = 0x80

# NOTE: vtable slots (IUnknown 0-2, IModalWindow 3, IFileDialog 4-26).
_SHOW = 3
_SET_OPTIONS = 9
_GET_OPTIONS = 10
_SET_FOLDER = 12
_SET_TITLE = 17
_GET_RESULT = 20
_RELEASE = 2
_ITEM_GET_DISPLAY_NAME = 5


class GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]


def _guid(text):
    guid = GUID()
    ctypes.oledll.ole32.CLSIDFromString(ctypes.c_wchar_p(text), ctypes.byref(guid))
    return guid


def _method(obj, slot, *argtypes, restype=ctypes.HRESULT):
    """Method number `slot` of a COM object's vtable, ready to call.

    NOTE: restype HRESULT makes ctypes raise OSError for any failure code.
    """
    vtable = ctypes.cast(obj, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    return ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(vtable[slot])


def _release(obj):
    _method(obj, _RELEASE, restype=wintypes.ULONG)(obj)


def _owner_window():
    # NOTE: the server isn't the foreground app (the browser is), so a plain
    # dialog would open BEHIND the browser. Owned by a hidden topmost window,
    # it opens on top - the same trick the old PowerShell version used.
    user32 = ctypes.windll.user32
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD] + [ctypes.c_int] * 4 + [wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
    return user32.CreateWindowExW(WS_EX_TOPMOST | WS_EX_TOOLWINDOW, "STATIC", "", WS_POPUP, 0, 0, 0, 0, None, None, None, None)


def pick_folder(title="", start=""):
    """Show the dialog; return the chosen folder or None if cancelled."""
    ole32 = ctypes.oledll.ole32
    ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
    out = ctypes.POINTER(ctypes.c_void_p)
    dialog = ctypes.c_void_p()
    ole32.CoCreateInstance(
        ctypes.byref(_guid(CLSID_FileOpenDialog)), None, CLSCTX_INPROC_SERVER, ctypes.byref(_guid(IID_IFileOpenDialog)), ctypes.byref(dialog)
    )
    try:
        options = wintypes.DWORD()
        _method(dialog, _GET_OPTIONS, ctypes.POINTER(wintypes.DWORD))(dialog, ctypes.byref(options))
        _method(dialog, _SET_OPTIONS, wintypes.DWORD)(dialog, options.value | FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM)
        if title:
            _method(dialog, _SET_TITLE, wintypes.LPCWSTR)(dialog, title)
        if start and os.path.isdir(start):
            folder = ctypes.c_void_p()
            try:
                ctypes.oledll.shell32.SHCreateItemFromParsingName(
                    wintypes.LPCWSTR(start), None, ctypes.byref(_guid(IID_IShellItem)), ctypes.byref(folder)
                )
                _method(dialog, _SET_FOLDER, ctypes.c_void_p)(dialog, folder)
                _release(folder)
            except OSError:
                pass  # NOTE: just opens wherever Windows last left it
        # NOTE: a cancel comes back as the failing HRESULT ERROR_CANCELLED.
        try:
            _method(dialog, _SHOW, wintypes.HWND)(dialog, _owner_window())
        except OSError:
            return None
        item = ctypes.c_void_p()
        _method(dialog, _GET_RESULT, out)(dialog, ctypes.byref(item))
        try:
            name = ctypes.c_void_p()
            _method(item, _ITEM_GET_DISPLAY_NAME, wintypes.DWORD, out)(item, SIGDN_FILESYSPATH, ctypes.byref(name))
            path = ctypes.wstring_at(name.value)
            ctypes.windll.ole32.CoTaskMemFree(name)
        finally:
            _release(item)
        return path
    finally:
        _release(dialog)


if __name__ == "__main__":
    chosen = pick_folder(os.environ.get("MEDIAGRAB_PICKER_TITLE", ""), os.environ.get("MEDIAGRAB_PICKER_START", ""))
    if chosen:
        sys.stdout.buffer.write(chosen.encode("utf-8"))
