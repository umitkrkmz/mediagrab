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


# --- yt-dlp update command / JS runtime status --------------------------------


def test_manual_update_command_matches_the_in_app_update():
    # NOTE: the copyable "update manually" command must install the same
    # extras as the button - quoted, since PowerShell splits an unquoted
    # "yt-dlp[default,deno]" at the comma.
    from mediagrab.downloader import YTDLP_PIP_SPEC

    snippet = _extract(r"const YTDLP_PIP_CMD = .*?;")
    assert _run_js(snippet, "YTDLP_PIP_CMD") == f'pip install --upgrade "{YTDLP_PIP_SPEC}"'


@pytest.fixture(scope="module")
def js_runtime_missing():
    return _extract(r"function jsRuntimeMissing\(info\) \{.*?\n\}")


@pytest.mark.parametrize(
    "info, expected",
    [
        ({"js_runtime": "deno", "js_solver": "0.8.0"}, False),
        ({"js_runtime": None, "js_solver": "0.8.0"}, True),
        ({"js_runtime": "deno", "js_solver": None}, True),
        # NOTE: the version request itself failed - nothing is known, so no
        # "missing" warning (and no update button) on that basis alone.
        ({"installed": None}, False),
    ],
)
def test_js_runtime_missing(js_runtime_missing, info, expected):
    assert _run_js(js_runtime_missing, f"jsRuntimeMissing({json.dumps(info)})") is expected



# --- Settings: Docker-aware version sections ---------------------------------


@pytest.fixture(scope="module")
def offer_update():
    return (
        _extract(r"function jsRuntimeMissing\(info\) \{.*?\n\}")
        + "\n"
        + _extract(r"function shouldOfferYtdlpUpdate\(info\) \{.*?\n\}")
    )


@pytest.mark.parametrize(
    "info, expected",
    [
        ({"update_available": True, "js_runtime": "deno", "js_solver": "0.8.0"}, True),
        ({"update_available": True, "js_runtime": "deno", "js_solver": "0.8.0", "is_docker": True}, True),
        ({"update_available": False, "js_runtime": None, "js_solver": None, "is_docker": False}, True),
        # NOTE: in Docker the button can't fix a missing runtime (the image
        # ships Deno; a --user install's binary isn't on yt-dlp's search path)
        ({"update_available": False, "js_runtime": None, "js_solver": None, "is_docker": True}, False),
        ({"update_available": False, "js_runtime": "deno", "js_solver": "0.8.0"}, False),
    ],
)
def test_should_offer_ytdlp_update(offer_update, info, expected):
    assert _run_js(offer_update, f"shouldOfferYtdlpUpdate({json.dumps(info)})") is expected


@pytest.fixture(scope="module")
def instructions_html():
    # NOTE: t() and escapeHtml are stubbed - this is about which blocks are
    # present, not their wording.
    return (
        "const t = () => new Proxy({}, { get: (_, key) => key });\n"
        "const escapeHtml = (s) => s;\n"
        + _extract(r"const YTDLP_PIP_CMD = .*?;")
        + "\n"
        + _extract(r"function ytdlpInstructionsHtml\(isDocker\) \{.*?\n\}")
    )


def test_ytdlp_instructions_keep_the_update_button_in_docker(instructions_html):
    html = _run_js(instructions_html, "ytdlpInstructionsHtml(true)")
    assert "ytdlp-update-now-btn" in html
    assert "ytdlp-manual" not in html
    assert ".venv" not in html


def test_ytdlp_instructions_include_manual_steps_outside_docker(instructions_html):
    html = _run_js(instructions_html, "ytdlpInstructionsHtml(false)")
    assert "ytdlp-update-now-btn" in html
    assert "ytdlp-manual" in html


# --- Settings: uploaded cookies.txt review list -------------------------------


@pytest.fixture(scope="module")
def cookie_review(escape_html):
    return (
        escape_html
        + "\nconst t = () => new Proxy({cookieErrors: {json: 'JSON!'}}, { get: (o, key) => o[key] ?? key });\n"
        + _extract(r"function cookieErrorText\(code\) \{.*?\n\}")
        + "\n"
        + _extract(r"function cookieReviewHtml\(info\) \{.*?\n\}")
    )


