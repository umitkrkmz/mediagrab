"""Tests for the translation dictionaries.

NOTE: a missing key renders as an empty string in Jinja rather than raising,
so a typo or a half-finished translation silently ships a blank label. These
checks make that a test failure instead.
"""

import re
from pathlib import Path

from mediagrab.i18n import UI, ui_text

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "mediagrab" / "templates"


def test_both_languages_define_exactly_the_same_keys():
    missing_in_en = set(UI["tr"]) - set(UI["en"])
    missing_in_tr = set(UI["en"]) - set(UI["tr"])
    assert not missing_in_en, f"English is missing: {sorted(missing_in_en)}"
    assert not missing_in_tr, f"Turkish is missing: {sorted(missing_in_tr)}"


def test_no_translation_is_left_empty():
    for lang, table in UI.items():
        for key, value in table.items():
            assert value.strip(), f"{lang}.{key} is empty"


def test_turkish_and_english_actually_differ():
    # NOTE: catches a copy-paste where an English string was left in the
    # Turkish table (or vice versa). A handful legitimately match - proper
    # nouns and identical technical terms - so this only asserts that the two
    # tables aren't wholesale duplicates.
    identical = [k for k in UI["tr"] if UI["tr"][k] == UI["en"][k]]
    assert len(identical) < len(UI["tr"]) / 2


def test_unknown_language_falls_back_to_turkish():
    assert ui_text("klingon") is UI["tr"]
    assert ui_text("en") is UI["en"]


def test_every_ui_key_used_in_a_template_exists():
    # NOTE: the real failure mode - a template referencing {{ ui.foo }} that
    # nobody ever added to i18n.py renders as blank, which is exactly how the
    # theme section first shipped with no visible labels.
    used = set()
    for template in TEMPLATES_DIR.glob("*.html"):
        used.update(re.findall(r"\bui\.([a-z0-9_]+)", template.read_text(encoding="utf-8")))
    assert used, "no ui.* references found - did the templates move?"
    unknown = used - set(UI["tr"])
    assert not unknown, f"templates use undefined keys: {sorted(unknown)}"


def test_no_key_collides_with_a_real_dict_method():
    # NOTE: regression test, reproduced live. `ui` is a plain dict, and
    # Jinja's `{{ ui.copy }}` tries getattr(ui, "copy") BEFORE ui["copy"] -
    # since dict has a real .copy() method, a key named "copy" silently
    # rendered as "<built-in method copy of dict object at 0x...>" instead of
    # the translated string, with no error anywhere. Same trap for any other
    # key matching a dict attribute (items, keys, values, get, update, pop,
    # clear, ...).
    reserved = set(dir({}))
    colliding = set(UI["tr"]) & reserved
    assert not colliding, f"these i18n keys are shadowed by dict methods and must be renamed: {sorted(colliding)}"


# --- the Windows installer's own texts (packaging/*.iss) ----------------------

PACKAGING_DIR = Path(__file__).resolve().parent.parent / "packaging"


def _installer_messages():
    # NOTE: Inno Setup's [CustomMessages], "english.Name=..." / "turkish.Name=...".
    # A message defined for one language only compiles fine and then stops
    # the wizard with "Unknown custom message name" in the other.
    text = (PACKAGING_DIR / "mediagrab.iss").read_text(encoding="utf-8-sig")
    section = text.split("\n[CustomMessages]", 1)[1].split("\n[Code]", 1)[0]
    found = {}
    for lang, name, value in re.findall(r"^(english|turkish)\.(\w+)=(.*)$", section, re.M):
        found.setdefault(lang, {})[name] = value
    return found


def test_the_installer_has_every_message_in_both_languages():
    messages = _installer_messages()
    assert len(messages["english"]) > 50, "the [CustomMessages] section wasn't found"
    assert set(messages["english"]) == set(messages["turkish"])
    for lang, table in messages.items():
        for name, value in table.items():
            assert value.strip(), f"{lang}.{name} is empty"


def test_the_installer_uses_only_messages_it_defines():
    defined = set(_installer_messages()["english"])
    # NOTE: Inno's own built-in custom messages.
    defined |= {"LaunchProgram", "CreateDesktopIcon", "AdditionalIcons"}
    code = "".join(p.read_text(encoding="utf-8-sig") for p in sorted(PACKAGING_DIR.glob("*.iss")))
    used = set(re.findall(r"\{cm:(\w+)", code)) | set(re.findall(r"CustomMessage\('(\w+)'\)", code))
    # NOTE: the Docker page builds 'DockerStatus_' + DockerStatus() at run
    # time - every status that function can return needs its message.
    wizard = (PACKAGING_DIR / "docker_wizard.iss").read_text(encoding="utf-8-sig")
    status_fn = wizard.split("function DockerStatus", 1)[1].split("\nend;", 1)[0]
    statuses = re.findall(r"Result := '(\w+)'", status_fn)
    assert statuses, "DockerStatus() wasn't found"
    used |= {f"DockerStatus_{status}" for status in statuses}
    assert not used - defined, f"used but not defined: {sorted(used - defined)}"
