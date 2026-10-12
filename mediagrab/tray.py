"""MediaGrab's notification-area (system tray) icon - Windows installer only.

Started by run.py when MediaGrab runs from the Windows installer (pythonw.exe,
no console window): without a console, this icon is how the user sees that
MediaGrab is running and how they stop it.

  left click / "Open MediaGrab"  -> opens the browser
  "Quit MediaGrab"               -> stops the server, removes the icon

NOTE: written with plain ctypes against the Win32 API (Shell_NotifyIconW, a
hidden window and a popup menu) instead of pystray, which would have brought
Pillow and six into the package; the icon comes from mediagrab.ico.

NOTE: the hidden window is a real top-level window (not a message-only one)
with a fixed class name, TRAY_WINDOW_CLASS, on purpose:
  - the installer and uninstaller find it by that name and send WM_CLOSE, so
    MediaGrab shuts down cleanly before its files are replaced or removed -
    no network "shutdown" endpoint needed (packaging/mediagrab.iss);
  - Windows' log-off / shutdown messages reach it, so the server stops
    properly then too.
"""

import ctypes
import os
import threading
from ctypes import wintypes
from typing import Callable, Optional

# NOTE: shared with packaging/mediagrab.iss (FindWindowByClassName) - a test
# keeps the two in step.
TRAY_WINDOW_CLASS = "MediaGrabTrayWindow"

WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_QUERYENDSESSION = 0x0011
WM_ENDSESSION = 0x0016
WM_NULL = 0x0000
WM_COMMAND = 0x0111
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
WM_CONTEXTMENU = 0x007B
WM_APP = 0x8000
WM_TRAY_CALLBACK = WM_APP + 1
# NOTE: "remove the icon and stop" from run.py's own thread - kept apart from
# WM_CLOSE, which means "someone asks MediaGrab to quit" (the installer).
WM_TRAY_STOP = WM_APP + 2

NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP = 0x1, 0x2, 0x4
MF_STRING, MF_SEPARATOR = 0x0, 0x800
TPM_RIGHTBUTTON, TPM_RETURNCMD, TPM_NONOTIFY = 0x2, 0x100, 0x80
IMAGE_ICON, LR_LOADFROMFILE = 1, 0x10
SM_CXSMICON, SM_CYSMICON = 49, 50
IDI_APPLICATION = 32512

ID_OPEN = 1
ID_QUIT = 2

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", ctypes.c_byte * 16),
        ("hBalloonIcon", wintypes.HICON),
    ]


def _api():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.DefWindowProcW.restype = LRESULT
    user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
    user32.RegisterClassW.restype = wintypes.ATOM
    user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD] + [
        ctypes.c_int
    ] * 4 + [wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
    user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.restype = LRESULT
    user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.LoadIconW.argtypes = [wintypes.HINSTANCE, wintypes.LPVOID]
    user32.LoadIconW.restype = wintypes.HICON
    user32.CreatePopupMenu.restype = wintypes.HMENU
    user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
    user32.SetMenuDefaultItem.argtypes = [wintypes.HMENU, wintypes.UINT, wintypes.UINT]
    user32.TrackPopupMenu.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.LPVOID]
    user32.DestroyMenu.argtypes = [wintypes.HMENU]
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.DestroyIcon.argtypes = [wintypes.HICON]
    user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
    user32.RegisterWindowMessageW.restype = wintypes.UINT
    shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
    shell32.Shell_NotifyIconW.restype = wintypes.BOOL
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HMODULE
    return user32, shell32, kernel32