def test_cookie_review_pre_ticks_only_the_suggested_sites(cookie_review):
    info = {"sites": [{"site": "youtube.com", "count": 3}, {"site": "mybank.example", "count": 1}],
            "suggested": ["youtube.com"]}
    html = _run_js(cookie_review, f"cookieReviewHtml({json.dumps(info)})")
    assert re.search(r'value="youtube\.com" checked', html)
    assert re.search(r'value="mybank\.example">', html)


def test_cookie_review_escapes_site_names_from_the_file(cookie_review):
    # NOTE: site names come straight out of an uploaded file.
    info = {"sites": [{"site": '"><img src=x onerror=alert(1)>', "count": 1}], "suggested": []}
    html = _run_js(cookie_review, f"cookieReviewHtml({json.dumps(info)})")
    assert "<img" not in html
    assert "&lt;img" in html


def test_cookie_error_codes_map_to_messages(cookie_review):
    assert _run_js(cookie_review, "cookieErrorText('json')") == "JSON!"


@pytest.fixture(scope="module")
def cookie_current_text():
    return (
        "const t = () => ({cookieCurrentUploaded: 'U {sites}/{n}', cookieCurrentPath: 'P {path} {sites}/{n}',"
        " cookieUploadedAt: 'up {date}', cookieUpdatedAt: 'upd {date}'});\n"
        + _extract(r"function cookieCurrentText\(data, fmtDate\) \{.*?\n\}")
    )


def test_cookie_summary_shows_upload_and_last_update_separately(cookie_current_text):
    data = {"source": "uploaded", "path": None, "uploaded_at": "A",
            "summary": {"sites": [1, 2], "total": 3, "updated_at": "B"}}
    assert _run_js(cookie_current_text, f"cookieCurrentText({json.dumps(data)}, (d) => d)") == "U 2/3 · up A · upd B"


def test_cookie_summary_for_a_typed_path_has_no_upload_time(cookie_current_text):
    data = {"source": "path", "path": "C:/x.txt", "uploaded_at": None,
            "summary": {"sites": [1], "total": 5, "updated_at": "B"}}
    assert _run_js(cookie_current_text, f"cookieCurrentText({json.dumps(data)}, (d) => d)") == "P C:/x.txt 1/5 · upd B"


# --- error messages: pointing sign-in failures at Settings -> Cookies ---------


@pytest.fixture(scope="module")
def error_hints(escape_html):
    return (
        escape_html
        + "\nconst t = () => new Proxy({}, { get: (_, key) => key });\n"
        + _extract(r"const ERROR_PATTERNS = \[.*?\n\];")
        + "\n"
        + _extract(r"function friendlyErrorEntry\(raw\) \{.*?\n\}")
        + "\n"
        + _extract(r"function cookieHintHtml\(entry, configured, settingsHref\) \{.*?\n\}")
    )


AGE = "ERROR: [youtube] x: Sign in to confirm your age. This video may be inappropriate for some users."


@pytest.mark.parametrize(
    "raw, key",
    [
        (AGE, "errAgeRestricted"),
        # NOTE: the precise side message wins over the generic age error it
        # always arrives with (downloader.probe appends it on a new line).
        (AGE + "\n[youtube] The provided YouTube account cookies are no longer valid.", "errCookiesExpired"),
        (AGE + "\n[youtube] x: This video is age-restricted and YouTube is requiring account age-verification",
         "errAgeVerification"),
    ],
)
def test_the_most_precise_explanation_wins(error_hints, raw, key):
    assert _run_js(error_hints, f"friendlyErrorEntry({json.dumps(raw)}).key") == key


def test_age_restricted_points_to_cookie_settings(error_hints):
    html = _run_js(error_hints, f"cookieHintHtml(friendlyErrorEntry({json.dumps(AGE)}), false, '/settings?lang=tr#cookies')")
    assert "errCookieHintOff" in html
    assert 'href="/settings?lang=tr#cookies"' in html


def test_the_hint_changes_when_cookies_are_already_set(error_hints):
    html = _run_js(error_hints, f"cookieHintHtml(friendlyErrorEntry({json.dumps(AGE)}), true, '/s')")
    assert "errCookieHintOn" in html


@pytest.mark.parametrize(
    "raw",
    [
        # NOTE: a new cookies.txt can't fix account age-verification - no
        # pointer to the cookie settings there, it'd send people in circles.
        AGE + "\n[youtube] x: This video is age-restricted and YouTube is requiring account age-verification",
        "ERROR: Unsupported URL: https://example.com",
    ],
)
def test_no_cookie_hint_where_cookies_cant_help(error_hints, raw):
    assert _run_js(error_hints, f"cookieHintHtml(friendlyErrorEntry({json.dumps(raw)}), false, '/s')") == ""


