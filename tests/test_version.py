"""MediaGrab's own version: the single version source, install-type detection,
and the "is there a newer release?" check against GitHub.

NOTE: no real network - every GitHub call is faked.
"""

import importlib.util
import inspect
import io
import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mediagrab import __version__, deps, paths
from mediagrab import app as app_module

ROOT = Path(__file__).resolve().parent.parent


# --- the single version source ------------------------------------------------


@pytest.mark.parametrize("section", ["## Türkçe", "## English"])
def test_version_matches_the_newest_changelog_entry(section):
    # NOTE: the guard against tagging a release without bumping __version__
    # (Settings would then call every fresh install outdated, or never notice
    # a real update) - both language sections must lead with this version.
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    after = changelog.split(section, 1)[1]
    newest = re.search(r"^### \[(\d+\.\d+\.\d+)\]", after, re.M).group(1)
    assert newest == __version__


def test_the_about_page_shows_the_version():
    with TestClient(app_module.app) as client:
        assert f"MediaGrab {__version__}" in client.get("/about?lang=en").text


# --- install type ---------------------------------------------------------------


def test_installer_launcher_names_match_the_installer():
    # NOTE: paths.INSTALLER_LAUNCHERS is a deliberate duplicate (the installer
    # runs before this package exists) - this keeps the two from drifting.
    spec = importlib.util.spec_from_file_location("setup_for_version_test", ROOT / "setup_mediagrab.py")
    setup_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(setup_mod)
    source = inspect.getsource(setup_mod._launcher_name)
    for name in paths.INSTALLER_LAUNCHERS:
        assert f'"{name}"' in source


def test_install_type_docker(monkeypatch):
    monkeypatch.setattr(paths, "is_docker", lambda: True)
    assert paths.install_type() == "docker"


def test_install_type_installer(monkeypatch, tmp_path):
    (tmp_path / "MediaGrab Baslat.bat").write_text("", encoding="utf-8")
    monkeypatch.setattr(paths, "is_docker", lambda: False)
    monkeypatch.setattr(paths, "app_dir", lambda: str(tmp_path))
    assert paths.install_type() == "installer"


def test_install_type_source(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "is_docker", lambda: False)
    monkeypatch.setattr(paths, "app_dir", lambda: str(tmp_path))
    assert paths.install_type() == "source"


# --- the GitHub release check ------------------------------------------------------


@pytest.fixture
def github(monkeypatch):
    """Fake GitHub: set .response (a dict, or an Exception to raise); counts calls."""

    class Fake:
        response = {"tag_name": "v9.9.9", "html_url": "https://github.com/umitkrkmz/mediagrab/releases/tag/v9.9.9"}
        calls = 0

    def fake_urlopen(req, timeout=None):
        Fake.calls += 1
        assert req.full_url == "https://api.github.com/repos/umitkrkmz/mediagrab/releases/latest"
        # NOTE: GitHub's API rejects requests without a User-Agent.
        assert req.get_header("User-agent", "").startswith("MediaGrab/")
        if isinstance(Fake.response, Exception):
            raise Fake.response
        return io.BytesIO(json.dumps(Fake.response).encode())

    monkeypatch.setattr(deps.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setitem(deps._release_cache, "expires", 0.0)
    monkeypatch.setitem(deps._release_cache, "value", None)
    return Fake


def test_a_newer_release_is_reported(github):
    result = deps.check_mediagrab_update()
    assert result["installed"] == __version__
    assert result["latest"] == "9.9.9"
    assert result["update_available"] is True
    assert result["release_url"].endswith("/tag/v9.9.9")


def test_the_same_release_is_not_an_update(github):
    github.response = {"tag_name": f"v{__version__}", "html_url": "u"}
    assert deps.check_mediagrab_update()["update_available"] is False


def test_an_older_release_is_not_an_update(github):
    # NOTE: a development build is ahead of the latest release - that's not
    # "outdated", and 2.10.0 vs 2.9.0 must compare numerically.
    github.response = {"tag_name": "v0.10.0", "html_url": "u"}
    assert deps.check_mediagrab_update()["update_available"] is False


def test_an_unreachable_github_means_unknown_not_an_error(github):
    github.response = OSError("no network")
    result = deps.check_mediagrab_update()
    assert result["update_available"] is None
    assert result["latest"] is None
    assert result["installed"] == __version__


def test_the_answer_is_cached(github):
    # NOTE: GitHub allows 60 unauthenticated requests an hour - opening
    # Settings repeatedly must not spend one each time.
    deps.check_mediagrab_update()
    deps.check_mediagrab_update()
    assert github.calls == 1


def test_a_failure_is_cached_too_but_briefly(github):
    github.response = OSError("no network")
    deps.check_mediagrab_update()
    deps.check_mediagrab_update()
    assert github.calls == 1
    assert deps._RELEASE_FAILURE_CACHE_SECONDS < deps._RELEASE_CACHE_SECONDS


def test_the_route_reports_the_install_type(github, monkeypatch):
    monkeypatch.setattr(deps, "install_type", lambda: "docker")
    with TestClient(app_module.app) as client:
        body = client.get("/api/mediagrab-version").json()
    assert body["install_type"] == "docker"
    assert body["latest"] == "9.9.9"


# --- Docker: "docker compose pull" needs the published image -------------------


def test_the_repo_compose_file_uses_the_published_image():
    # NOTE: Settings tells Docker users to run "docker compose pull" - which
    # does nothing for a compose file that builds locally with `build: .`.
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert re.search(r"^\s*image:\s*ghcr\.io/umitkrkmz/mediagrab:latest\s*$", compose, re.M)
    assert not re.search(r"^\s*build:", compose, re.M)
