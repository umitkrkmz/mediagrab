"""Keeps maps/ honest.

NOTE: a hand-written map that drifts from the code is worse than no map -
an agent will trust it and look in the wrong place. So every file in the
repo has to be listed in project-map.md, and every route in app.py in
site-map.md; adding one without the other fails here.
"""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT_MAP = ROOT / "maps" / "project-map.md"
SITE_MAP = ROOT / "maps" / "site-map.md"


def _repo_files() -> list[str]:
    # NOTE: tracked AND untracked-but-not-ignored, so a freshly added file has
    # to be mapped before it's even committed.
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return sorted(line.strip() for line in out.splitlines() if line.strip())


def _directory_rows(text: str) -> set[str]:
    # NOTE: only a directory listed as its own TABLE ROW (`| \`dir/\` | ...`)
    # covers the files under it - that's how sixteen logo files get one row.
    # A directory name in a heading or in prose must NOT count, or a heading
    # like "Backend — `mediagrab/`" would silently cover every file in the
    # package and the guard would catch nothing (it did, once).
    return set(re.findall(r"^\| `([^`]+/)` \|", text, flags=re.MULTILINE))


def _mentioned(path: str, text: str, directory_rows: set[str]) -> bool:
    if f"`{path}`" in text:
        return True
    parts = path.split("/")
    return any(f"{'/'.join(parts[:i])}/" in directory_rows for i in range(1, len(parts)))


def test_every_repo_file_is_on_the_project_map():
    text = PROJECT_MAP.read_text(encoding="utf-8")
    directory_rows = _directory_rows(text)
    missing = [p for p in _repo_files() if not _mentioned(p, text, directory_rows)]
    assert not missing, f"add to maps/project-map.md: {missing}"


def test_a_directory_in_a_heading_does_not_count_as_coverage():
    text = PROJECT_MAP.read_text(encoding="utf-8")
    assert "`mediagrab/static/icons/`" in text  # the one legitimate directory row
    assert _directory_rows(text) == {"mediagrab/static/icons/"}, _directory_rows(text)


def test_the_project_map_lists_no_file_that_does_not_exist():
    text = PROJECT_MAP.read_text(encoding="utf-8")
    listed = set(re.findall(r"`([A-Za-z0-9_./-]+\.[a-z]+)`", text))
    # NOTE: entries starting with "/" are URLs (`/sw.js`), not files.
    stale = sorted(p for p in listed if "/" in p and not p.startswith("/") and not (ROOT / p).exists())
    assert not stale, f"listed in maps/project-map.md but gone: {stale}"


def _routes() -> list[tuple[str, str]]:
    source = (ROOT / "mediagrab" / "app.py").read_text(encoding="utf-8")
    return re.findall(r'@app\.(get|post|delete|put)\(\s*"([^"]+)"', source)


def test_app_has_routes_to_map():
    assert len(_routes()) > 20


def test_every_route_is_on_the_site_map():
    text = SITE_MAP.read_text(encoding="utf-8")
    missing = [f"{method.upper()} {path}" for method, path in _routes() if f"`{path}`" not in text]
    assert not missing, f"add to maps/site-map.md: {missing}"


def test_the_site_map_lists_no_route_that_does_not_exist():
    text = SITE_MAP.read_text(encoding="utf-8")
    real = {path for _method, path in _routes()}
    listed = set(re.findall(r"^\| `(/[^`]*)` \|", text, flags=re.MULTILINE))
    stale = sorted(listed - real)
    assert not stale, f"listed in maps/site-map.md but not in app.py: {stale}"


def test_every_template_is_on_the_site_map():
    text = SITE_MAP.read_text(encoding="utf-8")
    templates = sorted(p.name for p in (ROOT / "mediagrab" / "templates").glob("*.html"))
    missing = [name for name in templates if name != "base.html" and f"`{name}`" not in text]
    assert not missing, f"page templates missing from maps/site-map.md: {missing}"