def test_a_browser_cookie_failure_gets_a_friendly_message_and_the_cookie_link(error_hints):
    # NOTE: the exact message seen on a real Windows machine with Chrome selected.
    raw = "ERROR: Could not copy Chrome cookie database. See  https://github.com/yt-dlp/yt-dlp/issues/7271  for more info"
    assert _run_js(error_hints, f"friendlyErrorEntry({json.dumps(raw)}).key") == "errBrowserCookies"
    assert "errCookieHintOn" in _run_js(error_hints, f"cookieHintHtml(friendlyErrorEntry({json.dumps(raw)}), true, '/s')")


# --- Settings: MediaGrab update instructions per install type -----------------


@pytest.fixture(scope="module")
def mediagrab_update_html(escape_html):
    return (
        escape_html
        + "\nconst t = () => new Proxy({}, { get: (_, key) => key });\n"
        + _extract(r"function mediagrabUpdateHtml\(info\) \{.*?\n\}")
    )


def test_docker_gets_compose_pull(mediagrab_update_html):
    html = _run_js(mediagrab_update_html, "mediagrabUpdateHtml({install_type: 'docker'})")
    assert "docker compose pull" in html and "docker compose up -d" in html
    assert "git pull\"" not in html and "MediaGrabSetup" not in html


def test_the_installer_gets_repair_update_and_a_download_link(mediagrab_update_html):
    html = _run_js(mediagrab_update_html, "mediagrabUpdateHtml({install_type: 'installer'})")
    assert "mgUpdateInstaller" in html
    assert "releases/latest" in html
    assert "docker compose" not in html and "pip install" not in html


def test_a_source_install_gets_git_pull_and_pip(mediagrab_update_html):
    html = _run_js(mediagrab_update_html, "mediagrabUpdateHtml({install_type: 'source'})")
    assert 'data-command="git pull"' in html
    assert 'data-command="pip install -r requirements.txt"' in html
    assert "docker compose" not in html


# --- home page: a degraded probe result ---------------------------------------


@pytest.fixture(scope="module")
def degraded_helpers():
    return (
        "const t = () => new Proxy({}, { get: (_, key) => key });\n"
        + _extract(r"function audioChoiceAvailable\(info, choice\) \{.*?\n\}")
        + "\n"
        + _extract(r"function bestAudioChoice\(info\) \{.*?\n\}")
        + "\n"
        + _extract(r"function probeNoticesHtml\(info\) \{.*?\n\}")
    )


def test_without_an_audio_only_stream_only_mp3_is_offered(degraded_helpers):
    info = "{audio_only: false}"
    assert _run_js(degraded_helpers, f"['opus','m4a','mp3'].map((c) => audioChoiceAvailable({info}, c))") == [
        False,
        False,
        True,
    ]
    # NOTE: "Best Audio" must not pick a choice that's guaranteed to fail.
    assert _run_js(degraded_helpers, f"bestAudioChoice({info})") == "mp3"


@pytest.mark.parametrize("info", ["{audio_only: true}", "{}"])
def test_normally_every_audio_choice_is_offered(degraded_helpers, info):
    # NOTE: "{}" - a response from an older server without the field.
    assert _run_js(degraded_helpers, f"['opus','m4a','mp3'].every((c) => audioChoiceAvailable({info}, c))") is True
    assert _run_js(degraded_helpers, f"bestAudioChoice({info})") == "opus"


def test_the_age_verification_notice_is_shown(degraded_helpers):
    assert "noticeAgeVerification" in _run_js(degraded_helpers, "probeNoticesHtml({notices: ['account_age_verification']})")
    assert _run_js(degraded_helpers, "probeNoticesHtml({notices: []})") == ""
    assert _run_js(degraded_helpers, "probeNoticesHtml({})") == ""


def test_requested_format_not_available_gets_a_friendly_message(error_hints):
    raw = "ERROR: [youtube] qpgTC9MDx1o: Requested format is not available. Use --list-formats for a list of available formats"
    assert _run_js(error_hints, f"friendlyErrorEntry({json.dumps(raw)}).key") == "errFormatUnavailable"
