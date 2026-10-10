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


# --- saveFileToFolder ("Save to folder", host's own browser in Docker) ------
# NOTE: the bug this guards: cancelling Chrome's Save As dialog still let the
# server delete the file (relay mode), because the browser had already
# fetched it in the background. The server may only hear "/saved" once the
# bytes are really written to the folder the user picked.


def _run_js_async(snippet: str, expression: str):
    script = (
        f"{snippet}\nPromise.resolve({expression})"
        ".then((v) => process.stdout.write(JSON.stringify(v)))"
        ".catch((e) => process.stdout.write(JSON.stringify({ thrown: String(e && e.message || e) })));"
    )
    result = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, encoding="utf-8", timeout=30
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


SAVE_HARNESS = r"""
const calls = [];
const written = [];
function picker(behaviour) {
  return async (opts) => {
    calls.push(["pick", opts.suggestedName || null]);
    if (behaviour === "cancel") { const e = new Error("aborted"); e.name = "AbortError"; throw e; }
    return { createWritable: async () => ({ write: async (b) => written.push(b), close: async () => written.push("<closed>") }) };
  };
}
function fakeFetch({ deleted = false, failMidway = false } = {}) {
  return async (url, init) => {
    calls.push([init && init.method || "GET", url]);
    if (url.endsWith("/saved")) return { ok: true, json: async () => ({ deleted }) };
    return { ok: true, body: { pipeTo: async (w) => {
      await w.write("bytes");
      if (failMidway) throw new Error("connection lost");
      await w.close();
    } } };
  };
}
"""


@pytest.fixture(scope="module")
def save_to_folder():
    return _extract(r"async function saveFileToFolder\(.*?\n\}") + SAVE_HARNESS


def test_cancelling_the_picker_never_downloads_or_confirms(save_to_folder):
    result = _run_js_async(
        save_to_folder,
        "saveFileToFolder(picker('cancel'), fakeFetch(), '/api/history/file/V.mp4', 'V.mp4').then((r) => [r, calls])",
    )
    assert result == ["cancelled", [["pick", "V.mp4"]]]


def test_a_completed_save_confirms_to_the_server(save_to_folder):
    result = _run_js_async(
        save_to_folder,
        "saveFileToFolder(picker('ok'), fakeFetch(), '/api/history/file/V.mp4', 'V.mp4').then((r) => [r, calls, written])",
    )
    outcome, calls, written = result
    assert outcome == "saved"
    assert calls == [
        ["pick", "V.mp4"],
        ["GET", "/api/history/file/V.mp4/download"],
        ["POST", "/api/history/file/V.mp4/saved"],
    ]
    assert written == ["bytes", "<closed>"]


def test_the_outcome_says_when_the_server_removed_its_copy(save_to_folder):
    result = _run_js_async(
        save_to_folder,
        "saveFileToFolder(picker('ok'), fakeFetch({ deleted: true }), '/api/file/j1', 'V.mp4')",
    )
    assert result == "removed"


def test_an_interrupted_write_never_confirms(save_to_folder):
    result = _run_js_async(
        save_to_folder,
        "saveFileToFolder(picker('ok'), fakeFetch({ failMidway: true }), '/api/file/j1', 'V.mp4')"
        ".catch((e) => ({ thrown: e.message, calls }))",
    )
    assert result["thrown"] == "connection lost"
    assert not any(method == "POST" for method, _url in result["calls"])


@pytest.mark.parametrize(
    "is_local, same_machine, has_picker, expected",
    [
        (False, True, True, True),  # host's own browser in Docker, Chromium
        (False, True, False, False),  # same, but Firefox: plain download (never auto-deleted)
        (False, False, True, False),  # a LAN device
        (True, True, True, False),  # native install: "show in folder" instead
    ],
)
def test_save_to_folder_is_offered_only_on_the_docker_host_with_a_picker(is_local, same_machine, has_picker, expected):
    snippet = (
        f"let isLocalClient = {json.dumps(is_local)}; let isSameMachine = {json.dumps(same_machine)};\n"
        f"const window = {{ showSaveFilePicker: {'() => {}' if has_picker else 'undefined'} }};\n"
        + _extract(r"function canSaveToFolder\(\) \{.*?\n\}")
    )
    assert _run_js(snippet, "canSaveToFolder()") is expected


# --- I18N: tr and en must offer the same keys ----------------------------------


