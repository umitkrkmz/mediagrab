"""Tests for GET /api/settings/export and POST /api/settings/import.

NOTE: the security-critical property here is that a backup file - something
people might share (moving to a new device, asking for help) - can NEVER
carry the remote-access password, either out (export) or in (import), even
if someone hand-edits one to include it. See app.py's own comment on
_SETTINGS_BACKUP_EXCLUDED_KEYS.
"""

import json

import pytest
from fastapi.testclient import TestClient

import mediagrab.app as app_module
from mediagrab import store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setattr(store, "STORE_PATH", str(tmp_path / "channels.json"))
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: None)
    with TestClient(app_module.app) as test_client:
        yield test_client


# --- export --------------------------------------------------------------------


def test_export_never_includes_the_password_hash_or_salt(client):
    client.post("/api/remote-access/password", json={"password": "a-fine-password"})
    body = client.get("/api/settings/export").json()
    assert "remote_access_password_hash" not in body["settings"]
    assert "remote_access_password_salt" not in body["settings"]
    # NOTE: belt and suspenders - also check the raw bytes, not just the
    # parsed keys, in case the hash value itself leaked into some other field.
    assert "a-fine-password" not in client.get("/api/settings/export").text


def test_export_sets_a_download_filename(client):
    res = client.get("/api/settings/export")
    assert "attachment" in res.headers["content-disposition"]
    assert "mediagrab-yedek.json" in res.headers["content-disposition"]


def test_export_includes_settings_channels_and_pending(client):
    store.save_settings(default_audio_lang="tr", download_speed_limit_mbps=5)
    store.add_channel(
        url="https://youtube.com/c/test",
        name="Test Channel",
        thumbnail=None,
        mode="notify",
        choice_kind="video",
        choice="best",
        last_video_id=None,
    )
    store.add_pending([{"channel_id": "x", "channel_name": "Test Channel", "id": "v1", "title": "V", "url": "u"}])

    body = client.get("/api/settings/export").json()
    assert body["settings"]["default_audio_lang"] == "tr"
    assert body["settings"]["download_speed_limit_mbps"] == 5
    assert len(body["channels"]) == 1
    assert body["channels"][0]["name"] == "Test Channel"
    assert len(body["pending"]) == 1


# --- import: the security property ----------------------------------------------


def test_import_never_accepts_a_password_hash_even_if_the_file_has_one(client):
    old_password = "the-real-password"
    client.post("/api/remote-access/password", json={"password": old_password})
    original_hash = store.get_settings()["remote_access_password_hash"]

    # NOTE: simulates a hand-edited (or maliciously crafted) backup file that
    # tries to smuggle in a different password hash - e.g. shared by someone
    # hoping the recipient imports it and unknowingly grants them access.
    malicious = {
        "mediagrab_export_version": 1,
        "settings": {
            "remote_access_password_hash": "attacker-controlled-hash",
            "remote_access_password_salt": "attacker-controlled-salt",
            "default_audio_lang": "en",
        },
        "channels": [],
        "pending": [],
    }
    res = client.post("/api/settings/import", json=malicious)
    assert res.status_code == 200

    settings = store.get_settings()
    assert settings["remote_access_password_hash"] == original_hash
    assert settings["remote_access_password_hash"] != "attacker-controlled-hash"
    # NOTE: the rest of the payload (a legitimate field) must still apply -
    # this isn't "reject the whole import", just "never touch credentials".
    assert settings["default_audio_lang"] == "en"


def test_the_first_password_cannot_be_set_via_import_either(client):
    # NOTE: even on a device with NO password yet, import must not be a way
    # to set one - only the dedicated password endpoint (with its own rules)
    # may ever write these fields.
    res = client.post(
        "/api/settings/import",
        json={
            "settings": {
                "remote_access_password_hash": "smuggled-hash",
                "remote_access_password_salt": "smuggled-salt",
            },
            "channels": [],
            "pending": [],
        },
    )
    assert res.status_code == 200
    settings = store.get_settings()
    assert settings["remote_access_password_hash"] == ""
    assert settings["remote_access_password_salt"] == ""


# --- import: restoring real data ------------------------------------------------


def test_import_restores_settings(client):
    res = client.post(
        "/api/settings/import",
        json={"settings": {"default_audio_lang": "de", "download_speed_limit_mbps": 10}, "channels": [], "pending": []},
    )
    assert res.status_code == 200
    settings = store.get_settings()
    assert settings["default_audio_lang"] == "de"
    assert settings["download_speed_limit_mbps"] == 10


def test_import_replaces_the_whole_channel_list_not_merges(client):
    store.add_channel(
        url="https://youtube.com/c/old",
        name="Old Channel",
        thumbnail=None,
        mode="notify",
        choice_kind="video",
        choice="best",
        last_video_id=None,
    )
    imported_channel = {
        "id": "imported-1",
        "url": "https://youtube.com/c/new",
        "name": "New Channel",
        "thumbnail": None,
        "mode": "auto",
        "choice_kind": "audio",
        "choice": "opus",
        "last_video_id": None,
        "added_at": "2026-01-01T00:00:00",
        "last_checked_at": None,
        "last_error": None,
    }
    res = client.post(
        "/api/settings/import", json={"settings": {}, "channels": [imported_channel], "pending": []}
    )
    assert res.status_code == 200
    channels = store.list_channels()
    assert len(channels) == 1
    assert channels[0]["name"] == "New Channel"


def test_import_round_trips_a_real_export(client):
    # NOTE: the realistic end-to-end path - export what's there, wipe it,
    # import it back, and confirm it's identical (minus the credentials,
    # which were never in the export to begin with).
    store.save_settings(default_audio_lang="tr", cookie_mode="file", cookie_file="/some/cookies.txt")
    store.add_channel(
        url="https://youtube.com/c/x",
        name="X",
        thumbnail=None,
        mode="notify",
        choice_kind="video",
        choice="best",
        last_video_id="abc",
    )
    exported = client.get("/api/settings/export").json()

    store.save_settings(default_audio_lang="", cookie_mode="off", cookie_file="")
    store.replace_channels([], [])

    res = client.post("/api/settings/import", json=exported)
    assert res.status_code == 200
    settings = store.get_settings()
    assert settings["default_audio_lang"] == "tr"
    assert settings["cookie_mode"] == "file"
    assert len(store.list_channels()) == 1


def test_a_malformed_channel_entry_is_rejected_with_422(client):
    # NOTE: Pydantic validation on `channels: list[ChannelItem]` - a corrupt
    # or hand-edited file with the wrong shape must not silently half-import.
    res = client.post(
        "/api/settings/import",
        json={"settings": {}, "channels": [{"id": "x"}], "pending": []},  # missing every other required field
    )
    assert res.status_code == 422


def test_unknown_settings_keys_are_ignored_not_injected(client):
    res = client.post(
        "/api/settings/import",
        json={"settings": {"something_dangerous": "value"}, "channels": [], "pending": []},
    )
    assert res.status_code == 200
    assert "something_dangerous" not in store.get_settings()
