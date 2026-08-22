"""Tests for the browser-side helpers in static/app.js.

NOTE: app.js touches the DOM as soon as it loads, so it can't simply be
imported in Node. These tests lift the self-contained pure functions out of
the shipped file and run them under Node instead - which means they test the
code that actually ships, not a copy. Skipped when Node isn't installed.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

APP_JS = Path(__file__).resolve().parent.parent / "mediagrab" / "static" / "app.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


def _extract(pattern: str) -> str:
    source = APP_JS.read_text(encoding="utf-8")
    match = re.search(pattern, source, re.S)
    assert match, f"could not find {pattern!r} in app.js - was it renamed?"
    return match.group(0)


def _run_js(snippet: str, expression: str):
    """Evaluate `expression` against helpers pulled out of app.js."""
    script = f"{snippet}\nprocess.stdout.write(JSON.stringify({expression}));"
    result = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, encoding="utf-8", timeout=30
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def escape_html():
    return _extract(r"const HTML_ESCAPES = \{.*?\};") + "\n" + _extract(r"function escapeHtml\(str\) \{.*?\n\}")


# --- escapeHtml -------------------------------------------------------------


def test_escapes_the_html_structural_characters(escape_html):
    assert _run_js(escape_html, "escapeHtml('<b>a & b</b>')") == "&lt;b&gt;a &amp; b&lt;/b&gt;"


def test_escapes_quotes(escape_html):
    # NOTE: the bug this guards. The old implementation set textContent and
    # read innerHTML back, which escapes & < > but NOT quotes - and almost
    # every caller interpolates into an attribute (title="...", data-*="...").
    assert _run_js(escape_html, "escapeHtml('\"')") == "&quot;"
    assert _run_js(escape_html, "escapeHtml(\"'\")") == "&#39;"


def test_a_crafted_title_cannot_break_out_of_an_attribute(escape_html):
    # NOTE: video titles come from arbitrary third-party sites, so they are
    # untrusted input. Unescaped, this closed the attribute and injected a
    # live event handler.
    payload = 'x" onmouseover="alert(1)'
    escaped = _run_js(escape_html, f"escapeHtml({json.dumps(payload)})")
    assert '"' not in escaped
    assert "&quot;" in escaped


def test_ordinary_titles_survive_unchanged(escape_html):
    title = "Sir Ken Robinson: Do schools kill creativity?"
    assert _run_js(escape_html, f"escapeHtml({json.dumps(title)})") == title


def test_null_and_undefined_render_as_empty_string(escape_html):
    # NOTE: a missing uploader/title used to print the literal text "undefined".
    assert _run_js(escape_html, "escapeHtml(null)") == ""
    assert _run_js(escape_html, "escapeHtml(undefined)") == ""


def test_escaping_is_not_applied_twice(escape_html):
    # NOTE: documents the contract - callers must escape exactly once. An
    # already-escaped string legitimately gets its & escaped again.
    assert _run_js(escape_html, "escapeHtml('&amp;')") == "&amp;amp;"


# --- shipped-file sanity ----------------------------------------------------


def test_app_js_parses():
    result = subprocess.run(["node", "--check", str(APP_JS)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_service_worker_parses():
    sw = APP_JS.parent / "sw.js"
    result = subprocess.run(["node", "--check", str(sw)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
