"""MediaGrab kurulum aracı.

Git ve Python'un sistemde kurulu olup olmadığını kontrol eder (kurmaz -
eksikse resmi indirme sayfasına yönlendirir), sonra bu programın bulunduğu
klasöre MediaGrab'ı klonlar, bir sanal ortam oluşturur ve bağımlılıkları
kurar. Zaten kuruluysa güncelleyebilir (mümkünse `git pull`, değilse temiz
kurulum) ya da kaldırabilir - her durumda `indirilenler/` ve `channels.json`
dokunulmadan korunur.

PyInstaller ile derlenip GitHub Release'e eklenmek üzere tasarlandı (bkz.
setup_mediagrab.spec); `python setup_mediagrab.py` ile kaynak koddan da
doğrudan çalıştırılabilir.
"""

import locale
import os
import queue
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, scrolledtext, ttk

REPO_URL = "https://github.com/umitkrkmz/mediagrab.git"
GIT_DOWNLOAD_URL = "https://git-scm.com/downloads"
PYTHON_DOWNLOAD_URL = "https://www.python.org/downloads/"
FFMPEG_DOWNLOAD_URL = "https://www.ffmpeg.org/download.html"
USER_DATA_ENTRIES = ("indirilenler", "channels.json")

# NOTE: the app's own code uses list[dict] (3.9+) but no 3.10-only syntax, so
# 3.9 is the real floor. Checked here rather than left to fail later with a
# confusing pip/syntax error halfway through the install.
MIN_PYTHON = (3, 9)

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