class TrayIcon:
    """The icon, its hidden window and the message loop, on their own thread."""

    def __init__(
        self,
        tooltip: str,
        open_label: str,
        quit_label: str,
        on_open: Callable[[], None],
        on_quit: Callable[[], None],
        icon_path: Optional[str] = None,
    ):
        self.tooltip = tooltip[:127]
        self.open_label = open_label
        self.quit_label = quit_label
        self.on_open = on_open
        self.on_quit = on_quit
        self.icon_path = icon_path
        self.hwnd = None
        self.added = False
        self._ready = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._quit_requested = False

    # --- lifecycle (called from run.py's thread) -------------------------------

    def start(self, timeout: float = 5.0) -> bool:
        """Start the icon's thread; True once the icon is in the tray."""
        global _running
        self._thread = threading.Thread(target=self._run, name="mediagrab-tray", daemon=True)
        self._thread.start()
        self._ready.wait(timeout)
        _running = self
        return self.added

    def stop(self, timeout: float = 5.0) -> None:
        """Remove the icon and end its thread (safe to call more than once)."""
        global _running
        if self.hwnd and self._thread and self._thread.is_alive():
            self._user32.PostMessageW(self.hwnd, WM_TRAY_STOP, 0, 0)
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout)
        if _running is self:
            _running = None

    # --- the icon's own thread ----------------------------------------------------

    def _run(self) -> None:
        self._user32, self._shell32, kernel32 = _api()
        hinstance = kernel32.GetModuleHandleW(None)
        _register_class(self._user32, hinstance)
        self.hwnd = self._user32.CreateWindowExW(0, TRAY_WINDOW_CLASS, "MediaGrab", 0, 0, 0, 0, 0, None, None, hinstance, None)
        if not self.hwnd:
            self._ready.set()
            return
        _WINDOWS[self.hwnd] = self
        self._taskbar_created = self._user32.RegisterWindowMessageW("TaskbarCreated")
        self._hicon = self._load_icon()
        self.added = self._notify(NIM_ADD)
        self._ready.set()
        msg = wintypes.MSG()
        while self._user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            self._user32.TranslateMessage(ctypes.byref(msg))
            self._user32.DispatchMessageW(ctypes.byref(msg))

    def _load_icon(self):
        if self.icon_path and os.path.isfile(self.icon_path):
            cx = self._user32.GetSystemMetrics(SM_CXSMICON)
            cy = self._user32.GetSystemMetrics(SM_CYSMICON)
            handle = self._user32.LoadImageW(None, self.icon_path, IMAGE_ICON, cx, cy, LR_LOADFROMFILE)
            if handle:
                return handle
        # NOTE: a missing .ico (antivirus, a broken copy) still gets an icon.
        return self._user32.LoadIconW(None, ctypes.c_void_p(IDI_APPLICATION))

    def _notify(self, action: int) -> bool:
        data = NOTIFYICONDATAW()
        data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        data.hWnd = self.hwnd
        data.uID = 1
        data.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        data.uCallbackMessage = WM_TRAY_CALLBACK
        data.hIcon = self._hicon
        data.szTip = self.tooltip
        return bool(self._shell32.Shell_NotifyIconW(action, ctypes.byref(data)))

    def _show_menu(self) -> None:
        menu = self._user32.CreatePopupMenu()
        self._user32.AppendMenuW(menu, MF_STRING, ID_OPEN, self.open_label)
        self._user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        self._user32.AppendMenuW(menu, MF_STRING, ID_QUIT, self.quit_label)
        self._user32.SetMenuDefaultItem(menu, ID_OPEN, 0)
        point = wintypes.POINT()
        self._user32.GetCursorPos(ctypes.byref(point))
        # NOTE: Microsoft's documented dance - without the foreground call
        # the menu doesn't close when clicking elsewhere, and the WM_NULL
        # afterwards stops it from closing straight away the next time.
        self._user32.SetForegroundWindow(self.hwnd)
        command = self._user32.TrackPopupMenu(
            menu, TPM_RIGHTBUTTON | TPM_RETURNCMD | TPM_NONOTIFY, point.x, point.y, 0, self.hwnd, None
        )
        self._user32.PostMessageW(self.hwnd, WM_NULL, 0, 0)
        self._user32.DestroyMenu(menu)
        if command:
            self._command(command)

    def _command(self, command: int) -> None:
        if command == ID_OPEN:
            self.on_open()
        elif command == ID_QUIT:
            self._request_quit()

    def _request_quit(self) -> None:
        # NOTE: only asks; run.py stops the server and then calls stop(),
        # which is what removes the icon.
        if not self._quit_requested:
            self._quit_requested = True
            self.on_quit()

    def _window_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAY_CALLBACK:
            event = lparam & 0xFFFF
            if event == WM_LBUTTONUP:
                self.on_open()
            elif event in (WM_RBUTTONUP, WM_CONTEXTMENU):
                self._show_menu()
            return 0
        if msg == WM_COMMAND:
            self._command(wparam & 0xFFFF)
            return 0
        if msg in (WM_CLOSE, WM_ENDSESSION):
            # NOTE: the installer/uninstaller (WM_CLOSE) or Windows logging
            # off - stop the server the same way the menu's Quit does.
            if msg == WM_CLOSE or wparam:
                self._request_quit()
            return 0
        if msg == WM_QUERYENDSESSION:
            return 1
        if msg == WM_TRAY_STOP:
            if self.added:
                self._notify(NIM_DELETE)
                self.added = False
            self._user32.DestroyWindow(hwnd)
            return 0
        if msg == WM_DESTROY:
            _WINDOWS.pop(hwnd, None)
            self._user32.PostQuitMessage(0)
            return 0
        if msg == getattr(self, "_taskbar_created", None):
            # NOTE: Explorer restarted (crash, update) - its new taskbar
            # knows nothing of us until the icon is added again.
            self.added = self._notify(NIM_ADD)
            return 0
        return self._user32.DefWindowProcW(hwnd, msg, wparam, lparam)


