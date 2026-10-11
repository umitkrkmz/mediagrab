"""The uninstaller's "delete my downloads" helper (mediagrab/uninstall.py).

NOTE: works on the isolated folders from conftest.py plus tmp_path.
"""

from pathlib import Path

from mediagrab import paths, store, uninstall


def _write(path: Path, data: bytes = b"x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _folder_with_downloads(tmp_path) -> Path:
    folder = tmp_path / "Videolarım"
    _write(folder / "Kanal Ç" / "Video.mp4", b"12345")
    _write(folder / "Kanal Ç" / "Video.json", b"{}")
    _write(folder / "Şarkı.mp3", b"123")
    _write(folder / "tatil.jpg")  # the user's own file
    store.save_settings(download_dir=str(folder))
    return folder


def test_summary_counts_what_history_shows(tmp_path):
    folder = _folder_with_downloads(tmp_path)
    assert uninstall.summary() == [str(folder), "3", "10", "1"]


def test_summary_never_creates_a_missing_folder(tmp_path, monkeypatch):
    missing = tmp_path / "Downloads" / "MediaGrab"
    monkeypatch.setattr(uninstall, "default_download_dir", lambda: str(missing))
    assert uninstall.summary() == [str(missing), "0", "0", "0"]
    assert not missing.exists()


def test_delete_removes_only_mediagrabs_files(tmp_path):
    folder = _folder_with_downloads(tmp_path)
    assert uninstall.delete_downloads() == ["3", "0"]
    assert not (folder / "Kanal Ç").exists(), "the emptied channel folder goes too"
    assert (folder / "tatil.jpg").exists(), "the user's own file stays"
    assert folder.is_dir(), "and so does the folder holding it"


def test_an_emptied_download_folder_is_removed(tmp_path):
    folder = _folder_with_downloads(tmp_path)
    (folder / "tatil.jpg").unlink()
    uninstall.delete_downloads()
    assert not folder.exists()


def test_a_file_that_cant_be_deleted_is_counted(tmp_path, monkeypatch):
    folder = _folder_with_downloads(tmp_path)
    real_remove = uninstall.os.remove

    def busy(path):
        if path.endswith("Video.mp4"):
            raise PermissionError("in use")
        return real_remove(path)

    monkeypatch.setattr(uninstall.os, "remove", busy)
    assert uninstall.delete_downloads() == ["2", "1"]
    assert (folder / "Kanal Ç" / "Video.mp4").exists()


def test_main_writes_lines_the_installer_reads(tmp_path):
    # NOTE: UTF-8 with a BOM - how Inno's LoadStringsFromFile knows it's UTF-8.
    folder = _folder_with_downloads(tmp_path)
    out = tmp_path / "out.txt"
    assert uninstall.main(["summary", str(out)]) == 0
    raw = out.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert raw.decode("utf-8-sig").splitlines() == [str(folder), "3", "10", "1"]


def test_main_refuses_anything_else(tmp_path):
    assert uninstall.main(["delete-everything", str(tmp_path / "out.txt")]) == 2
    assert uninstall.main([]) == 2


def test_the_default_folder_is_the_one_downloads_use(tmp_path, monkeypatch):
    # NOTE: no setting -> the same default the app downloads into.
    monkeypatch.setattr(uninstall, "default_download_dir", paths.default_download_dir)
    assert uninstall.download_folder() == paths.default_download_dir()
