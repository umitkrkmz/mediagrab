"""MediaGrab kurulum sihirbazı.

Açılışta Kur / Onar-Güncelle / Kaldır seçilir. Kur ve Onar önce Git, Python
ve ffmpeg'i kontrol eder (kurmaz - eksikse resmi indirme sayfasına
yönlendirir), sonra klasör ve kısayol seçimi, bir özet sayfası ve işlemin
canlı günlüğü gelir. Kur: klonla, sanal ortam oluştur, bağımlılıkları kur,
çift tıklanabilir bir başlatma dosyası yaz. Onar: mümkünse `git pull`, değilse
temiz kurulum. Kaldır: uygulama dosyalarını sil - her durumda `indirilenler/`,
`channels.json` ve `settings.json` dokunulmadan korunur. Son kurulum klasörü
%LOCALAPPDATA%/MediaGrab/installer.json içinde hatırlanır, böylece Onar ve
Kaldır klasörü kendiliğinden bulur.

PyInstaller ile derlenip GitHub Release'e eklenmek üzere tasarlandı (bkz.
setup_mediagrab.spec); `python setup_mediagrab.py` ile kaynak koddan da
doğrudan çalıştırılabilir.
"""

import json
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
USER_DATA_ENTRIES = ("indirilenler", "channels.json", "settings.json")

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
        "welcome_heading": "MediaGrab Kurulum",
        "welcome_intro": "Ne yapmak istiyorsunuz?",
        "welcome_install_desc": "MediaGrab'ı bu bilgisayara ilk kez kurun.",
        "welcome_repair_desc": "Mevcut kurulumu güncelleyin ya da bozulduysa onarın.",
        "welcome_remove_desc": "MediaGrab'ı kaldırın — indirdikleriniz ve ayarlarınız korunur.",
        "docker": "Docker ile kur",
        "docker_desc": "Docker imajından çalıştırma — henüz hazır değil.",
        "docker_soon_title": "Yapım aşamasında",
        "docker_soon": (
            "Docker ile kurulum henüz hazır değil; sonraki bir sürümde gelecek.\n\n"
            "Şimdilik \"Kur\" ile kaynak koddan kurabilirsiniz."
        ),
        "remembered_install": "Son kurulum: {folder}",
        "next": "İleri →",
        "back": "← Geri",
        "home": "Ana sayfa",
        "close": "Kapat",
        "page_folder": "Kurulum klasörü",
        "page_summary": "Özet",
        "page_progress": "İşlem",
        "deps_intro": (
            "Kurulum için Git ve Python {min}+ gerekli. ffmpeg indirmeler için gerekli ama "
            "kurulumu engellemez — sonradan da kurabilirsiniz."
        ),
        "deps_blocked": "Eksik gereksinimleri kurun, sonra \"Durumu yenile\"ye basın.",
        "folder_intro_install": (
            "MediaGrab'a ayrılmış boş bir klasör seçin (ör. C:\\MediaGrab). Kaldırma işlemi bu "
            "klasörün içeriğini sildiği için sürücü kökü ve kişisel klasörler kabul edilmez."
        ),
        "folder_intro_repair": "Onarılacak / güncellenecek kurulumun klasörü:",
        "folder_intro_remove": "Kaldırılacak kurulumun klasörü:",
        "folder_unsafe_short": (
            "Bu klasör kurulum için uygun değil (sürücü kökü veya kişisel klasör) — başka bir klasör seçin."
        ),
        "folder_already_installed": (
            "Bu klasörde zaten bir MediaGrab kurulumu var — ana sayfadan \"Onar / Güncelle\"yi kullanın."
        ),
        "folder_not_installed": "Bu klasörde bir MediaGrab kurulumu bulunamadı — doğru klasörü seçin.",
        "folder_remembered_hint": "Son kurulumun klasörü otomatik dolduruldu; isterseniz değiştirebilirsiniz.",
        "summary_action": "İşlem:",
        "summary_folder": "Klasör:",
        "summary_tools": "Araçlar:",
        "summary_shortcuts": "Kısayollar:",
        "summary_none": "eklenmeyecek",
        "summary_overwrite_launcher": "Mevcut '{name}' dosyasının üzerine yazılacak.",
        "summary_overwrite_shortcut": "Mevcut MediaGrab kısayolunun üzerine yazılacak.",
        "summary_ffmpeg_missing": (
            "ffmpeg bulunamadı — kurulum yapılır ama indirmeler ffmpeg kurulana kadar çalışmaz."
        ),
        "summary_remove_note": (
            "Uygulama dosyaları silinecek; indirilenler/, channels.json ve settings.json olduğu gibi korunacak."
        ),
        "progress_title_install": "Kuruluyor…",
        "progress_title_repair": "Onarılıyor / güncelleniyor…",
        "progress_title_remove": "Kaldırılıyor…",
        "done_ok": "Tamamlandı ✓",
        "done_fail": "Tamamlanamadı ✗ — ayrıntılar günlükte",
    },
    "en": {
        "title": "MediaGrab Setup",
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
        "welcome_heading": "MediaGrab Setup",
        "welcome_intro": "What would you like to do?",
        "welcome_install_desc": "Install MediaGrab on this computer for the first time.",
        "welcome_repair_desc": "Update an existing install, or repair it if it's broken.",
        "welcome_remove_desc": "Remove MediaGrab — your downloads and settings are kept.",
        "docker": "Install with Docker",
        "docker_desc": "Run from a Docker image — not ready yet.",
        "docker_soon_title": "Coming soon",
        "docker_soon": (
            "Installing with Docker isn't ready yet; it's planned for a later version.\n\n"
            "For now, use \"Install\" to install from source."
        ),
        "remembered_install": "Last install: {folder}",
        "next": "Next →",
        "back": "← Back",
        "home": "Home",
        "close": "Close",
        "page_folder": "Install folder",
        "page_summary": "Summary",
        "page_progress": "Progress",
        "deps_intro": (
            "Git and Python {min}+ are required to install. ffmpeg is needed for downloads but "
            "doesn't block the install — you can add it later."
        ),
        "deps_blocked": "Install the missing requirements, then click \"Refresh\".",
        "folder_intro_install": (
            "Pick an empty folder dedicated to MediaGrab (e.g. C:\\MediaGrab). Removing deletes this "
            "folder's contents, so drive roots and personal folders are refused."
        ),
        "folder_intro_repair": "The folder of the install to repair / update:",
        "folder_intro_remove": "The folder of the install to remove:",
        "folder_unsafe_short": (
            "This folder can't be used (a drive root or a personal folder) — pick another one."
        ),
        "folder_already_installed": (
            "There's already a MediaGrab install in this folder — use \"Repair / Update\" from the home page."
        ),
        "folder_not_installed": "No MediaGrab install was found in this folder — pick the right one.",
        "folder_remembered_hint": "Filled in from your last install; change it if needed.",
        "summary_action": "Action:",
        "summary_folder": "Folder:",
        "summary_tools": "Tools:",
        "summary_shortcuts": "Shortcuts:",
        "summary_none": "none",
        "summary_overwrite_launcher": "The existing '{name}' will be overwritten.",
        "summary_overwrite_shortcut": "The existing MediaGrab shortcut will be overwritten.",
        "summary_ffmpeg_missing": (
            "ffmpeg not found — the install proceeds, but downloads won't work until ffmpeg is installed."
        ),
        "summary_remove_note": (
            "Application files will be deleted; indirilenler/, channels.json and settings.json are kept as they are."
        ),
        "progress_title_install": "Installing…",
        "progress_title_repair": "Repairing / updating…",
        "progress_title_remove": "Removing…",
        "done_ok": "Done ✓",
        "done_fail": "Did not complete ✗ — see the log for details",
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


def refresh_path_from_registry() -> None:
    """Re-read PATH from the registry so just-installed tools become visible."""
    # NOTE: os.environ["PATH"] is a snapshot taken when this process started.
    # Installing Git or Python writes their new PATH entries to the registry,
    # but a window that was already open never learns about it - so "Refresh"
    # kept re-checking the same stale list and closing/reopening the app was
    # the only cure. Entries are only ever ADDED: whatever this process was
    # handed stays put, so PyInstaller's own temp directory can't be dropped.
    if os.name != "nt":
        return
    import winreg

    found = []
    for root, key in (
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
        (winreg.HKEY_CURRENT_USER, "Environment"),
    ):
        try:
            with winreg.OpenKey(root, key) as handle:
                value, _ = winreg.QueryValueEx(handle, "Path")
        except OSError:
            # NOTE: HKCU\Environment has no Path until the user gets one, and
            # a locked-down machine can refuse the read. Neither is fatal -
            # we just keep whichever scopes did answer.
            continue
        # NOTE: PATH is normally REG_EXPAND_SZ, so "%SystemRoot%\system32"
        # arrives unexpanded and resolves to nothing until expanded.
        found.append(os.path.expandvars(value))

    merged = []
    for chunk in found + [os.environ.get("PATH", "")]:
        for entry in chunk.split(os.pathsep):
            entry = entry.strip()
            if entry and entry not in merged:
                merged.append(entry)
    if merged:
        os.environ["PATH"] = os.pathsep.join(merged)


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


def same_folder(a: str, b: str) -> bool:
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


STATE_FILE_NAME = "installer.json"


def installer_state_dir() -> str:
    # NOTE: deliberately NOT next to the exe. People run the installer from
    # Downloads and then delete or move it, so anything kept beside it is lost
    # with it. LOCALAPPDATA is per-user, needs no elevation, and survives that.
    if os.name == "nt":
        root = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    else:
        root = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(root, "MediaGrab")


def installer_state_path() -> str:
    return os.path.join(installer_state_dir(), STATE_FILE_NAME)


def load_last_install_dir():
    """The folder of the last successful install, or None if unknown/unreadable."""
    try:
        with open(installer_state_path(), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    folder = data.get("last_install_dir") if isinstance(data, dict) else None
    return folder if isinstance(folder, str) and folder else None


def save_last_install_dir(folder: str) -> None:
    # NOTE: remembering is a convenience - a failure here must never turn a
    # finished install into a reported error.
    try:
        os.makedirs(installer_state_dir(), exist_ok=True)
        with open(installer_state_path(), "w", encoding="utf-8") as f:
            json.dump({"last_install_dir": os.path.abspath(folder)}, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def forget_last_install_dir() -> None:
    try:
        os.remove(installer_state_path())
    except OSError:
        pass


MODE_INSTALL = "install"
MODE_REPAIR = "repair"
MODE_REMOVE = "remove"

PROGRESS_TITLE_KEYS = {
    MODE_INSTALL: "progress_title_install",
    MODE_REPAIR: "progress_title_repair",
    MODE_REMOVE: "progress_title_remove",
}


class SetupApp(tk.Tk):
    """A wizard: welcome → (requirements) → folder → summary → progress."""

    def __init__(self):
        super().__init__()
        self.lang = detect_lang()
        self.geometry("680x620")
        self.minsize(640, 540)

        self.mode = None
        self.current_page = None
        self.base_dir = base_dir()
        self.folder_prefilled = False
        self.git_path = None
        self.python_path = None
        self.python_ver = None
        self.ffmpeg_ver = None
        self.ffprobe_ver = None
        self.desktop_shortcut_var = tk.BooleanVar(value=False)
        self.start_shortcut_var = tk.BooleanVar(value=False)
        self.log_queue: queue.Queue = queue.Queue()
        self._poll_after_id = None
        self._job_running = False

        self._setup_style()
        self._build_ui()
        self.after(150, self._poll_log_queue)

    def t(self, key: str, **kwargs) -> str:
        text = STRINGS[self.lang][key]
        return text.format(**kwargs) if kwargs else text

    # ---------- window / pages ----------

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
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("HeadingOk.TLabel", font=("Segoe UI", 12, "bold"), foreground="#1d8049")
        style.configure("HeadingBad.TLabel", font=("Segoe UI", 12, "bold"), foreground="#b3261e")
        style.configure("Ok.TLabel", foreground="#1d8049")
        style.configure("Bad.TLabel", foreground="#b3261e")
        style.configure("Muted.TLabel", foreground="#6b717b")
        style.configure("Warn.TLabel", foreground="#8a6100")
        style.configure("Cmd.TLabel", font=("Consolas", 9), foreground="#3c414a")
        style.configure("Path.TLabel", font=("Segoe UI", 9, "bold"))

    def _build_ui(self):
        self.title(self.t("title"))
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)
        self.pages = {
            "welcome": self._build_welcome_page(),
            "deps": self._build_deps_page(),
            "folder": self._build_folder_page(),
            "summary": self._build_summary_page(),
            "progress": self._build_progress_page(),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")
        self._show_page("welcome")

    def _set_lang(self, lang: str):
        if lang == self.lang:
            return
        # NOTE: the toggle only exists on the welcome page, where nothing is in
        # flight - so rebuilding every page from scratch is the simplest way to
        # retranslate all of them at once.
        self.lang = lang
        self.container.destroy()
        self._build_ui()

    def _show_page(self, name: str):
        self.current_page = name
        self.pages[name].tkraise()
        if name == "welcome":
            self._render_welcome()
        elif name == "deps":
            self._refresh_status()
        elif name == "folder":
            self._render_folder_page()
        elif name == "summary":
            self._render_summary()

    def _new_page(self, heading_key: str):
        """A blank wizard page: heading on top, nav bar pinned to the bottom, body between."""
        frame = ttk.Frame(self.container, padding=(18, 14, 18, 14))
        heading = ttk.Label(frame, text=self.t(heading_key), style="Heading.TLabel")
        heading.pack(anchor="w")
        nav = ttk.Frame(frame)
        nav.pack(side="bottom", fill="x", pady=(10, 0))
        body = ttk.Frame(frame)
        body.pack(fill="both", expand=True, pady=(10, 0))
        return frame, heading, body, nav

    # ---------- welcome ----------

    def _build_welcome_page(self):
        frame = ttk.Frame(self.container, padding=(18, 14, 18, 14))

        top = ttk.Frame(frame)
        top.pack(fill="x")
        ttk.Label(top, text=self.t("welcome_heading"), style="Title.TLabel").pack(side="left")
        langs = ttk.Frame(top)
        langs.pack(side="right")
        for code in ("tr", "en"):
            btn = ttk.Button(langs, text=code.upper(), width=4, command=lambda c=code: self._set_lang(c))
            btn.pack(side="left", padx=(4, 0))
            if code == self.lang:
                btn.state(["disabled"])

        ttk.Label(frame, text=self.t("welcome_intro"), style="Muted.TLabel").pack(anchor="w", pady=(6, 14))

        for key, desc_key, mode, style in (
            ("install", "welcome_install_desc", MODE_INSTALL, "Primary.TButton"),
            ("repair", "welcome_repair_desc", MODE_REPAIR, "TButton"),
            ("remove", "welcome_remove_desc", MODE_REMOVE, "TButton"),
        ):
            ttk.Button(frame, text=self.t(key), style=style, command=lambda m=mode: self._start_mode(m)).pack(
                fill="x", ipady=6
            )
            ttk.Label(frame, text=self.t(desc_key), style="Muted.TLabel").pack(anchor="w", pady=(2, 12))

        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=(4, 12))
        ttk.Button(frame, text=self.t("docker"), command=self._docker_soon).pack(fill="x", ipady=4)
        ttk.Label(frame, text=self.t("docker_desc"), style="Muted.TLabel").pack(anchor="w", pady=(2, 0))

        self.remembered_label = ttk.Label(frame, text="", style="Muted.TLabel", wraplength=620, justify="left")
        self.remembered_label.pack(side="bottom", anchor="w")
        return frame

    def _render_welcome(self):
        remembered = load_last_install_dir()
        if remembered and is_installed(remembered):
            self.remembered_label.config(text=self.t("remembered_install", folder=remembered))
        else:
            self.remembered_label.config(text="")

    def _docker_soon(self):
        messagebox.showinfo(self.t("docker_soon_title"), self.t("docker_soon"))

    def _start_mode(self, mode: str):
        self.mode = mode
        self.folder_prefilled = False
        if mode in (MODE_REPAIR, MODE_REMOVE):
            # NOTE: the remembered folder is only trusted if it still holds an
            # install - if the user deleted it by hand, pre-filling it would
            # point Remove at a folder that isn't MediaGrab's any more.
            remembered = load_last_install_dir()
            if remembered and is_installed(remembered):
                self.base_dir = remembered
                self.folder_prefilled = True
            elif is_installed(base_dir()):
                self.base_dir = base_dir()
        self._show_page("folder" if mode == MODE_REMOVE else "deps")

    # ---------- requirements ----------

    def _build_deps_page(self):
        frame, _heading, body, nav = self._new_page("requirements")
        min_text = ".".join(str(p) for p in MIN_PYTHON)
        ttk.Label(
            body, text=self.t("deps_intro", min=min_text), style="Muted.TLabel", wraplength=620, justify="left"
        ).pack(anchor="w", pady=(0, 12))

        git_row = ttk.Frame(body)
        git_row.pack(fill="x", pady=4)
        self.git_status_label = ttk.Label(git_row, text=f"Git: {self.t('checking')}")
        self.git_status_label.pack(side="left")
        self.git_download_btn = ttk.Button(
            git_row, text=f"Git {self.t('download')}", command=lambda: webbrowser.open(GIT_DOWNLOAD_URL)
        )
        self.git_download_btn.pack(side="right")

        python_row = ttk.Frame(body)
        python_row.pack(fill="x", pady=4)
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
        ffmpeg_row = ttk.Frame(body)
        ffmpeg_row.pack(fill="x", pady=4)
        self.ffmpeg_status_label = ttk.Label(ffmpeg_row, text=f"ffmpeg: {self.t('checking')}")
        self.ffmpeg_status_label.pack(side="left")
        self.ffmpeg_copy_btn = ttk.Button(ffmpeg_row, text=self.t("copy"), command=self._copy_ffmpeg_command)
        self.ffmpeg_copy_btn.pack(side="right")
        self.ffmpeg_cmd_label = ttk.Label(body, text="", style="Cmd.TLabel")
        self.ffmpeg_cmd_label.pack(fill="x")
        self.ffmpeg_note_label = ttk.Label(body, text="", style="Warn.TLabel", wraplength=620, justify="left")
        self.ffmpeg_note_label.pack(fill="x")

        refresh_row = ttk.Frame(body)
        refresh_row.pack(fill="x", pady=(12, 0))
        self.deps_blocked_label = ttk.Label(
            refresh_row, text=self.t("deps_blocked"), style="Warn.TLabel", wraplength=460, justify="left"
        )
        ttk.Button(refresh_row, text=self.t("refresh"), command=self._refresh_status).pack(side="right")

        ttk.Button(nav, text=self.t("back"), command=lambda: self._show_page("welcome")).pack(side="left")
        self.deps_next_btn = ttk.Button(
            nav, text=self.t("next"), style="Primary.TButton", command=lambda: self._show_page("folder")
        )
        self.deps_next_btn.pack(side="right")
        return frame

    def _copy_ffmpeg_command(self):
        command = ffmpeg_install_command()
        self.clipboard_clear()
        self.clipboard_append(command)
        original = self.ffmpeg_copy_btn.cget("text")
        self.ffmpeg_copy_btn.config(text=self.t("copied"))
        self.after(1500, lambda: self.ffmpeg_copy_btn.config(text=original))

    def _refresh_status(self):
        # NOTE: before probing anything - the whole point of the Refresh button
        # is to notice a tool the user installed while this window was open.
        refresh_path_from_registry()

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

        # NOTE: ffmpeg deliberately does NOT gate installing - it's needed to
        # download, not to install, and the user may well fix it afterwards.
        # Git and a new enough Python genuinely are required to get this far.
        tools_ok = bool(self.git_path and python_ok)
        self.deps_next_btn.config(state="normal" if tools_ok else "disabled")
        if tools_ok:
            self.deps_blocked_label.pack_forget()
        else:
            self.deps_blocked_label.pack(side="left", fill="x", expand=True)

    # ---------- folder ----------

    def _build_folder_page(self):
        frame, _heading, body, nav = self._new_page("page_folder")
        self.folder_intro_label = ttk.Label(body, text="", style="Muted.TLabel", wraplength=620, justify="left")
        self.folder_intro_label.pack(anchor="w", pady=(0, 10))

        row = ttk.Frame(body)
        row.pack(fill="x")
        self.folder_label = ttk.Label(row, text=self.base_dir, style="Path.TLabel", wraplength=500, justify="left")
        self.folder_label.pack(side="left", fill="x", expand=True)
        self.browse_btn = ttk.Button(row, text=self.t("browse"), command=self._choose_folder)
        self.browse_btn.pack(side="right", padx=(10, 0))

        # NOTE: permanent holder frames keep the hint and the checkboxes in a
        # fixed position while their contents are packed/forgotten per mode.
        hint_holder = ttk.Frame(body)
        hint_holder.pack(fill="x", pady=(8, 0))
        self.folder_hint_label = ttk.Label(hint_holder, text="", style="Warn.TLabel", wraplength=620, justify="left")

        self.shortcuts_holder = ttk.Frame(body)
        self.shortcuts_holder.pack(fill="x", pady=(16, 0))
        self.desktop_check = ttk.Checkbutton(
            self.shortcuts_holder, text=self.t("desktop_shortcut"), variable=self.desktop_shortcut_var
        )
        self.start_check = ttk.Checkbutton(
            self.shortcuts_holder, text=self.t("start_shortcut"), variable=self.start_shortcut_var
        )

        self.folder_back_btn = ttk.Button(nav, text=self.t("back"))
        self.folder_back_btn.pack(side="left")
        self.folder_next_btn = ttk.Button(nav, text=self.t("next"), style="Primary.TButton", command=self._folder_next)
        self.folder_next_btn.pack(side="right")
        return frame

    def _render_folder_page(self):
        intro_key = {
            MODE_INSTALL: "folder_intro_install",
            MODE_REPAIR: "folder_intro_repair",
            MODE_REMOVE: "folder_intro_remove",
        }[self.mode]
        self.folder_intro_label.config(text=self.t(intro_key))
        self.folder_label.config(text=self.base_dir)

        installed = is_installed(self.base_dir)
        hints = []
        can_continue = True
        if is_unsafe_target(self.base_dir):
            hints.append(self.t("folder_unsafe_short"))
            can_continue = False
        elif self.mode == MODE_INSTALL:
            if installed:
                hints.append(self.t("folder_already_installed"))
                can_continue = False
            else:
                service = cloud_service_in_path(self.base_dir)
                if service:
                    hints.append(self.t("warn_cloud", service=service).splitlines()[0])
        else:
            if not installed:
                hints.append(self.t("folder_not_installed"))
                can_continue = False
            elif self.folder_prefilled:
                hints.append(self.t("folder_remembered_hint"))

        self.folder_hint_label.config(text="\n".join(hints))
        if hints:
            self.folder_hint_label.pack(fill="x")
        else:
            self.folder_hint_label.pack_forget()

        if self.mode == MODE_REMOVE:
            self.desktop_check.pack_forget()
            self.start_check.pack_forget()
        else:
            # NOTE: shortcuts are Windows-only (.lnk via PowerShell); greying
            # the boxes out elsewhere answers "what do these do?" without text.
            shortcut_state = "normal" if os.name == "nt" else "disabled"
            self.desktop_check.config(state=shortcut_state)
            self.start_check.config(state=shortcut_state)
            self.desktop_check.pack(side="left")
            self.start_check.pack(side="left", padx=(16, 0))

        self.folder_back_btn.config(
            command=lambda: self._show_page("welcome" if self.mode == MODE_REMOVE else "deps")
        )
        self.folder_next_btn.config(state="normal" if can_continue else "disabled")

    def _choose_folder(self):
        chosen = filedialog.askdirectory(initialdir=self.base_dir, mustexist=True)
        if not chosen:
            return
        chosen = os.path.abspath(chosen)
        if is_unsafe_target(chosen):
            messagebox.showerror(self.t("err_unsafe_title"), self.t("err_unsafe", folder=chosen))
            return
        self.base_dir = chosen
        self.folder_prefilled = False
        self._render_folder_page()

    def _folder_next(self):
        if self.mode == MODE_INSTALL and not self._confirm_target_folder():
            return
        self._show_page("summary")

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

    # ---------- summary ----------

    def _build_summary_page(self):
        frame, _heading, body, nav = self._new_page("page_summary")
        self.summary_body = ttk.Frame(body)
        self.summary_body.pack(fill="both", expand=True)
        ttk.Button(nav, text=self.t("back"), command=lambda: self._show_page("folder")).pack(side="left")
        self.summary_action_btn = ttk.Button(nav, text="", style="Primary.TButton", command=self._start_job)
        self.summary_action_btn.pack(side="right")
        return frame

    def _render_summary(self):
        for child in self.summary_body.winfo_children():
            child.destroy()

        action_key = {MODE_INSTALL: "install", MODE_REPAIR: "repair", MODE_REMOVE: "remove"}[self.mode]
        ffmpeg_ok = bool(self.ffmpeg_ver and self.ffprobe_ver)
        rows = [("summary_action", self.t(action_key)), ("summary_folder", self.base_dir)]
        if self.mode != MODE_REMOVE:
            python = ".".join(str(p) for p in self.python_ver) if self.python_ver else "?"
            tools = f"Git ✓ · Python {python} ✓ · " + (f"ffmpeg {self.ffmpeg_ver} ✓" if ffmpeg_ok else "ffmpeg ✗")
            rows.append(("summary_tools", tools))
            chosen = [
                self.t(key)
                for key, var in (("desktop_shortcut", self.desktop_shortcut_var), ("start_shortcut", self.start_shortcut_var))
                if var.get()
            ]
            rows.append(("summary_shortcuts", ", ".join(chosen) if chosen else self.t("summary_none")))

        grid = ttk.Frame(self.summary_body)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        for i, (key, value) in enumerate(rows):
            ttk.Label(grid, text=self.t(key), style="Path.TLabel").grid(row=i, column=0, sticky="nw", padx=(0, 12), pady=2)
            ttk.Label(grid, text=value, wraplength=480, justify="left").grid(row=i, column=1, sticky="w", pady=2)

        notes = []
        if self.mode == MODE_REMOVE:
            notes.append(self.t("summary_remove_note"))
        else:
            if os.path.isfile(os.path.join(self.base_dir, _launcher_name())):
                notes.append(self.t("summary_overwrite_launcher", name=_launcher_name()))
            if self._shortcut_would_be_overwritten():
                notes.append(self.t("summary_overwrite_shortcut"))
            if not ffmpeg_ok:
                notes.append(self.t("summary_ffmpeg_missing"))
        for note in notes:
            ttk.Label(self.summary_body, text=note, style="Warn.TLabel", wraplength=620, justify="left").pack(
                anchor="w", pady=(10, 0)
            )

        if self.mode == MODE_INSTALL:
            ttk.Label(self.summary_body, text=self.t("ready_title"), style="Path.TLabel").pack(anchor="w", pady=(18, 0))
            ttk.Label(self.summary_body, text=self.t("ready_steps"), style="Muted.TLabel", justify="left").pack(
                anchor="w", pady=(6, 0)
            )
        self.summary_action_btn.config(text=self.t(action_key))

    def _shortcut_would_be_overwritten(self) -> bool:
        if os.name != "nt":
            return False
        for csidl, var in ((CSIDL_DESKTOPDIRECTORY, self.desktop_shortcut_var), (CSIDL_PROGRAMS, self.start_shortcut_var)):
            if not var.get():
                continue
            folder = _known_folder(csidl)
            if folder and os.path.isfile(os.path.join(folder, "MediaGrab.lnk")):
                return True
        return False

    def _start_job(self):
        if self._job_running:
            return
        want_desktop = self.desktop_shortcut_var.get()
        want_start = self.start_shortcut_var.get()
        if self.mode == MODE_REMOVE:
            if not messagebox.askyesno(self.t("remove_confirm_title"), self.t("remove_confirm")):
                return
            self._run_async(self._do_remove)
        elif self.mode == MODE_REPAIR:
            self._run_async(lambda: self._do_repair(want_desktop, want_start))
        else:
            self._run_async(lambda: self._do_install(want_desktop, want_start))

    # ---------- progress ----------

    def _build_progress_page(self):
        frame, heading, body, nav = self._new_page("page_progress")
        self.progress_heading = heading
        self.progress = ttk.Progressbar(body, mode="indeterminate")
        self.progress.pack(fill="x", pady=(0, 8))
        self.log_text = scrolledtext.ScrolledText(
            body, state="disabled", font=("Consolas", 9), bg="#1e1e1e", fg="#d8d8d8", height=10
        )
        self.log_text.pack(fill="both", expand=True)

        self.launch_btn = ttk.Button(nav, text=self.t("launch"), style="Primary.TButton", command=self._launch_app)
        self.progress_close_btn = ttk.Button(nav, text=self.t("close"), command=self.destroy)
        self.progress_close_btn.pack(side="right")
        self.progress_home_btn = ttk.Button(nav, text=self.t("home"), command=lambda: self._show_page("welcome"))
        self.progress_home_btn.pack(side="right", padx=(0, 8))
        return frame

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

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _run_async(self, fn):
        self._job_running = True
        self._clear_log()
        self.progress_heading.config(text=self.t(PROGRESS_TITLE_KEYS[self.mode]), style="Heading.TLabel")
        self.launch_btn.pack_forget()
        for btn in (self.progress_home_btn, self.progress_close_btn):
            btn.config(state="disabled")
        # NOTE: git/pip give no usable percentage, so this is an indeterminate
        # "still working" indicator rather than a fake bar.
        self.progress.configure(mode="indeterminate", value=0)
        self.progress.start(12)
        self._show_page("progress")

        def wrapper():
            ok = False
            try:
                ok = bool(fn())
            except Exception as exc:  # surface anything unexpected in the log instead of crashing silently
                self.log(self.t("err_generic", msg=exc))
            finally:
                self.log_queue.put(("done", ok))

        threading.Thread(target=wrapper, daemon=True).start()

    def _on_job_done(self, ok: bool):
        self._job_running = False
        self.progress.stop()
        # NOTE: a stopped indeterminate bar freezes with a stray block in it;
        # a full bar reads as "complete", an empty one as "didn't".
        self.progress.configure(mode="determinate", maximum=100, value=100 if ok else 0)
        self.progress_heading.config(
            text=self.t("done_ok" if ok else "done_fail"), style="HeadingOk.TLabel" if ok else "HeadingBad.TLabel"
        )
        if ok and self.mode in (MODE_INSTALL, MODE_REPAIR):
            save_last_install_dir(self.base_dir)
            if os.path.isfile(os.path.join(self.base_dir, _launcher_name())):
                self.launch_btn.pack(side="left", ipady=4)
        elif ok and self.mode == MODE_REMOVE:
            # NOTE: only forget the remembered folder if it's the one that was
            # just emptied - removing some other, older install must not lose it.
            remembered = load_last_install_dir()
            if remembered and same_folder(remembered, self.base_dir):
                forget_last_install_dir()
        for btn in (self.progress_home_btn, self.progress_close_btn):
            btn.config(state="normal")

    # ---------- logging / threading plumbing ----------

    def log(self, message: str):
        self.log_queue.put(message)

    def _poll_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if isinstance(msg, tuple):
                    self._on_job_done(msg[1])
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
        # calls the venv's own python.exe by full path sidesteps that. An
        # existing launcher is simply overwritten - a Repair may need to point
        # it at a recreated venv.
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

    def _do_install(self, want_desktop: bool = False, want_start: bool = False) -> bool:
        # NOTE: `git clone <url> .` refuses to run in a non-empty directory,
        # and this folder always has at least the setup exe/script itself in
        # it - so we clone the long way instead (init + remote + fetch +
        # checkout), which has no such restriction.
        self.log(self.t("log_installing", folder=self.base_dir))
        if not self._run_cmd([self.git_path, "init"], cwd=self.base_dir):
            self.log(self.t("err_git_init"))
            return False
        if not self._run_cmd([self.git_path, "remote", "add", "origin", REPO_URL], cwd=self.base_dir):
            self.log(self.t("err_remote"))
            return False
        if not self._run_cmd([self.git_path, "fetch", "origin"], cwd=self.base_dir):
            self.log(self.t("err_fetch"))
            return False
        if not self._run_cmd([self.git_path, "remote", "set-head", "origin", "-a"], cwd=self.base_dir):
            self.log(self.t("err_head"))
            return False
        branch = self._default_branch()
        if not self._run_cmd([self.git_path, "checkout", "-B", branch, f"origin/{branch}"], cwd=self.base_dir):
            self.log(self.t("err_checkout"))
            return False
        if not self._setup_venv_and_deps():
            return False
        if want_desktop or want_start:
            self._create_shortcuts(want_desktop, want_start)
        self.log(self.t("log_done"))
        self.log(self.t("log_launch_hint", name=_launcher_name()))
        if not (self.ffmpeg_ver and self.ffprobe_ver):
            self.log(self.t("log_ffmpeg_missing"))
        return True

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
        # NOTE: CreateShortcut + Save overwrites an existing MediaGrab.lnk, so
        # a shortcut left by an older install is refreshed rather than duplicated.
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

    def _do_repair(self, want_desktop: bool = False, want_start: bool = False) -> bool:
        if is_git_repo(self.base_dir):
            self.log(self.t("log_updating"))
            if self._run_cmd([self.git_path, "pull"], cwd=self.base_dir):
                if not self._setup_venv_and_deps():
                    return False
                self.log(self.t("log_update_done"))
                if want_desktop or want_start:
                    self._create_shortcuts(want_desktop, want_start)
                return True
            self.log(self.t("log_pull_failed"))

        self.log(self.t("log_keep_data"))
        stash_dir = self._stash_user_data()
        self.log(self.t("log_removing_old"))
        self._wipe_app_files()
        self._restore_user_data(stash_dir)
        return self._do_install(want_desktop, want_start)

    def _do_remove(self) -> bool:
        self.log(self.t("log_keep_data"))
        stash_dir = self._stash_user_data()
        self.log(self.t("log_removing"))
        self._wipe_app_files()
        self._restore_user_data(stash_dir)
        self.log(self.t("log_removed"))
        return True

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