# NOTE: this file must stay import-free of the mediagrab package - it runs
# BEFORE MediaGrab exists on disk. That's also what keeps the built exe free
# of third-party code (see the licence note in the README), so the strings and
# the ffmpeg/Python probes below are deliberate small duplicates rather than
# shared imports.
STRINGS = {
    "tr": {
        "title": "MediaGrab Kurulum",
        "install_folder": "Kurulum klasörü:",
        "browse": "Gözat…",
        "launch": "MediaGrab'ı Başlat",
        "ready_title": "Kur'a bastığınızda:",
        "ready_steps": (
            "1) MediaGrab bu klasöre indirilecek\n"
            "2) İzole bir Python ortamı (.venv) oluşturulacak\n"
            "3) Bağımlılıklar kurulacak\n"
            "4) Çift tıklayıp çalıştırabileceğiniz bir başlatma dosyası hazırlanacak"
        ),
        "warn_cloud_title": "Bulut klasörü uyarısı",
        "warn_cloud": (
            "Seçtiğiniz klasör bir bulut senkronizasyon servisi ({service}) içinde görünüyor.\n\n"
            "İndirme sırasında çok sayıda geçici dosya hızlıca yazılıp siliniyor; senkron servisi "
            "bunlardan birini kilitlerse indirme yarıda kesilebilir.\n\n"
            "Yine de bu klasöre kurulsun mu?"
        ),
        "warn_notempty_title": "Klasör boş değil",
        "warn_notempty": (
            "Bu klasörde zaten {count} öge var. MediaGrab yine de buraya kurulacak.\n\n"
            "Devam edilsin mi?"
        ),
        "err_unsafe_title": "Uygun olmayan klasör",
        "err_unsafe": (
            "Bu klasör kurulum için uygun değil: {folder}\n\n"
            "Sürücü kökü veya kişisel klasörleriniz (Masaüstü, Belgeler, kullanıcı klasörü) "
            "seçilemez — kaldırma işlemi bu klasörün içeriğini siler.\n\n"
            "Lütfen MediaGrab'a ayrılmış boş bir klasör seçin (ör. C:\\MediaGrab)."
        ),
        "requirements": "Gereksinimler",
        "checking": "kontrol ediliyor...",
        "found": "bulundu",
        "not_found": "bulunamadı",
        "too_old": "sürüm çok eski",
        "download": "indir",
        "refresh": "Durumu yenile",
        "copy": "Kopyala",
        "copied": "Kopyalandı ✓",
        "desktop_shortcut": "Masaüstüne kısayol ekle",
        "start_shortcut": "Başlat menüsüne ekle",
        "install": "Kur",
        "repair": "Onar / Güncelle",
        "remove": "Kaldır",
        "ffmpeg_note": (
            "ffmpeg olmadan uygulama açılır ama indirmeler birleştirme "
            "aşamasında başarısız olur."
        ),
        "python_min": "MediaGrab için Python {min} veya üstü gerekir.",
        "remove_confirm_title": "Kaldırma onayı",
        "remove_confirm": (
            "MediaGrab uygulaması bu klasörden kaldırılacak. İndirdiğiniz dosyalar "
            "(indirilenler/) ve takip listeniz (channels.json) korunacak. Devam edilsin mi?"
        ),
        "log_installing": "MediaGrab '{folder}' klasörüne kuruluyor...",
        "log_venv": "Sanal ortam oluşturuluyor...",
        "log_deps": "Bağımlılıklar kuruluyor (bu biraz sürebilir)...",
        "log_launcher": "'{name}' başlatma dosyası oluşturuldu.",
        "log_done": "Kurulum tamamlandı.",
        "log_launch_hint": "Başlatmak için: '{name}' dosyasına çift tıklayın.",
        "log_ffmpeg_missing": (
            "UYARI: ffmpeg/ffprobe bulunamadı. Kurmadan indirmeler çalışmaz - "
            "yukarıdaki komutu çalıştırın."
        ),
        "log_updating": "Mevcut kurulum güncelleniyor (git pull)...",
        "log_update_done": "Güncelleme tamamlandı.",
        "log_pull_failed": "git pull başarısız oldu, temiz kurulum deneniyor...",
        "log_keep_data": "Kullanıcı verisi (indirilenler/, channels.json) korunuyor...",
        "log_removing_old": "Eski kurulum siliniyor...",
        "log_removing": "Uygulama dosyaları siliniyor...",
        "log_removed": "Kaldırıldı. indirilenler/ ve channels.json korundu.",
        "log_shortcut": "{where} kısayol ekleniyor...",
        "err_generic": "HATA: {msg}",
        "err_venv": "HATA: Sanal ortam oluşturulamadı.",
        "err_deps": "HATA: Bağımlılıklar kurulamadı.",
        "err_git_init": "HATA: git init başarısız oldu.",
        "err_remote": "HATA: remote eklenemedi.",
        "err_fetch": "HATA: fetch başarısız oldu.",
        "err_head": "HATA: uzak varsayılan dal bulunamadı.",
        "err_checkout": "HATA: checkout başarısız oldu.",
        "warn_shortcut_os": "Uyarı: kısayollar yalnızca Windows'ta destekleniyor.",
        "warn_launcher_missing": "Uyarı: başlatma dosyası bulunamadığı için kısayol oluşturulamadı.",
        "warn_shortcut_folder": "Uyarı: {where} kısayol eklenemedi (klasör bulunamadı).",
        "warn_shortcut_failed": "Uyarı: {where} kısayol oluşturulamadı.",
        "warn_delete": "Uyarı: '{name}' silinemedi: {msg}",
        "where_desktop": "Masaüstüne",
        "where_start": "Başlat menüsüne",
    },
    "en": {
        "title": "MediaGrab Setup",
        "install_folder": "Install folder:",
        "browse": "Browse…",
        "launch": "Start MediaGrab",
        "ready_title": "When you click Install:",
        "ready_steps": (
            "1) MediaGrab is downloaded into this folder\n"
            "2) An isolated Python environment (.venv) is created\n"
            "3) Dependencies are installed\n"
            "4) A launcher you can double-click is written"
        ),
        "warn_cloud_title": "Cloud folder warning",
        "warn_cloud": (
            "This folder looks like it sits inside a cloud sync service ({service}).\n\n"
            "Downloads write and delete a lot of temporary files in quick succession; if the sync "
            "client locks one of them, a download can fail part-way.\n\n"
            "Install here anyway?"
        ),
        "warn_notempty_title": "Folder is not empty",
        "warn_notempty": (
            "This folder already contains {count} item(s). MediaGrab will still be installed here.\n\n"
            "Continue?"
        ),
        "err_unsafe_title": "Unsuitable folder",
        "err_unsafe": (
            "This folder can't be used for the install: {folder}\n\n"
            "A drive root or one of your personal folders (Desktop, Documents, your user folder) "
            "can't be chosen — removing MediaGrab deletes the contents of this folder.\n\n"
            "Please pick an empty folder dedicated to MediaGrab (e.g. C:\\MediaGrab)."
        ),
        "requirements": "Requirements",
        "checking": "checking...",
        "found": "found",
        "not_found": "not found",
        "too_old": "version too old",
        "download": "Download",
        "refresh": "Refresh",
        "copy": "Copy",
        "copied": "Copied ✓",
        "desktop_shortcut": "Add a desktop shortcut",
        "start_shortcut": "Add to the Start menu",
        "install": "Install",
        "repair": "Repair / Update",
        "remove": "Remove",
        "ffmpeg_note": (
            "Without ffmpeg the app still starts, but downloads fail at the merge step."
        ),
        "python_min": "MediaGrab needs Python {min} or newer.",
        "remove_confirm_title": "Confirm removal",
        "remove_confirm": (
            "MediaGrab will be removed from this folder. Your downloads "
            "(indirilenler/) and followed channels (channels.json) are kept. Continue?"
        ),
        "log_installing": "Installing MediaGrab into '{folder}'...",
        "log_venv": "Creating the virtual environment...",
        "log_deps": "Installing dependencies (this can take a while)...",
        "log_launcher": "Created the launcher '{name}'.",
        "log_done": "Installation complete.",
        "log_launch_hint": "To start it: double-click '{name}'.",
        "log_ffmpeg_missing": (
            "WARNING: ffmpeg/ffprobe not found. Downloads won't work until you "
            "install it - run the command shown above."
        ),
        "log_updating": "Updating the existing install (git pull)...",
        "log_update_done": "Update complete.",
        "log_pull_failed": "git pull failed, trying a clean install...",
        "log_keep_data": "Keeping your data (indirilenler/, channels.json)...",
        "log_removing_old": "Removing the old install...",
        "log_removing": "Removing application files...",
        "log_removed": "Removed. indirilenler/ and channels.json were kept.",
        "log_shortcut": "Adding {where} shortcut...",
        "err_generic": "ERROR: {msg}",
        "err_venv": "ERROR: could not create the virtual environment.",
        "err_deps": "ERROR: could not install dependencies.",
        "err_git_init": "ERROR: git init failed.",
        "err_remote": "ERROR: could not add the remote.",
        "err_fetch": "ERROR: fetch failed.",
        "err_head": "ERROR: could not determine the remote's default branch.",
        "err_checkout": "ERROR: checkout failed.",
        "warn_shortcut_os": "Note: shortcuts are only supported on Windows.",
        "warn_launcher_missing": "Note: no launcher file found, so no shortcut was created.",
        "warn_shortcut_folder": "Note: could not add the {where} shortcut (folder not found).",
        "warn_shortcut_failed": "Note: could not create the {where} shortcut.",
        "warn_delete": "Note: could not delete '{name}': {msg}",
        "where_desktop": "desktop",
        "where_start": "Start menu",
    },
}


