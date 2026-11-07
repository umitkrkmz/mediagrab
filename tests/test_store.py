"""The Microsoft Store (MSIX) build: how it is recognised (paths.is_store_package,
install_type "store") and what it refuses - updating its own packages, which
Store policy 10.2.2 and the read-only package folder both rule out.

NOTE: a real packaged run can't happen inside pytest; packaging/msix's local
install (Developer Mode) is where the True path was seen working for real.
"""

import ctypes
import os

import pytest
from fastapi.testclient import TestClient

import mediagrab.app as app_module
from mediagrab import paths, store

windows_only = pytest.mark.skipif(os.name != "nt", reason="package identity is a Windows API")


@pytest.fixture
def fresh_detection():
    # NOTE: is_store_package is cached for the life of the process - each test
    # here must ask Windows (or the fake) again.
    paths.is_store_package.cache_clear()
    yield
    paths.is_store_package.cache_clear()


def _fake_windll(result: int):
    kernel32 = type("Kernel32", (), {"GetCurrentPackageFullName": staticmethod(lambda length, name: result)})
    return type("WinDLL", (), {"kernel32": kernel32})


# --- detection ------------------------------------------------------------------


@windows_only
def test_this_test_process_has_no_package_identity(fresh_detection):
    # NOTE: the real API, not a fake - pytest runs from a plain python.exe.
    assert paths.is_store_package() is False


@windows_only
@pytest.mark.parametrize(
    "result, packaged",
    [
        (122, True),  # ERROR_INSUFFICIENT_BUFFER: has a name, wants a buffer for it
        (15700, False),  # APPMODEL_ERROR_NO_PACKAGE
        (0, False),
        (87, False),  # ERROR_INVALID_PARAMETER - anything unexpected is "not packaged"
    ],
)
def test_package_identity_comes_from_windows(fresh_detection, monkeypatch, result, packaged):
    monkeypatch.setattr(ctypes, "windll", _fake_windll(result))
    assert paths.is_store_package() is packaged


@windows_only
def test_no_api_means_not_packaged(fresh_detection, monkeypatch):
    # NOTE: Windows 7 has no GetCurrentPackageFullName.
    monkeypatch.setattr(ctypes, "windll", type("WinDLL", (), {"kernel32": object()}))
    assert paths.is_store_package() is False


def test_never_packaged_outside_windows(fresh_detection, monkeypatch):
    monkeypatch.setattr(paths.os, "name", "posix")
    assert paths.is_store_package() is False


def test_install_type_store_wins_over_the_shared_windows_layout(monkeypatch, tmp_path):
    # NOTE: the Store package has the Windows installer's app\ + python\
    # layout too - identity is what tells them apart.
    (tmp_path / "app").mkdir()
    (tmp_path / "python").mkdir()
    monkeypatch.setattr(paths, "is_docker", lambda: False)
    monkeypatch.setattr(paths, "app_dir", lambda: str(tmp_path / "app"))
    monkeypatch.setattr(paths, "is_store_package", lambda: True)
    assert paths.install_type() == "store"
    monkeypatch.setattr(paths, "is_store_package", lambda: False)
    assert paths.install_type() == "windows"


# --- what the Store build refuses -------------------------------------------------


@pytest.fixture
def client_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setattr(store, "STORE_PATH", str(tmp_path / "channels.json"))
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: None)


@pytest.mark.parametrize(
    "route, module, function",
    [
        ("/api/ytdlp-update", "downloader", "update_ytdlp"),
        ("/api/dependencies-update", "deps", "update_dependencies"),
    ],
)
def test_self_updates_are_refused_in_the_store_build(client_settings, monkeypatch, route, module, function):
    monkeypatch.setattr(app_module, "is_store_package", lambda: True)
    calls = []
    monkeypatch.setattr(getattr(app_module, module), function, lambda: calls.append(1))

    with TestClient(app_module.app) as client:
        res = client.post(route)

    assert res.status_code == 400
    assert "Store" in res.json()["detail"]
    # NOTE: refused before pip is ever started - not "tried and failed".
    assert calls == []


def test_ytdlp_update_still_runs_outside_the_store_build(client_settings, monkeypatch):
    monkeypatch.setattr(app_module, "is_store_package", lambda: False)
    monkeypatch.setattr(app_module.downloader, "update_ytdlp", lambda: {"ok": False, "output": "x"})

    with TestClient(app_module.app) as client:
        res = client.post("/api/ytdlp-update")

    assert res.status_code == 200
    assert res.json() == {"ok": False, "output": "x"}


@pytest.mark.parametrize("packaged", [True, False])
def test_version_routes_report_is_store(client_settings, monkeypatch, packaged):
    # NOTE: Settings uses this to show "comes with Store updates" instead of
    # the update buttons.
    monkeypatch.setattr(app_module, "is_store_package", lambda: packaged)
    monkeypatch.setattr(
        app_module.downloader,
        "check_ytdlp_update",
        lambda: {"installed": "2026.08.19", "latest": None, "update_available": None},
    )
    monkeypatch.setattr(
        app_module.deps, "check_dependencies", lambda: {"reachable": True, "packages": [], "update_count": 0}
    )

    with TestClient(app_module.app) as client:
        ytdlp = client.get("/api/ytdlp-version").json()
        deps = client.get("/api/dependencies").json()

    assert ytdlp["is_store"] is packaged
    assert deps["is_store"] is packaged


def test_msix_manifest_version_matches_the_app():
    # NOTE: the Store package's version is written by hand in the manifest;
    # a release that forgets it ships a package reporting the old number (and
    # the Store refuses an upload that doesn't go up). The 4th part is the
    # Store's own and must stay 0.
    import xml.etree.ElementTree as ET

    from mediagrab import __version__

    manifest = os.path.join(os.path.dirname(__file__), "..", "packaging", "msix", "AppxManifest.xml")
    ns = {"m": "http://schemas.microsoft.com/appx/manifest/foundation/windows10"}
    identity = ET.parse(manifest).getroot().find("m:Identity", ns)
    assert identity.get("Version") == f"{__version__}.0"
    assert identity.get("Name") == "umitkrkmz.MediaGrab"
