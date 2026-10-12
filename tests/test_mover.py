"""Moving downloads between folders (mediagrab/mover.py) - the safety rules.

NOTE: every test works in its own tmp_path; "another drive" is simulated by
making mover._same_drive say no, which takes the copy -> check -> delete path.
"""

import os
import shutil

import pytest

from mediagrab import mover

EXTS = {"mp3", "m4a", "opus", "mp4", "mkv", "srt", "txt"}


def _write(path, data=b"x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


@pytest.fixture
def other_drive(monkeypatch):
    monkeypatch.setattr(mover, "_same_drive", lambda a, b: False)


@pytest.mark.parametrize("drive", ["same", "other"])
def test_moves_history_files_with_their_info_and_channel_folders(tmp_path, monkeypatch, drive):
    if drive == "other":
        monkeypatch.setattr(mover, "_same_drive", lambda a, b: False)
    old, new = tmp_path / "old", tmp_path / "new"
    _write(old / "Kanal Ç" / "Video.mp4", b"video")
    _write(old / "Kanal Ç" / "Video.json", b"{}")
    _write(old / "Kanal Ç" / "Video.tr.srt", b"sub")
    _write(old / "Şarkı.mp3", b"song")
    result = mover.move_files(str(old), str(new), EXTS)
    assert result["moved"] == 4 and result["conflicts"] == [] and result["failed"] == []
    assert (new / "Kanal Ç" / "Video.mp4").read_bytes() == b"video"
    assert (new / "Kanal Ç" / "Video.json").exists()
    assert (new / "Kanal Ç" / "Video.tr.srt").exists()
    assert (new / "Şarkı.mp3").read_bytes() == b"song"
    assert not old.exists(), "the old folder is removed once this move emptied it"
    assert not list(new.rglob("*" + mover.TEMP_SUFFIX))


def test_other_files_in_the_old_folder_are_left_alone(tmp_path):
    # NOTE: the old folder may have been someone's own folder too.
    old, new = tmp_path / "old", tmp_path / "new"
    _write(old / "Video.mp4")
    _write(old / "tatil.jpg")
    _write(old / "ayarlar.json")  # a .json with no video of that name
    (old / "Boş Klasör").mkdir()
    result = mover.move_files(str(old), str(new), EXTS)
    assert result["moved"] == 1
    assert (old / "tatil.jpg").exists() and (old / "ayarlar.json").exists()
    assert (old / "Boş Klasör").is_dir(), "an empty folder of the user's isn't ours to delete"
    assert not (new / "tatil.jpg").exists()


def test_never_overwrites_a_different_file(tmp_path):
    old, new = tmp_path / "old", tmp_path / "new"
    _write(old / "Kanal" / "Video.mp4", b"old one")
    _write(new / "Kanal" / "Video.mp4", b"a different video")
    result = mover.move_files(str(old), str(new), EXTS)
    assert result["conflicts"] == ["Kanal/Video.mp4"]
    assert result["moved"] == 0
    assert (old / "Kanal" / "Video.mp4").read_bytes() == b"old one"
    assert (new / "Kanal" / "Video.mp4").read_bytes() == b"a different video"


def test_a_rerun_finishes_a_file_copied_but_not_yet_deleted(tmp_path, other_drive):
    # NOTE: interrupted between "copied" and "original deleted".
    old, new = tmp_path / "old", tmp_path / "new"
    _write(old / "Video.mp4", b"video")
    new.mkdir()
    shutil.copy2(old / "Video.mp4", new / "Video.mp4")
    result = mover.move_files(str(old), str(new), EXTS)
    assert result["moved"] == 1 and result["conflicts"] == []
    assert not (old / "Video.mp4").exists()
    assert (new / "Video.mp4").read_bytes() == b"video"


def test_a_half_copied_temp_file_is_simply_copied_again(tmp_path, other_drive):
    old, new = tmp_path / "old", tmp_path / "new"
    _write(old / "Video.mp4", b"the whole video")
    _write(new / ("Video.mp4" + mover.TEMP_SUFFIX), b"the wh")
    result = mover.move_files(str(old), str(new), EXTS)
    assert result["moved"] == 1
    assert (new / "Video.mp4").read_bytes() == b"the whole video"
    assert not (new / ("Video.mp4" + mover.TEMP_SUFFIX)).exists()


def test_another_drive_keeps_the_file_time(tmp_path, other_drive):
    old, new = tmp_path / "old", tmp_path / "new"
    source = _write(old / "Video.mp4")
    os.utime(source, (1_600_000_000, 1_600_000_000))
    mover.move_files(str(old), str(new), EXTS)
    # NOTE: History sorts by this - a move mustn't make old videos "new".
    assert int(os.path.getmtime(new / "Video.mp4")) == 1_600_000_000


def test_a_bad_copy_keeps_the_original(tmp_path, other_drive, monkeypatch):
    old, new = tmp_path / "old", tmp_path / "new"
    _write(old / "Video.mp4", b"the whole video")

    def short_copy(src, dst):
        with open(dst, "wb") as f:
            f.write(b"the wh")

    monkeypatch.setattr(mover.shutil, "copy2", short_copy)
    result = mover.move_files(str(old), str(new), EXTS)
    assert result["failed"] == ["Video.mp4"] and result["moved"] == 0
    assert (old / "Video.mp4").read_bytes() == b"the whole video"
    assert not (new / "Video.mp4").exists()
    assert not list(new.rglob("*" + mover.TEMP_SUFFIX))


def test_a_file_in_use_is_skipped_and_the_rest_move(tmp_path, monkeypatch):
    old, new = tmp_path / "old", tmp_path / "new"
    _write(old / "Playing.mp4")
    _write(old / "Other.mp4")
    real_rename = os.rename

    def busy(src, dst):
        if "Playing" in str(src):
            raise PermissionError("in use")
        return real_rename(src, dst)

    monkeypatch.setattr(mover.os, "rename", busy)
    result = mover.move_files(str(old), str(new), EXTS)
    assert result["failed"] == ["Playing.mp4"] and result["moved"] == 1
    assert (old / "Playing.mp4").exists() and (new / "Other.mp4").exists()
    assert old.is_dir(), "not emptied - stays"


def test_not_enough_space_on_the_other_drive_touches_nothing(tmp_path, other_drive, monkeypatch):
    old, new = tmp_path / "old", tmp_path / "new"
    _write(old / "Video.mp4", b"x" * 1000)
    monkeypatch.setattr(mover.shutil, "disk_usage", lambda p: shutil._ntuple_diskusage(10**12, 10**12, 500))
    with pytest.raises(mover.NotEnoughSpace) as info:
        mover.move_files(str(old), str(new), EXTS)
    assert info.value.needed == 1000
    assert (old / "Video.mp4").exists()
    assert not (new / "Video.mp4").exists()


def test_the_same_drive_needs_no_free_space(tmp_path, monkeypatch):
    # NOTE: a rename takes no extra room - a nearly full disk still works.
    old, new = tmp_path / "old", tmp_path / "new"
    _write(old / "Video.mp4", b"x" * 1000)
    monkeypatch.setattr(mover.shutil, "disk_usage", lambda p: shutil._ntuple_diskusage(10**12, 10**12, 0))
    assert mover.move_files(str(old), str(new), EXTS)["moved"] == 1


def test_a_current_folder_inside_the_old_one_is_not_moved_into_itself(tmp_path):
    old = tmp_path / "Videolar"
    new = old / "MediaGrab"
    _write(old / "Eski.mp4")
    _write(new / "Yeni.mp4")
    result = mover.move_files(str(old), str(new), EXTS, exclude=str(new))
    assert result["moved"] == 1
    assert (new / "Eski.mp4").exists() and (new / "Yeni.mp4").exists()
    assert not (new / "MediaGrab").exists()


def test_progress_reaches_the_total(tmp_path):
    old, new = tmp_path / "old", tmp_path / "new"
    _write(old / "a.mp4", b"12345")
    _write(old / "b.mp3", b"123")
    seen = []
    mover.move_files(str(old), str(new), EXTS, progress=lambda done, total: seen.append((done, total)))
    assert seen[-1] == (8, 8)


def test_is_inside():
    base = os.path.abspath("Videolar")
    assert mover.is_inside(os.path.join(base, "Kanal"), base)
    assert mover.is_inside(base, base)
    assert not mover.is_inside(base + " 2", base)
