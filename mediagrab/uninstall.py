"""Clean-up for the Windows uninstaller: what MediaGrab downloaded, and deleting it.

    python -m mediagrab.uninstall summary <out.txt>
    python -m mediagrab.uninstall delete-downloads <out.txt>

Run by packaging/mediagrab.iss with the embedded Python while it still exists
(before the program files are removed); the answer goes to <out.txt> as
plain lines, which Inno's Pascal reads easily:

    summary           -> folder, number of files, bytes, MB (rounded up)
    delete-downloads  -> files deleted, files that couldn't be

NOTE: "delete my downloads" deletes what History shows (mover.movable_files:
MediaGrab's file types + their .json info files), never the whole folder -
someone may have pointed MediaGrab at a folder that holds their own files
too. Folders this emptied are removed; the rest stays.

NOTE: deleting MediaGrab's own data folder (settings, channels, cookies,
statistics) needs no Python - the uninstaller does that itself.
"""

import os
import sys

from . import mover, store
from .paths import default_download_dir


def download_folder() -> str:
    # NOTE: downloader.download_dir() without its side effects - it creates
    # the folder (and importing downloader loads yt-dlp); an uninstaller
    # asking "how many videos are there?" must not make a new folder.
    return store.get_settings().get("download_dir") or default_download_dir()


def summary() -> list[str]:
    folder = download_folder()
    files = mover.movable_files(folder, mover.HISTORY_EXTS)
    total = sum(size for _rel, size in files)
    # NOTE: MB as well, rounded up - Pascal shows that without 64-bit maths.
    return [folder, str(len(files)), str(total), str(-(-total // (1024 * 1024)))]


def delete_downloads() -> list[str]:
    folder = download_folder()
    deleted, failed, emptied = 0, 0, set()
    for rel, _size in mover.movable_files(folder, mover.HISTORY_EXTS):
        path = os.path.join(folder, rel)
        try:
            os.remove(path)
            deleted += 1
            emptied.add(os.path.dirname(path))
        except OSError:
            failed += 1
    mover._remove_emptied_dirs(folder, emptied)
    return [str(deleted), str(failed)]


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] not in ("summary", "delete-downloads"):
        print(__doc__)
        return 2
    lines = summary() if argv[0] == "summary" else delete_downloads()
    # NOTE: UTF-8 with a BOM - Inno's LoadStringsFromFile reads that as UTF-8
    # (folder names like "İndirilenler" / "Müzik").
    with open(argv[1], "w", encoding="utf-8-sig") as f:
        f.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
