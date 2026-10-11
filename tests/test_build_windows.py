"""packaging/build_windows.py's own logic (not the download/staging itself).

NOTE: runs anywhere - a fake staging folder in tmp_path, no network.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "packaging"))

import build_windows  # noqa: E402


def _wheel(site: Path, folder: str, metadata: str) -> None:
    (site / folder).mkdir(parents=True)
    (site / folder / "METADATA").write_text(metadata, encoding="utf-8")


def _stage(tmp_path) -> Path:
    stage = tmp_path / "MediaGrab"
    site = stage / "python" / "Lib" / "site-packages"
    _wheel(site, "yt_dlp-2026.8.19.dist-info", "Name: yt-dlp\nVersion: 2026.8.19\nLicense-Expression: Unlicense\n")
    _wheel(
        site,
        "Jinja2-3.1.6.dist-info",
        "Name: Jinja2\nVersion: 3.1.6\nClassifier: License :: OSI Approved :: BSD License\n",
    )
    _wheel(site, "mutagen-1.48.1.dist-info", "Name: mutagen\nVersion: 1.48.1\nLicense: GPL-2.0-or-later\n")
    (site / "yt_dlp").mkdir()  # a package folder, not a dist-info
    return stage


def test_every_staged_package_is_listed_with_its_license(tmp_path):
    text = build_windows.notices_text(str(_stage(tmp_path)), "2.4.0")
    for name, version, license_name in [
        ("yt-dlp", "2026.8.19", "Unlicense"),
        ("Jinja2", "3.1.6", "BSD License"),
        ("mutagen", "1.48.1", "GPL-2.0-or-later"),
    ]:
        row = next(line for line in text.splitlines() if line.strip().startswith(name + " "))
        assert version in row and license_name in row
    assert "python\\Lib\\site-packages\\mutagen-1.48.1.dist-info" in text
    assert "yt_dlp " not in text, "only dist-info folders are packages"


def test_ffmpeg_points_at_its_exact_source(tmp_path):
    # NOTE: FFmpeg is GPL - the exact build and its source must be findable.
    text = build_windows.notices_text(str(_stage(tmp_path)), "2.4.0")
    commit = build_windows.FFMPEG_ASSET.split("-g", 1)[1].split("-", 1)[0]
    assert f"https://github.com/FFmpeg/FFmpeg/tree/{commit}" in text
    assert build_windows.FFMPEG_TAG in text
    assert build_windows.FFMPEG_ASSET in text


def test_mediagrab_and_python_with_their_sources(tmp_path):
    text = build_windows.notices_text(str(_stage(tmp_path)), "2.4.0")
    assert "https://github.com/umitkrkmz/mediagrab/tree/v2.4.0" in text
    assert f"Python {build_windows.PYTHON_VERSION}" in text
    assert "PSF License" in text


def test_written_into_the_package_root(tmp_path, monkeypatch):
    stage = _stage(tmp_path)
    build_windows.write_notices(str(stage))
    raw = (stage / build_windows.NOTICES_NAME).read_bytes()
    assert b"yt-dlp" in raw
    assert b"\r\n" in raw, "Notepad-friendly line endings"


# --- shown by the app: About -> third-party software ---------------------------------

from fastapi.testclient import TestClient  # noqa: E402

from mediagrab import app as app_module  # noqa: E402


def test_the_app_serves_the_notices_the_build_writes(tmp_path, monkeypatch):
    install = tmp_path / "MediaGrab"
    install.mkdir()
    (install / build_windows.NOTICES_NAME).write_text("FFmpeg - GPL\r\n", encoding="utf-8-sig")
    monkeypatch.setattr(app_module, "windows_install_dir", lambda: str(install))
    assert app_module.NOTICES_NAME == build_windows.NOTICES_NAME
    with TestClient(app_module.app) as client:
        res = client.get("/third-party-notices")
        about = client.get("/about").text
    assert res.status_code == 200 and "FFmpeg - GPL" in res.text
    assert res.headers["content-type"].startswith("text/plain")
    assert 'href="/third-party-notices"' in about


def test_no_notices_outside_the_windows_package(monkeypatch):
    monkeypatch.setattr(app_module, "windows_install_dir", lambda: None)
    with TestClient(app_module.app) as client:
        assert client.get("/third-party-notices").status_code == 404
        assert "third-party-notices" not in client.get("/about").text
