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
