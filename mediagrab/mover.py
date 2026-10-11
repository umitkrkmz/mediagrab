"""Moving downloads from an old downloads folder into the current one.

Used by Settings -> Download folder -> "Move here" (app.py). Only what
History shows is moved - the media/subtitle/transcript files (the `exts`
passed in, app.py's HISTORY_EXTS) and each one's "<name>.json" info file -
with their channel subfolders. Anything else in the old folder is left
alone: it may be someone's own folder that also held other files.

Safety rules (agreed for v2.4.0, see the tests in test_mover.py):
  - free space is checked first when the copy goes to another drive;
  - same drive: a rename; another drive: copy -> check the size -> only then
    delete the original;
  - nothing is ever overwritten: a different file already at the target is
    skipped and reported;
  - an interrupted move loses nothing and running it again carries on: a file
    left behind at the target by an earlier run (same size and time) counts
    as moved, a half-copied temp file is simply copied again;
  - only folders that this move emptied are removed, the old folder itself
    included; anything else left there keeps them in place.
"""

import os
import shutil
from typing import Callable, Optional

# NOTE: the file types History lists - what MediaGrab itself downloads. Kept
# here (app.py uses it as HISTORY_EXTS) so the uninstaller's clean-up
# (uninstall.py) can use it without loading the whole web app.
HISTORY_EXTS = {"mp3", "m4a", "opus", "mp4", "mkv", "srt", "txt"}
# NOTE: a copy in progress, so a half-written file never sits at the final
# name (History would show it, and a rerun would take it for a finished one).
TEMP_SUFFIX = ".mediagrab-move"
# NOTE: on top of the files themselves, like _has_enough_disk_space's margin
# for downloads - a disk filled to the last byte breaks other programs too.
SPACE_MARGIN_BYTES = 100 * 1024 * 1024


class NotEnoughSpace(Exception):
    def __init__(self, needed: int, free: int):
        super().__init__(f"needed {needed} bytes, {free} free")
        self.needed = needed
        self.free = free


def _key(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def is_inside(path: str, folder: str) -> bool:
    """True if `path` is `folder` itself or somewhere below it."""
    path, folder = _key(path), _key(folder)
    return path == folder or path.startswith(folder.rstrip(os.sep) + os.sep)


def movable_files(src: str, exts: set[str], exclude: Optional[str] = None) -> list[tuple[str, int]]:
    """(path relative to src, size) of everything a move would take.

    NOTE: `exclude` is the current downloads folder when it lies INSIDE the
    old one (old D:\\Videos, new D:\\Videos\\MediaGrab) - those files are
    already where they belong.
    """
    found = []
    if not os.path.isdir(src):
        return found
    for root, dirs, files in os.walk(src):
        if exclude:
            dirs[:] = [d for d in dirs if not is_inside(os.path.join(root, d), exclude)]
        media_stems = set()
        for name in files:
            stem, ext = os.path.splitext(name)
            if ext[1:].lower() in exts:
                media_stems.add(stem)
        for name in files:
            stem, ext = os.path.splitext(name)
            ext = ext[1:].lower()
            if ext in exts or (ext == "json" and stem in media_stems):
                path = os.path.join(root, name)
                try:
                    size = os.path.getsize(path)
                except OSError:
                    continue
                found.append((os.path.relpath(path, src), size))
    return found


def count_shown(files: list[tuple[str, int]], exts: set[str]) -> int:
    """How many of movable_files' files History would list.

    NOTE: what a person counts - "3 videos", not "6 files" with each one's
    .json info file (seen in the dev19 test). The .json files still move and
    still count towards the size.
    """
    return sum(1 for rel, _size in files if os.path.splitext(rel)[1][1:].lower() in exts)


def _same_drive(a: str, b: str) -> bool:
    try:
        return os.stat(a).st_dev == os.stat(b).st_dev
    except OSError:
        return False


def _already_there(src: str, dst: str) -> bool:
    # NOTE: a file an earlier, interrupted run finished copying but never got
    # to delete the original of: copy2 keeps the modification time, so size
    # AND time matching means it's the same file, not a namesake.
    try:
        a, b = os.stat(src), os.stat(dst)
    except OSError:
        return False
    return a.st_size == b.st_size and int(a.st_mtime) == int(b.st_mtime)


def move_files(
    src: str,
    dst: str,
    exts: set[str],
    exclude: Optional[str] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> dict:
    """Move src's History files into dst; return what happened.

    Raises NotEnoughSpace (before touching anything) if the files have to be
    copied to another drive that can't hold them.
    """
    files = movable_files(src, exts, exclude)
    os.makedirs(dst, exist_ok=True)
    same_drive = _same_drive(src, dst)
    if not same_drive:
        needed = sum(size for _rel, size in files)
        free = shutil.disk_usage(dst).free
        if needed + SPACE_MARGIN_BYTES > free:
            raise NotEnoughSpace(needed, free)

    result = {"moved": 0, "bytes": 0, "conflicts": [], "failed": []}
    emptied_dirs = set()
    total = sum(size for _rel, size in files)
    done = 0
    for rel, size in files:
        source = os.path.join(src, rel)
        target = os.path.join(dst, rel)
        shown = rel.replace(os.sep, "/")
        try:
            if os.path.exists(target):
                if not _already_there(source, target):
                    result["conflicts"].append(shown)
                    continue
                os.remove(source)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                if same_drive:
                    os.rename(source, target)
                else:
                    temp = target + TEMP_SUFFIX
                    shutil.copy2(source, temp)
                    if os.path.getsize(temp) != os.path.getsize(source):
                        os.remove(temp)
                        raise OSError("size mismatch after copy")
                    # NOTE: checked again right before - os.rename silently
                    # replaces an existing file on Linux.
                    if os.path.exists(target):
                        os.remove(temp)
                        result["conflicts"].append(shown)
                        continue
                    os.rename(temp, target)
                    os.remove(source)
            result["moved"] += 1
            result["bytes"] += size
            emptied_dirs.add(os.path.dirname(source))
        except OSError:
            # NOTE: e.g. the file is open in a player right now - it stays
            # where it is, untouched, and is listed; the rest carry on.
            result["failed"].append(shown)
        finally:
            done += size
            if progress:
                progress(done, total)
    _remove_emptied_dirs(src, emptied_dirs)
    return result


def _remove_emptied_dirs(src: str, dirs: set[str]) -> None:
    # NOTE: only folders a moved file came out of (and their parents up to
    # the old downloads folder itself) - an empty folder the user made there
    # for their own reasons isn't ours to delete. rmdir only ever removes an
    # EMPTY folder, so anything still inside keeps it.
    candidates = set()
    for folder in dirs:
        while is_inside(folder, src):
            candidates.add(_key(folder))
            if _key(folder) == _key(src):
                break
            folder = os.path.dirname(folder)
    for folder in sorted(candidates, key=len, reverse=True):
        try:
            os.rmdir(folder)
        except OSError:
            pass
