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

import os
import queue
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox, scrolledtext

REPO_URL = "https://github.com/umitkrkmz/mediagrab.git"
GIT_DOWNLOAD_URL = "https://git-scm.com/downloads"
PYTHON_DOWNLOAD_URL = "https://www.python.org/downloads/"
USER_DATA_ENTRIES = ("indirilenler", "channels.json")


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
        self.title("MediaGrab Kurulum")
        self.geometry("680x560")
        self.minsize(620, 460)

        self.base_dir = base_dir()
        self.git_path = None
        self.python_path = None
        self.log_queue: queue.Queue = queue.Queue()

        self._build_widgets()
        self._refresh_status()
        self.after(150, self._poll_log_queue)

    # ---------- UI ----------

    def _build_widgets(self):
        top = tk.Frame(self)
        top.pack(fill="x", padx=14, pady=(14, 6))
        tk.Label(top, text=f"Kurulum klasörü: {self.base_dir}", anchor="w", wraplength=640, justify="left").pack(
            fill="x"
        )

        status = tk.LabelFrame(self, text="Gereksinimler")
        status.pack(fill="x", padx=14, pady=8)

        git_row = tk.Frame(status)
        git_row.pack(fill="x", padx=10, pady=(8, 4))
        self.git_status_label = tk.Label(git_row, text="Git: kontrol ediliyor...", anchor="w")
        self.git_status_label.pack(side="left")
        self.git_download_btn = tk.Button(
            git_row, text="Git'i indir", command=lambda: webbrowser.open(GIT_DOWNLOAD_URL)
        )
        self.git_download_btn.pack(side="right")

        python_row = tk.Frame(status)
        python_row.pack(fill="x", padx=10, pady=4)
        self.python_status_label = tk.Label(python_row, text="Python: kontrol ediliyor...", anchor="w")
        self.python_status_label.pack(side="left")
        self.python_download_btn = tk.Button(
            python_row, text="Python'ı indir", command=lambda: webbrowser.open(PYTHON_DOWNLOAD_URL)
        )
        self.python_download_btn.pack(side="right")

        refresh_row = tk.Frame(status)
        refresh_row.pack(fill="x", padx=10, pady=(4, 8))
        tk.Button(refresh_row, text="Durumu yenile", command=self._refresh_status).pack(side="right")

        shortcuts_row = tk.Frame(self)
        shortcuts_row.pack(fill="x", padx=14, pady=(0, 4))
        self.desktop_shortcut_var = tk.BooleanVar(value=False)
        self.start_shortcut_var = tk.BooleanVar(value=False)
        tk.Checkbutton(shortcuts_row, text="Masaüstüne kısayol ekle", variable=self.desktop_shortcut_var).pack(
            side="left"
        )
        tk.Checkbutton(shortcuts_row, text="Başlat menüsüne ekle", variable=self.start_shortcut_var).pack(
            side="left", padx=(16, 0)
        )

        actions = tk.Frame(self)
        actions.pack(fill="x", padx=14, pady=8)
        for col in range(3):
            actions.columnconfigure(col, weight=1)
        self.install_btn = tk.Button(actions, text="Kur", command=self.on_install)
        self.install_btn.grid(row=0, column=0, sticky="ew", padx=4, ipady=4)
        self.repair_btn = tk.Button(actions, text="Onar / Güncelle", command=self.on_repair)
        self.repair_btn.grid(row=0, column=1, sticky="ew", padx=4, ipady=4)
        self.remove_btn = tk.Button(actions, text="Kaldır", command=self.on_remove)
        self.remove_btn.grid(row=0, column=2, sticky="ew", padx=4, ipady=4)

        self.log_text = scrolledtext.ScrolledText(self, state="disabled", font=("Consolas", 9), bg="#1e1e1e", fg="#d8d8d8")
        self.log_text.pack(fill="both", expand=True, padx=14, pady=(6, 12))

        note = (
            "Not: ffmpeg ayrıca kurulmalı (kurulum bunu yapmaz) - MediaGrab'ı ilk "
            "çalıştırmadan önce README'deki ffmpeg adımını uygulayın."
        )
        tk.Label(self, text=note, anchor="w", wraplength=640, justify="left", fg="#767b84").pack(
            fill="x", padx=14, pady=(0, 12)
        )

    def _refresh_status(self):
        self.git_path = find_tool("git")
        self.python_path = find_tool("python", "python3", "py")

        # NOTE: deliberately not showing the resolved path here - it can be
        # long enough to push the button on the right off the edge of the
        # window. It's still logged in full when an action actually runs.
        self.git_status_label.config(text="Git: bulundu ✓" if self.git_path else "Git: bulunamadı ✗")
        self.git_download_btn.config(state="normal" if not self.git_path else "disabled")

        self.python_status_label.config(text="Python: bulundu ✓" if self.python_path else "Python: bulunamadı ✗")
        self.python_download_btn.config(state="normal" if not self.python_path else "disabled")

        installed = is_installed(self.base_dir)
        tools_ok = bool(self.git_path and self.python_path)

        self.install_btn.config(state="normal" if (tools_ok and not installed) else "disabled")
        self.repair_btn.config(state="normal" if (tools_ok and installed) else "disabled")
        self.remove_btn.config(state="normal" if installed else "disabled")

    def _set_buttons_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in (self.install_btn, self.repair_btn, self.remove_btn):
            btn.config(state=state)
        if enabled:
            self._refresh_status()

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
        self.after(150, self._poll_log_queue)

    def _run_async(self, fn):
        self._set_buttons_enabled(False)

        def wrapper():
            try:
                fn()
            except Exception as exc:  # surface anything unexpected in the log instead of crashing silently
                self.log(f"HATA: {exc}")
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
        self.log("Sanal ortam oluşturuluyor...")
        if not self._run_cmd([self.python_path, "-m", "venv", venv_dir], cwd=self.base_dir):
            self.log("HATA: Sanal ortam oluşturulamadı.")
            return False

        venv_python = venv_python_path(venv_dir)
        self.log("Bağımlılıklar kuruluyor (bu biraz sürebilir)...")
        if not self._run_cmd([venv_python, "-m", "pip", "install", "-r", "requirements.txt"], cwd=self.base_dir):
            self.log("HATA: Bağımlılıklar kurulamadı.")
            return False

        launcher_name = self._write_launcher(venv_python)
        self.log(f"'{launcher_name}' başlatma dosyası oluşturuldu.")
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
        want_desktop = self.desktop_shortcut_var.get()
        want_start = self.start_shortcut_var.get()
        self._run_async(lambda: self._do_install(want_desktop, want_start))

    def _do_install(self, want_desktop: bool = False, want_start: bool = False):
        # NOTE: `git clone <url> .` refuses to run in a non-empty directory,
        # and this folder always has at least the setup exe/script itself in
        # it - so we clone the long way instead (init + remote + fetch +
        # checkout), which has no such restriction.
        self.log(f"MediaGrab '{self.base_dir}' klasörüne kuruluyor...")
        if not self._run_cmd([self.git_path, "init"], cwd=self.base_dir):
            self.log("HATA: git init başarısız oldu.")
            return
        if not self._run_cmd([self.git_path, "remote", "add", "origin", REPO_URL], cwd=self.base_dir):
            self.log("HATA: remote eklenemedi.")
            return
        if not self._run_cmd([self.git_path, "fetch", "origin"], cwd=self.base_dir):
            self.log("HATA: fetch başarısız oldu.")
            return
        if not self._run_cmd([self.git_path, "remote", "set-head", "origin", "-a"], cwd=self.base_dir):
            self.log("HATA: uzak varsayılan dal bulunamadı.")
            return
        branch = self._default_branch()
        if not self._run_cmd([self.git_path, "checkout", "-B", branch, f"origin/{branch}"], cwd=self.base_dir):
            self.log("HATA: checkout başarısız oldu.")
            return
        if not self._setup_venv_and_deps():
            return
        if want_desktop or want_start:
            self._create_shortcuts(want_desktop, want_start)
        self.log("Kurulum tamamlandı.")
        self.log(f"Başlatmak için: '{_launcher_name()}' dosyasına çift tıklayın.")

    def _create_shortcuts(self, want_desktop: bool, want_start: bool):
        if os.name != "nt":
            self.log("Uyarı: kısayollar yalnızca Windows'ta destekleniyor.")
            return
        launcher_path = os.path.join(self.base_dir, _launcher_name())
        if not os.path.isfile(launcher_path):
            self.log("Uyarı: başlatma dosyası bulunamadığı için kısayol oluşturulamadı.")
            return
        if want_desktop:
            self._create_one_shortcut(CSIDL_DESKTOPDIRECTORY, "Masaüstüne", launcher_path)
        if want_start:
            self._create_one_shortcut(CSIDL_PROGRAMS, "Başlat menüsüne", launcher_path)

    def _create_one_shortcut(self, csidl: int, label: str, target: str):
        folder = _known_folder(csidl)
        if not folder:
            self.log(f"Uyarı: {label} kısayol eklenemedi (klasör bulunamadı).")
            return
        self.log(f"{label} kısayol ekleniyor...")
        link_path = os.path.join(folder, "MediaGrab.lnk")
        ps_cmd = (
            f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut({_ps_quote(link_path)}); "
            f"$s.TargetPath = {_ps_quote(target)}; "
            f"$s.WorkingDirectory = {_ps_quote(self.base_dir)}; "
            "$s.Save()"
        )
        if not self._run_cmd(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd], cwd=self.base_dir):
            self.log(f"Uyarı: {label} kısayol oluşturulamadı.")

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
            self.log("Mevcut kurulum güncelleniyor (git pull)...")
            if self._run_cmd([self.git_path, "pull"], cwd=self.base_dir):
                if self._setup_venv_and_deps():
                    self.log("Güncelleme tamamlandı.")
                    if want_desktop or want_start:
                        self._create_shortcuts(want_desktop, want_start)
                return
            self.log("git pull başarısız oldu, temiz kurulum deneniyor...")

        self.log("Kullanıcı verisi (indirilenler/, channels.json) korunuyor...")
        stash_dir = self._stash_user_data()
        self.log("Eski kurulum siliniyor...")
        self._wipe_app_files()
        self._restore_user_data(stash_dir)
        self._do_install(want_desktop, want_start)

    def on_remove(self):
        if not messagebox.askyesno(
            "Kaldırma onayı",
            "MediaGrab uygulaması bu klasörden kaldırılacak. "
            "İndirdiğiniz dosyalar (indirilenler/) ve takip listeniz (channels.json) korunacak. Devam edilsin mi?",
        ):
            return
        self._run_async(self._do_remove)

    def _do_remove(self):
        self.log("Kullanıcı verisi (indirilenler/, channels.json) korunuyor...")
        stash_dir = self._stash_user_data()
        self.log("Uygulama dosyaları siliniyor...")
        self._wipe_app_files()
        self._restore_user_data(stash_dir)
        self.log("Kaldırıldı. indirilenler/ ve channels.json korundu.")

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
                self.log(f"Uyarı: '{name}' silinemedi: {exc}")


if __name__ == "__main__":
    SetupApp().mainloop()