def detect_lang() -> str:
    # NOTE: mirrors mediagrab/app.py's _detect_system_lang() - anything that
    # doesn't look Turkish gets English, so the installer speaks the same
    # language the app will once it's installed.
    try:
        lang = locale.getlocale()[0]
        if not lang:
            locale.setlocale(locale.LC_ALL, "")
            lang = locale.getlocale()[0]
    except Exception:
        lang = None
    if lang and "turk" not in lang.lower() and not lang.lower().startswith("tr"):
        return "en"
    return "tr"


def base_dir() -> str:
    # NOTE: same idiom as mediagrab/paths.py's app_dir() - when frozen into a
    # PyInstaller onefile exe, sys.executable is the .exe itself; running
    # from source, it's this script's own folder.
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def this_exe_name() -> str:
    if getattr(sys, "frozen", False):
        return os.path.basename(sys.executable)
    return os.path.basename(os.path.abspath(__file__))


def find_tool(*candidates: str):
    for name in candidates:
        path = shutil.which(name)
        if path:
            return path
    return None


def _run_probe(cmd: list) -> str:
    """Run a --version style command and return its output, or "" on failure."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10, creationflags=_NO_WINDOW
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if result.returncode != 0:
        return ""
    return ((result.stdout or "") + (result.stderr or "")).strip()


def python_version(python_path: str):
    """(major, minor) of the interpreter at `python_path`, or None."""
    # NOTE: asked of the interpreter itself rather than parsed from
    # "python --version" text, which varies between builds and launchers.
    out = _run_probe([python_path, "-c", "import sys;print('%d.%d' % sys.version_info[:2])"])
    match = re.match(r"^(\d+)\.(\d+)", out)
    return (int(match.group(1)), int(match.group(2))) if match else None


_FFMPEG_VERSION_RE = re.compile(r"^\w+ version n?([0-9][^\s,]*)")


def tool_version(tool: str):
    """Version string reported by ffmpeg/ffprobe, or None if it isn't there."""
    out = _run_probe([tool, "-version"])
    if not out:
        return None
    first_line = out.splitlines()[0]
    match = _FFMPEG_VERSION_RE.match(first_line)
    return match.group(1) if match else first_line


def ffmpeg_install_command() -> str:
    if sys.platform == "win32":
        return "winget install --id Gyan.FFmpeg -e"
    if sys.platform == "darwin":
        return "brew install ffmpeg"
    return "sudo apt install ffmpeg"


CLOUD_MARKERS = ("onedrive", "dropbox", "google drive", "googledrive", "icloud", "yandex.disk")


def cloud_service_in_path(folder: str):
    """Name of the cloud sync service this folder appears to live under, if any."""
    # NOTE: downloads churn through many small temp files; a sync client that
    # locks one mid-write aborts the download. Worth warning about, since on
    # Windows "Desktop" and "Documents" are frequently OneDrive-redirected.
    lowered = folder.replace("\\", "/").lower()
    for marker in CLOUD_MARKERS:
        if marker in lowered:
            return marker
    return None


def is_unsafe_target(folder: str) -> bool:
    """True for folders that must never be wiped by Remove/Repair."""
    # NOTE: Remove deletes everything in the install folder except user data.
    # That's fine for a folder dedicated to MediaGrab, and catastrophic for a
    # drive root or the user's own Desktop/Documents - so those are refused
    # outright rather than guarded by a confirmation the user might click past.
    path = os.path.abspath(folder)
    if os.path.dirname(path) == path:  # drive root / filesystem root
        return True
    home = os.path.abspath(os.path.expanduser("~"))
    if path == home:
        return True
    protected = {
        os.path.join(home, name)
        for name in ("Desktop", "Documents", "Downloads", "Masaüstü", "Belgeler", "İndirilenler")
    }
    return path in {os.path.abspath(p) for p in protected}