def test_app_js_tr_and_en_strings_have_the_same_keys():
    # NOTE: the same rule test_i18n.py enforces for the server-side dicts -
    # a key present in only one language renders as "undefined" in the other.
    # The whole dict is too long for a Windows command line (`node -e`), so
    # the script goes in on stdin instead.
    script = (
        _extract(r"const I18N = \{.*?\n\};")
        + "\nconst walk = (o, p = '') => Object.entries(o).flatMap(([k, v]) =>"
        " v && typeof v === 'object' ? walk(v, p + k + '.') : [p + k]);"
        "\nprocess.stdout.write(JSON.stringify({ tr: walk(I18N.tr), en: walk(I18N.en) }));"
    )
    result = subprocess.run(["node"], input=script, capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, result.stderr
    keys = json.loads(result.stdout)
    assert len(keys["tr"]) > 100
    assert set(keys["tr"]) ^ set(keys["en"]) == set()


# --- media player ------------------------------------------------------------


@pytest.fixture(scope="module")
def player_time():
    return _extract(r"function formatPlayerTime\(seconds\) \{.*?\n\}")


@pytest.mark.parametrize(
    "seconds, expected",
    [(0, "0:00"), (5.9, "0:05"), (65, "1:05"), (3725, "1:02:05"), ("NaN", "0:00"), ("Infinity", "0:00"), (-3, "0:00")],
)
def test_player_time_format(player_time, seconds, expected):
    assert _run_js(player_time, f"formatPlayerTime({seconds})") == expected


@pytest.fixture(scope="module")
def player_keys():
    return _extract(r"function playerKeyAction\(key\) \{.*?\n\}")


@pytest.mark.parametrize(
    "key, expected",
    [
        (" ", {"type": "toggle"}),
        ("k", {"type": "toggle"}),
        ("K", {"type": "toggle"}),
        ("ArrowLeft", {"type": "seekBy", "value": -5}),
        ("ArrowRight", {"type": "seekBy", "value": 5}),
        ("j", {"type": "seekBy", "value": -10}),
        ("l", {"type": "seekBy", "value": 10}),
        ("ArrowUp", {"type": "volumeBy", "value": 0.1}),
        ("ArrowDown", {"type": "volumeBy", "value": -0.1}),
        ("m", {"type": "mute"}),
        ("F", {"type": "fullscreen"}),
        ("Home", {"type": "seekTo", "fraction": 0}),
        ("End", {"type": "seekTo", "fraction": 1}),
        ("3", {"type": "seekTo", "fraction": 0.3}),
    ],
)
def test_player_keyboard_shortcuts(player_keys, key, expected):
    assert _run_js(player_keys, f"playerKeyAction({json.dumps(key)})") == expected


@pytest.mark.parametrize("key", ["Tab", "Enter", "Escape", "a", "F5", "Shift"])
def test_other_keys_are_left_to_the_browser(player_keys, key):
    assert _run_js(player_keys, f"playerKeyAction({json.dumps(key)})") is None


def test_the_player_never_shows_the_browsers_own_controls():
    # NOTE: the browser's built-in controls carry a "Download" menu entry -
    # the reason MediaGrab draws its own. A `controls` attribute sneaking
    # back onto the media element would bring both sets back at once.
    source = _extract(r"function createMediaPlayer\(container, src, kind\) \{.*?\n\}")
    media_tag = re.search(r"<\$\{kind\} class=\"mgp-media\"[^>]*>", source)
    assert media_tag, "the player's media element template moved - update this test"
    assert "controls" not in media_tag.group(0)
    assert '"contextmenu"' in source, "right-click 'Save video as' must stay suppressed"


# --- History -> Statistics ---------------------------------------------------


@pytest.fixture(scope="module")
def format_bytes():
    return _extract(r"function formatBytes\(bytes, language\) \{.*?\n\}")


@pytest.mark.parametrize(
    "size, language, expected",
    [
        (0, "tr", "0 B"),
        (512, "tr", "512 B"),
        (1536, "tr", "2 KB"),
        (5 * 1024**2, "tr", "5 MB"),
        (int(1.5 * 1024**3), "tr", "1,5 GB"),
        (int(1.5 * 1024**3), "en", "1.5 GB"),
        (int(155.7 * 1024**3), "tr", "156 GB"),
        (2 * 1024**4, "en", "2 TB"),
    ],
)
def test_format_bytes(format_bytes, size, language, expected):
    assert _run_js(format_bytes, f"formatBytes({size}, {json.dumps(language)})") == expected


@pytest.fixture(scope="module")
def stats_shares():
    return (
        _extract(r"const STATS_FORMAT_ORDER = \{.*?\n\};")
        + "\n"
        + _extract(r"function statsShares\(rows, kind\) \{.*?\n\}")
    )


def test_a_format_keeps_its_colour_slot_whatever_its_rank(stats_shares):
    # NOTE: colour follows the entity - 1080p is slot 3 whether it's the most
    # or the least downloaded resolution, so a new download never repaints it.
    first = _run_js(
        stats_shares,
        "statsShares([{name:'1080p',count:9,bytes:0},{name:'720p',count:1,bytes:0}], 'video').map(s => [s.name, s.slot])",
    )
    second = _run_js(
        stats_shares,
        "statsShares([{name:'720p',count:9,bytes:0},{name:'1080p',count:1,bytes:0}], 'video').map(s => [s.name, s.slot])",
    )
    assert first == second == [["1080p", 3], ["720p", 4]]


def test_unknown_formats_fold_into_one_neutral_segment_at_the_end(stats_shares):
    shares = _run_js(
        stats_shares,
        "statsShares([{name:'4320p',count:1,bytes:5},{name:'',count:1,bytes:5},{name:'480p',count:2,bytes:0}], 'video')",
    )
    assert [(s["name"], s["slot"], s["count"]) for s in shares] == [("480p", 5, 2), ("", 0, 2)]
    assert [round(s["percent"]) for s in shares] == [50, 50]


def test_no_downloads_means_no_segments(stats_shares):
    assert _run_js(stats_shares, "statsShares([], 'audio')") == []


@pytest.fixture(scope="module")
def bucket_label():
    return _extract(r"function statsBucketLabel\(startIso, period, language\) \{.*?\n\}")


def test_bucket_labels_follow_the_page_language(bucket_label):
    assert _run_js(bucket_label, "statsBucketLabel('2026-10-05', 'day', 'tr')") == "5 Eki"
    assert _run_js(bucket_label, "statsBucketLabel('2026-10-05', 'day', 'en')") == "Oct 5"
    assert _run_js(bucket_label, "statsBucketLabel('2026-01-01', 'month', 'tr')") == "Oca 26"