_running: Optional[TrayIcon] = None


def remove_running_icon() -> None:
    """Take this process's icon out of the tray, if it has one.

    NOTE: for app.py's restart after an update (os.execv): the old process
    ends without any cleanup, which would leave a dead icon in the tray until
    the mouse passes over it - next to the new process's live one.
    """
    if _running is not None:
        _running.stop()


# NOTE: a window class is registered once per process, with one window
# procedure - which then finds the TrayIcon a message belongs to by its
# window handle (only one in MediaGrab itself; several in the tests).
_WINDOWS: dict = {}
_class_lock = threading.Lock()
_class_proc = None


def _dispatch(hwnd, msg, wparam, lparam):
    icon = _WINDOWS.get(hwnd)
    if icon is not None:
        return icon._window_proc(hwnd, msg, wparam, lparam)
    # NOTE: messages sent while CreateWindowExW is still running, before
    # the handle is known.
    return _api_user32().DefWindowProcW(hwnd, msg, wparam, lparam)


def _api_user32():
    global _default_user32
    if _default_user32 is None:
        _default_user32 = _api()[0]
    return _default_user32


_default_user32 = None


def _register_class(user32, hinstance) -> None:
    global _class_proc
    with _class_lock:
        if _class_proc is not None:
            return
        _class_proc = WNDPROC(_dispatch)  # NOTE: must stay referenced
        wc = WNDCLASSW()
        wc.lpfnWndProc = _class_proc
        wc.hInstance = hinstance
        wc.lpszClassName = TRAY_WINDOW_CLASS
        user32.RegisterClassW(ctypes.byref(wc))


def other_process_window() -> bool:
    """True if ANOTHER process already has a MediaGrab tray window.

    NOTE: for the tests - the installer finds the window by class name, so
    with the user's real MediaGrab running a test could find (and close!)
    that one instead of its own.
    """
    user32 = _api_user32()
    user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    user32.FindWindowW.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    hwnd = user32.FindWindowW(TRAY_WINDOW_CLASS, None)
    if not hwnd:
        return False
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value != os.getpid()