def is_installed(folder: str) -> bool:
    return os.path.isfile(os.path.join(folder, "run.py")) and os.path.isdir(os.path.join(folder, "mediagrab"))


def is_git_repo(folder: str) -> bool:
    return os.path.isdir(os.path.join(folder, ".git"))


def _force_remove_readonly(func, path, _exc_info):
    # NOTE: git marks some of its object files read-only on Windows;
    # shutil.rmtree can't delete those without clearing the attribute first.
    os.chmod(path, stat.S_IWRITE)
    func(path)


def venv_python_path(venv_dir: str) -> str:
    if os.name == "nt":
        return os.path.join(venv_dir, "Scripts", "python.exe")
    return os.path.join(venv_dir, "bin", "python")


CSIDL_DESKTOPDIRECTORY = 0x10
CSIDL_PROGRAMS = 0x02  # user's Start Menu\Programs folder


def _known_folder(csidl: int):
    # NOTE: resolves the ACTUAL Desktop/Start Menu folder, including OneDrive
    # "Known Folder Move" redirection (e.g. Desktop moved under
    # C:\Users\<user>\OneDrive\Desktop) - os.path.expanduser("~/Desktop")
    # would silently point at a stale, non-redirected path in that case.
    import ctypes

    buf = ctypes.create_unicode_buffer(260)
    result = ctypes.windll.shell32.SHGetFolderPathW(0, csidl, 0, 0, buf)
    return buf.value if result == 0 else None


def _ps_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def _launcher_name() -> str:
    return "MediaGrab Baslat.bat" if os.name == "nt" else "mediagrab-baslat.sh"


class SetupApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = detect_lang()
        self.title(self.t("title"))
        self.geometry("680x600")
        self.minsize(620, 500)

        self.base_dir = base_dir()
        self.git_path = None
        self.python_path = None
        self.python_ver = None
        self.ffmpeg_ver = None
        self.ffprobe_ver = None
        self.log_queue: queue.Queue = queue.Queue()
        self._poll_after_id = None

        self._build_widgets()
        self._refresh_status()
        self.after(150, self._poll_log_queue)

    def t(self, key: str, **kwargs) -> str:
        text = STRINGS[self.lang][key]
        return text.format(**kwargs) if kwargs else text

    # ---------- UI ----------

    def _setup_style(self):
        style = ttk.Style(self)
        # NOTE: the default "clam"/"classic" themes look like Windows 95 next
        # to MediaGrab's own UI. "vista" is the native modern look and is
        # present on Windows; elsewhere fall back to whatever is available.
        for candidate in ("vista", "aqua", "clam"):
            if candidate in style.theme_names():
                style.theme_use(candidate)
                break
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Ok.TLabel", foreground="#1d8049")
        style.configure("Bad.TLabel", foreground="#b3261e")
        style.configure("Muted.TLabel", foreground="#6b717b")
        style.configure("Warn.TLabel", foreground="#8a6100")
        style.configure("Cmd.TLabel", font=("Consolas", 9), foreground="#3c414a")
        style.configure("Path.TLabel", font=("Segoe UI", 9, "bold"))

    def _build_widgets(self):
        self._setup_style()

        folder_box = ttk.LabelFrame(self, text=self.t("install_folder"))
        folder_box.pack(fill="x", padx=14, pady=(14, 8))
        folder_row = ttk.Frame(folder_box)
        folder_row.pack(fill="x", padx=10, pady=10)
        self.folder_label = ttk.Label(folder_row, text=self.base_dir, style="Path.TLabel", wraplength=520)
        self.folder_label.pack(side="left", fill="x", expand=True)
        self.browse_btn = ttk.Button(folder_row, text=self.t("browse"), command=self._choose_folder)
        self.browse_btn.pack(side="right", padx=(10, 0))
        self.folder_warning = ttk.Label(folder_box, text="", style="Warn.TLabel", wraplength=620, justify="left")

        status = ttk.LabelFrame(self, text=self.t("requirements"))
        status.pack(fill="x", padx=14, pady=8)

        git_row = ttk.Frame(status)
        git_row.pack(fill="x", padx=10, pady=(10, 4))
        self.git_status_label = ttk.Label(git_row, text=f"Git: {self.t('checking')}")
        self.git_status_label.pack(side="left")
        self.git_download_btn = ttk.Button(
            git_row, text=f"Git {self.t('download')}", command=lambda: webbrowser.open(GIT_DOWNLOAD_URL)
        )
        self.git_download_btn.pack(side="right")

        python_row = ttk.Frame(status)
        python_row.pack(fill="x", padx=10, pady=4)
        self.python_status_label = ttk.Label(python_row, text=f"Python: {self.t('checking')}")
        self.python_status_label.pack(side="left")
        self.python_download_btn = ttk.Button(
            python_row, text=f"Python {self.t('download')}", command=lambda: webbrowser.open(PYTHON_DOWNLOAD_URL)
        )
        self.python_download_btn.pack(side="right")

        # NOTE: ffmpeg is a hard requirement for merging/converting, but the
        # installer can't install it (system package manager, often needs
        # elevation). It's checked and surfaced here with a copyable command
        # so a missing ffmpeg is caught BEFORE the first failed download.
        ffmpeg_row = ttk.Frame(status)
        ffmpeg_row.pack(fill="x", padx=10, pady=4)
        self.ffmpeg_status_label = ttk.Label(ffmpeg_row, text=f"ffmpeg: {self.t('checking')}")
        self.ffmpeg_status_label.pack(side="left")
        self.ffmpeg_copy_btn = ttk.Button(ffmpeg_row, text=self.t("copy"), command=self._copy_ffmpeg_command)
        self.ffmpeg_copy_btn.pack(side="right")

        self.ffmpeg_cmd_label = ttk.Label(status, text="", style="Cmd.TLabel")
        self.ffmpeg_cmd_label.pack(fill="x", padx=10)
        self.ffmpeg_note_label = ttk.Label(status, text="", style="Warn.TLabel", wraplength=620, justify="left")
        self.ffmpeg_note_label.pack(fill="x", padx=10)

        refresh_row = ttk.Frame(status)
        refresh_row.pack(fill="x", padx=10, pady=(6, 10))
        ttk.Button(refresh_row, text=self.t("refresh"), command=self._refresh_status).pack(side="right")

        shortcuts_row = ttk.Frame(self)
        shortcuts_row.pack(fill="x", padx=14, pady=(0, 6))
        self.desktop_shortcut_var = tk.BooleanVar(value=False)
        self.start_shortcut_var = tk.BooleanVar(value=False)
        self.desktop_check = ttk.Checkbutton(
            shortcuts_row, text=self.t("desktop_shortcut"), variable=self.desktop_shortcut_var
        )
        self.desktop_check.pack(side="left")
        self.start_check = ttk.Checkbutton(
            shortcuts_row, text=self.t("start_shortcut"), variable=self.start_shortcut_var
        )
        self.start_check.pack(side="left", padx=(16, 0))

        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=14, pady=8)
        for col in range(3):
            actions.columnconfigure(col, weight=1)
        self.install_btn = ttk.Button(
            actions, text=self.t("install"), style="Primary.TButton", command=self.on_install
        )
        self.install_btn.grid(row=0, column=0, sticky="ew", padx=4, ipady=4)
        self.repair_btn = ttk.Button(actions, text=self.t("repair"), command=self.on_repair)
        self.repair_btn.grid(row=0, column=1, sticky="ew", padx=4, ipady=4)
        self.remove_btn = ttk.Button(actions, text=self.t("remove"), command=self.on_remove)
        self.remove_btn.grid(row=0, column=2, sticky="ew", padx=4, ipady=4)

        launch_row = ttk.Frame(self)
        launch_row.pack(fill="x", padx=14, pady=(0, 4))
        self.launch_btn = ttk.Button(
            launch_row, text=self.t("launch"), style="Primary.TButton", command=self._launch_app
        )
        self.launch_btn.pack(fill="x", ipady=4)

        self.progress = ttk.Progressbar(self, mode="indeterminate")

        # NOTE: the log used to be a black rectangle filling half the window
        # with nothing in it. Until something actually runs, the same space
        # explains what Install will do instead.
        self.ready_frame = ttk.Frame(self)
        ttk.Label(self.ready_frame, text=self.t("ready_title"), style="Path.TLabel").pack(anchor="w")
        ttk.Label(
            self.ready_frame, text=self.t("ready_steps"), style="Muted.TLabel", justify="left"
        ).pack(anchor="w", pady=(6, 0))
        self.ready_frame.pack(fill="both", expand=True, padx=18, pady=(8, 12))

        self.log_text = scrolledtext.ScrolledText(
            self, state="disabled", font=("Consolas", 9), bg="#1e1e1e", fg="#d8d8d8", height=10
        )
        self._log_shown = False

    def _show_log(self):
        """Swap the "what will happen" panel for the live log, once."""
        if self._log_shown:
            return
        self.ready_frame.pack_forget()
        self.log_text.pack(fill="both", expand=True, padx=14, pady=(6, 12))
        self._log_shown = True

    def _choose_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.base_dir, mustexist=True)
        if not chosen:
            return
        chosen = os.path.abspath(chosen)
        if is_unsafe_target(chosen):
            messagebox.showerror(self.t("err_unsafe_title"), self.t("err_unsafe", folder=chosen))
            return
        self.base_dir = chosen
        self.folder_label.config(text=self.base_dir)
        self._refresh_status()

    def _launch_app(self):
        launcher = os.path.join(self.base_dir, _launcher_name())
        if not os.path.isfile(launcher):
            return
        try:
            if os.name == "nt":
                os.startfile(launcher)  # noqa: S606 - launching our own script
            else:
                subprocess.Popen(["sh", launcher], cwd=self.base_dir)
        except OSError as exc:
            self.log(self.t("err_generic", msg=exc))

    def _copy_ffmpeg_command(self):
        command = ffmpeg_install_command()
        self.clipboard_clear()
        self.clipboard_append(command)
        original = self.ffmpeg_copy_btn.cget("text")
        self.ffmpeg_copy_btn.config(text=self.t("copied"))
        self.after(1500, lambda: self.ffmpeg_copy_btn.config(text=original))

    def _refresh_status(self):
        self.git_path = find_tool("git")
        self.python_path = find_tool("python", "python3", "py")
        self.python_ver = python_version(self.python_path) if self.python_path else None
        self.ffmpeg_ver = tool_version("ffmpeg")
        self.ffprobe_ver = tool_version("ffprobe")

        # NOTE: deliberately not showing the resolved path here - it can be
        # long enough to push the button on the right off the edge of the
        # window. It's still logged in full when an action actually runs.
        self.git_status_label.config(
            text=f"Git: {self.t('found')} ✓" if self.git_path else f"Git: {self.t('not_found')} ✗",
            style="Ok.TLabel" if self.git_path else "Bad.TLabel",
        )
        self.git_download_btn.config(state="normal" if not self.git_path else "disabled")

        min_text = ".".join(str(p) for p in MIN_PYTHON)
        python_ok = bool(self.python_ver and self.python_ver >= MIN_PYTHON)
        if not self.python_path:
            python_text = f"Python: {self.t('not_found')} ✗"
        elif not self.python_ver:
            # NOTE: found on PATH but wouldn't tell us its version - most often
            # the Windows Store stub, which isn't a usable interpreter.
            python_text = f"Python: {self.t('not_found')} ✗"
        elif not python_ok:
            found = ".".join(str(p) for p in self.python_ver)
            python_text = f"Python {found}: {self.t('too_old')} ✗ ({self.t('python_min', min=min_text)})"
        else:
            found = ".".join(str(p) for p in self.python_ver)
            python_text = f"Python {found}: {self.t('found')} ✓"
        self.python_status_label.config(text=python_text, style="Ok.TLabel" if python_ok else "Bad.TLabel")
        self.python_download_btn.config(state="disabled" if python_ok else "normal")

        ffmpeg_ok = bool(self.ffmpeg_ver and self.ffprobe_ver)
        if ffmpeg_ok:
            self.ffmpeg_status_label.config(
                text=f"ffmpeg / ffprobe {self.ffmpeg_ver}: {self.t('found')} ✓", style="Ok.TLabel"
            )
            self.ffmpeg_cmd_label.config(text="")
            self.ffmpeg_note_label.config(text="")
            self.ffmpeg_copy_btn.config(state="disabled")
        else:
            missing = " / ".join(
                name for name, ver in (("ffmpeg", self.ffmpeg_ver), ("ffprobe", self.ffprobe_ver)) if not ver
            )
            self.ffmpeg_status_label.config(text=f"{missing}: {self.t('not_found')} ✗", style="Bad.TLabel")
            self.ffmpeg_cmd_label.config(text=ffmpeg_install_command())
            self.ffmpeg_note_label.config(text=self.t("ffmpeg_note"))
            self.ffmpeg_copy_btn.config(state="normal")

        installed = is_installed(self.base_dir)
        # NOTE: ffmpeg deliberately does NOT gate installing - it's needed to
        # download, not to install, and the user may well fix it afterwards.
        # Git and a new enough Python genuinely are required to get this far.
        tools_ok = bool(self.git_path and python_ok)

        self.install_btn.config(state="normal" if (tools_ok and not installed) else "disabled")
        self.repair_btn.config(state="normal" if (tools_ok and installed) else "disabled")
        self.remove_btn.config(state="normal" if installed else "disabled")

        # NOTE: shortcuts are only created by Install/Repair, so the checkboxes
        # are meaningless when neither can run - greying them out answers
        # "what do these actually do?" without a paragraph of text.
        shortcut_state = "normal" if (tools_ok and os.name == "nt") else "disabled"
        self.desktop_check.config(state=shortcut_state)
        self.start_check.config(state=shortcut_state)

        # NOTE: only offered once there's actually something to launch.
        launcher_ready = os.path.isfile(os.path.join(self.base_dir, _launcher_name()))
        self.launch_btn.config(state="normal" if launcher_ready else "disabled")

        service = cloud_service_in_path(self.base_dir)
        if service and not installed:
            self.folder_warning.config(text=self.t("warn_cloud", service=service).splitlines()[0])
            self.folder_warning.pack(fill="x", padx=10, pady=(0, 8))
        else:
            self.folder_warning.pack_forget()

    def _set_buttons_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in (self.install_btn, self.repair_btn, self.remove_btn, self.browse_btn):
            btn.config(state=state)
        if enabled:
            self.progress.stop()
            self.progress.pack_forget()
            self._refresh_status()
        else:
            # NOTE: git/pip give no usable percentage, so this is an
            # indeterminate "still working" indicator rather than a fake bar.
            self.progress.pack(fill="x", padx=14, pady=(0, 6))
            self.progress.start(12)

    # ---------- logging / threading plumbing ----------

    def log(self, message: str):
        self.log_queue.put(message)

    def _poll_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if msg == "__DONE__":
                    self._set_buttons_enabled(True)
                    continue
                self.log_text.configure(state="normal")
                self.log_text.insert("end", msg + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        # NOTE: this poll reschedules itself forever, so it has to stop once
        # the window is gone - otherwise Tk fires the pending callback against
        # a destroyed widget and prints 'invalid command name ..._poll_log_queue'.
        if self.winfo_exists():
            self._poll_after_id = self.after(150, self._poll_log_queue)

    def destroy(self):
        if getattr(self, "_poll_after_id", None):
            try:
                self.after_cancel(self._poll_after_id)
            except tk.TclError:
                pass
            self._poll_after_id = None
        super().destroy()

    def _confirm_target_folder(self) -> bool:
        """Ask about anything risky about the install folder before touching it."""
        if is_unsafe_target(self.base_dir):
            messagebox.showerror(self.t("err_unsafe_title"), self.t("err_unsafe", folder=self.base_dir))
            return False

        service = cloud_service_in_path(self.base_dir)
        if service and not messagebox.askyesno(
            self.t("warn_cloud_title"), self.t("warn_cloud", service=service)
        ):
            return False

        # NOTE: the installer's own exe usually sits here, so it doesn't count
        # towards "is this folder already in use for something else".
        others = [n for n in os.listdir(self.base_dir) if n != this_exe_name()]
        if others and not messagebox.askyesno(
            self.t("warn_notempty_title"), self.t("warn_notempty", count=len(others))
        ):
            return False
        return True

    def _run_async(self, fn):
        self._show_log()
        self._set_buttons_enabled(False)

        def wrapper():
            try:
                fn()
            except Exception as exc:  # surface anything unexpected in the log instead of crashing silently
                self.log(self.t("err_generic", msg=exc))
            finally:
                self.log_queue.put("__DONE__")

        threading.Thread(target=wrapper, daemon=True).start()

    def _run_cmd(self, cmd: list, cwd: str) -> bool:
        self.log("$ " + " ".join(cmd))
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            for line in proc.stdout:
                self.log(line.rstrip())
            proc.wait()
            return proc.returncode == 0
        except OSError as exc:
            self.log(f"HATA: {exc}")
            return False

    # ---------- install / repair / remove ----------

    def _setup_venv_and_deps(self) -> bool:
        venv_dir = os.path.join(self.base_dir, ".venv")
        self.log(self.t("log_venv"))
        if not self._run_cmd([self.python_path, "-m", "venv", venv_dir], cwd=self.base_dir):
            self.log(self.t("err_venv"))
            return False

        venv_python = venv_python_path(venv_dir)
        self.log(self.t("log_deps"))
        if not self._run_cmd([venv_python, "-m", "pip", "install", "-r", "requirements.txt"], cwd=self.base_dir):
            self.log(self.t("err_deps"))
            return False

        launcher_name = self._write_launcher(venv_python)
        self.log(self.t("log_launcher", name=launcher_name))
        return True

    def _write_launcher(self, venv_python: str) -> str:
        # NOTE: double-clicking run.py directly would use whatever Python is
        # associated with .py files system-wide (almost never this venv), so
        # it fails with "no module named uvicorn" for most users. A .bat that
        # calls the venv's own python.exe by full path sidesteps that.
        name = _launcher_name()
        if os.name == "nt":
            content = f'@echo off\r\ncd /d "%~dp0"\r\n"{venv_python}" run.py\r\npause\r\n'
        else:
            content = f'#!/bin/sh\ncd "$(dirname "$0")"\n"{venv_python}" run.py\n'
        path = os.path.join(self.base_dir, name)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        if os.name != "nt":
            os.chmod(path, 0o755)
        return name

    def on_install(self):
        if not self._confirm_target_folder():
            return
        want_desktop = self.desktop_shortcut_var.get()
        want_start = self.start_shortcut_var.get()
        self._run_async(lambda: self._do_install(want_desktop, want_start))

    def _do_install(self, want_desktop: bool = False, want_start: bool = False):
        # NOTE: `git clone <url> .` refuses to run in a non-empty directory,
        # and this folder always has at least the setup exe/script itself in
        # it - so we clone the long way instead (init + remote + fetch +
        # checkout), which has no such restriction.
        self.log(self.t("log_installing", folder=self.base_dir))
        if not self._run_cmd([self.git_path, "init"], cwd=self.base_dir):
            self.log(self.t("err_git_init"))
            return
        if not self._run_cmd([self.git_path, "remote", "add", "origin", REPO_URL], cwd=self.base_dir):
            self.log(self.t("err_remote"))
            return
        if not self._run_cmd([self.git_path, "fetch", "origin"], cwd=self.base_dir):
            self.log(self.t("err_fetch"))
            return
        if not self._run_cmd([self.git_path, "remote", "set-head", "origin", "-a"], cwd=self.base_dir):
            self.log(self.t("err_head"))
            return
        branch = self._default_branch()
        if not self._run_cmd([self.git_path, "checkout", "-B", branch, f"origin/{branch}"], cwd=self.base_dir):
            self.log(self.t("err_checkout"))
            return
        if not self._setup_venv_and_deps():
            return
        if want_desktop or want_start:
            self._create_shortcuts(want_desktop, want_start)
        self.log(self.t("log_done"))
        self.log(self.t("log_launch_hint", name=_launcher_name()))
        if not (self.ffmpeg_ver and self.ffprobe_ver):
            self.log(self.t("log_ffmpeg_missing"))

    def _create_shortcuts(self, want_desktop: bool, want_start: bool):
        if os.name != "nt":
            self.log(self.t("warn_shortcut_os"))
            return
        launcher_path = os.path.join(self.base_dir, _launcher_name())
        if not os.path.isfile(launcher_path):
            self.log(self.t("warn_launcher_missing"))
            return
        if want_desktop:
            self._create_one_shortcut(CSIDL_DESKTOPDIRECTORY, self.t("where_desktop"), launcher_path)
        if want_start:
            self._create_one_shortcut(CSIDL_PROGRAMS, self.t("where_start"), launcher_path)

    def _create_one_shortcut(self, csidl: int, label: str, target: str):
        folder = _known_folder(csidl)
        if not folder:
            self.log(self.t("warn_shortcut_folder", where=label))
            return
        self.log(self.t("log_shortcut", where=label))
        link_path = os.path.join(folder, "MediaGrab.lnk")
        ps_cmd = (
            f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut({_ps_quote(link_path)}); "
            f"$s.TargetPath = {_ps_quote(target)}; "
            f"$s.WorkingDirectory = {_ps_quote(self.base_dir)}; "
            "$s.Save()"
        )
        if not self._run_cmd(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd], cwd=self.base_dir):
            self.log(self.t("warn_shortcut_failed", where=label))

    def _default_branch(self) -> str:
        try:
            result = subprocess.run(
                [self.git_path, "symbolic-ref", "refs/remotes/origin/HEAD"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            return result.stdout.strip().rsplit("/", 1)[-1] or "master"
        except OSError:
            return "master"

    def on_repair(self):
        want_desktop = self.desktop_shortcut_var.get()
        want_start = self.start_shortcut_var.get()
        self._run_async(lambda: self._do_repair(want_desktop, want_start))

    def _do_repair(self, want_desktop: bool = False, want_start: bool = False):
        if is_git_repo(self.base_dir):
            self.log(self.t("log_updating"))
            if self._run_cmd([self.git_path, "pull"], cwd=self.base_dir):
                if self._setup_venv_and_deps():
                    self.log(self.t("log_update_done"))
                    if want_desktop or want_start:
                        self._create_shortcuts(want_desktop, want_start)
                return
            self.log(self.t("log_pull_failed"))

        self.log(self.t("log_keep_data"))
        stash_dir = self._stash_user_data()
        self.log(self.t("log_removing_old"))
        self._wipe_app_files()
        self._restore_user_data(stash_dir)
        self._do_install(want_desktop, want_start)

    def on_remove(self):
        if not messagebox.askyesno(self.t("remove_confirm_title"), self.t("remove_confirm")):
            return
        self._run_async(self._do_remove)

    def _do_remove(self):
        self.log(self.t("log_keep_data"))
        stash_dir = self._stash_user_data()
        self.log(self.t("log_removing"))
        self._wipe_app_files()
        self._restore_user_data(stash_dir)
        self.log(self.t("log_removed"))

    # ---------- filesystem helpers ----------

    def _stash_user_data(self) -> str:
        stash_dir = tempfile.mkdtemp(prefix="mediagrab_setup_")
        for name in USER_DATA_ENTRIES:
            src = os.path.join(self.base_dir, name)
            if os.path.exists(src):
                shutil.move(src, os.path.join(stash_dir, name))
        return stash_dir

    def _restore_user_data(self, stash_dir: str):
        for name in USER_DATA_ENTRIES:
            src = os.path.join(stash_dir, name)
            if os.path.exists(src):
                shutil.move(src, os.path.join(self.base_dir, name))
        shutil.rmtree(stash_dir, ignore_errors=True)

    def _wipe_app_files(self):
        keep = {this_exe_name()}
        for name in os.listdir(self.base_dir):
            if name in keep:
                continue
            path = os.path.join(self.base_dir, name)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path, onerror=_force_remove_readonly)
                else:
                    os.chmod(path, stat.S_IWRITE)
                    os.remove(path)
            except OSError as exc:
                self.log(self.t("warn_delete", name=name, msg=exc))


if __name__ == "__main__":
    SetupApp().mainloop()
