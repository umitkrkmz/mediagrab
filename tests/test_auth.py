"""Tests for mediagrab/auth.py and the optional remote-access login gate.

NOTE: unlike the rest of the suite (see test_app.py's own note - "the HTTP
layer isn't exercised here"), the middleware wiring genuinely needs a real
HTTP round trip to prove it's connected: a login/session mechanism that's
fully unit-tested but never actually wired into the request pipeline is
exactly the kind of bug this project has been burned by before (see
test_setup.py's "Refresh" button comment). fastapi.testclient.TestClient
gives us that without a real server process.
"""

import json

import pytest
from fastapi.testclient import TestClient

from mediagrab import auth, store
import mediagrab.app as app_module

# --- password hashing --------------------------------------------------------


def test_correct_password_verifies():
    salt, digest = auth.hash_password("correct horse battery staple")
    assert auth.verify_password("correct horse battery staple", salt, digest)


def test_wrong_password_is_rejected():
    salt, digest = auth.hash_password("correct horse battery staple")
    assert not auth.verify_password("wrong guess", salt, digest)


def test_verify_against_unset_password_is_always_false():
    # NOTE: the "no password configured yet" state (empty salt/hash) must
    # never accidentally verify - e.g. an empty password against an empty hash.
    assert not auth.verify_password("", "", "")
    assert not auth.verify_password("anything", "", "")


def test_two_hashes_of_the_same_password_differ():
    # NOTE: proves a random salt is actually being used per call, not a
    # fixed one - identical hashes for the same password would mean the
    # salt isn't doing its job (rainbow-table resistance).
    _salt1, digest1 = auth.hash_password("same password")
    _salt2, digest2 = auth.hash_password("same password")
    assert digest1 != digest2


# --- sessions -----------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_sessions():
    # NOTE: _sessions is a module-level dict shared across every test in the
    # process - without this, a session created by one test could make a
    # later test's "no valid session" assumption false.
    auth.clear_all_sessions()
    yield
    auth.clear_all_sessions()


def test_a_fresh_session_is_valid():
    token = auth.create_session()
    assert auth.is_valid_session(token)


def test_an_unknown_token_is_invalid():
    assert not auth.is_valid_session("this-token-was-never-issued")
    assert not auth.is_valid_session(None)
    assert not auth.is_valid_session("")


def test_destroying_a_session_invalidates_it():
    token = auth.create_session()
    auth.destroy_session(token)
    assert not auth.is_valid_session(token)


def test_destroying_an_unknown_token_is_not_an_error():
    auth.destroy_session("never-issued")
    auth.destroy_session(None)


def test_an_expired_session_is_invalid_and_gets_swept():
    token = auth.create_session()
    auth._sessions[token]["expiry"] = 0.0  # NOTE: reach in directly to simulate the past
    assert not auth.is_valid_session(token)
    assert token not in auth._sessions, "an expired session should be pruned on check, not just rejected"


def test_clear_all_sessions_invalidates_everything():
    tokens = [auth.create_session() for _ in range(3)]
    auth.clear_all_sessions()
    assert not any(auth.is_valid_session(t) for t in tokens)


# --- store.remote_access_active ----------------------------------------------


def test_inactive_by_default():
    assert not store.remote_access_active(store.DEFAULT_SETTINGS)


def test_enabled_without_a_password_is_not_active():
    settings = dict(store.DEFAULT_SETTINGS, remote_access_enabled=True)
    assert not store.remote_access_active(settings)


def test_a_password_without_enabling_is_not_active():
    settings = dict(
        store.DEFAULT_SETTINGS, remote_access_password_salt="s", remote_access_password_hash="h"
    )
    assert not store.remote_access_active(settings)


def test_both_enabled_and_a_password_is_active():
    settings = dict(
        store.DEFAULT_SETTINGS,
        remote_access_enabled=True,
        remote_access_password_salt="s",
        remote_access_password_hash="h",
    )
    assert store.remote_access_active(settings)


# --- the login gate, end to end ------------------------------------------------


@pytest.fixture
def client(tmp_path, monkeypatch):
    # NOTE: isolates settings.json AND channels.json - without the latter,
    # the lifespan's background channel check would run against whatever
    # channels.json happens to sit at the real project root (gitignored, but
    # very much real on a dev machine).
    monkeypatch.setattr(store, "SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setattr(store, "STORE_PATH", str(tmp_path / "channels.json"))
    # NOTE: enabling remote access spawns a thread that (after 1s) calls
    # os.execv and replaces THIS PROCESS - i.e. the test runner itself. Never
    # let the real one run under pytest.
    monkeypatch.setattr(app_module, "_delayed_restart", lambda: None)
    with TestClient(app_module.app) as test_client:
        yield test_client


def _enable_remote_access(client, password="a-fine-password"):
    res = client.post("/api/remote-access/password", json={"password": password})
    assert res.status_code == 200, res.text
    res = client.post("/api/remote-access", json={"enabled": True})
    assert res.status_code == 200, res.text
    return password


def test_the_app_is_open_by_default(client):
    # NOTE: the whole feature is opt-in - a fresh install must behave exactly
    # like before this existed.
    assert client.get("/", follow_redirects=False).status_code == 200
    assert client.get("/api/history").status_code == 200


def test_enabling_without_a_password_set_is_refused(client):
    res = client.post("/api/remote-access", json={"enabled": True})
    assert res.status_code == 400
    assert not store.remote_access_active(store.get_settings())


def test_password_must_be_at_least_8_characters(client):
    res = client.post("/api/remote-access/password", json={"password": "short"})
    assert res.status_code == 400
    assert store.get_settings()["remote_access_password_hash"] == ""


def test_the_first_password_needs_no_current_password_to_confirm(client):
    # NOTE: nothing exists yet to prove you know - requiring current_password
    # here would make it impossible to ever set a password in the first place.
    res = client.post("/api/remote-access/password", json={"password": "brand-new-password"})
    assert res.status_code == 200
    assert res.json()["has_password"] is True


def test_changing_password_requires_the_correct_current_one(client):
    old_password = _enable_remote_access(client, password="original-password")
    client.post("/api/login", json={"password": old_password})

    res = client.post(
        "/api/remote-access/password",
        json={"password": "attacker-chosen-password", "current_password": "totally-wrong-guess"},
    )
    assert res.status_code == 401

    # the password was NOT changed - the original still works, the attempted new one does not
    assert client.post("/api/login", json={"password": old_password}).status_code == 200
    assert client.post("/api/login", json={"password": "attacker-chosen-password"}).status_code == 401


def test_once_active_pages_redirect_and_api_calls_401(client):
    _enable_remote_access(client)
    page_res = client.get("/", follow_redirects=False)
    assert page_res.status_code in (302, 307)
    assert "/login" in page_res.headers["location"]
    assert client.get("/api/history").status_code == 401


def test_login_and_static_and_locale_stay_reachable_while_gated(client):
    _enable_remote_access(client)
    assert client.get("/login", follow_redirects=False).status_code == 200
    assert client.get("/api/locale").status_code == 200
    assert client.get("/static/style.css").status_code == 200


def test_wrong_password_does_not_grant_a_session(client):
    _enable_remote_access(client, password="the-real-password")
    res = client.post("/api/login", json={"password": "guess"})
    assert res.status_code == 401
    assert client.get("/api/history").status_code == 401


def test_correct_password_grants_access(client):
    password = _enable_remote_access(client)
    res = client.post("/api/login", json={"password": password})
    assert res.status_code == 200
    assert auth.SESSION_COOKIE_NAME in res.cookies
    assert client.get("/", follow_redirects=False).status_code == 200
    assert client.get("/api/history").status_code == 200


def test_logout_revokes_access_immediately(client):
    password = _enable_remote_access(client)
    client.post("/api/login", json={"password": password})
    assert client.get("/api/history").status_code == 200

    client.post("/api/logout")
    assert client.get("/api/history").status_code == 401


def test_changing_the_password_signs_out_the_session_that_changed_it(client):
    # NOTE: a real security property, not just plumbing - if changing your
    # password didn't also invalidate the session you used to change it,
    # "I think someone else is in my account, let me change the password"
    # wouldn't actually remove their access until they happened to log out.
    old_password = _enable_remote_access(client)
    client.post("/api/login", json={"password": old_password})
    assert client.get("/api/history").status_code == 200

    res = client.post(
        "/api/remote-access/password",
        json={"password": "a-different-password", "current_password": old_password},
    )
    assert res.status_code == 200
    assert client.get("/api/history").status_code == 401

    # the new password logs in fine; the old one no longer works at all
    assert client.post("/api/login", json={"password": old_password}).status_code == 401
    assert client.post("/api/login", json={"password": "a-different-password"}).status_code == 200


def test_disabling_remote_access_makes_the_app_public_again(client):
    password = _enable_remote_access(client)
    client.post("/api/login", json={"password": password})

    res = client.post("/api/remote-access", json={"enabled": False})
    assert res.status_code == 200

    # NOTE: a fresh client with no cookie at all - not just "my session still
    # works", but "nobody needs a session any more".
    fresh = TestClient(app_module.app)
    assert fresh.get("/", follow_redirects=False).status_code == 200
    assert fresh.get("/api/history").status_code == 200


def test_remote_access_status_never_exposes_the_password_hash(client):
    _enable_remote_access(client, password="whatever-secret")
    res = client.post("/api/login", json={"password": "whatever-secret"})
    body = client.get("/api/remote-access").json()
    assert set(body.keys()) == {"enabled", "has_password", "lan_url", "mdns_url", "download_mode"}
    assert "whatever-secret" not in str(res.cookies)
    assert "whatever-secret" not in json.dumps(body)


# --- the LAN address shown in Settings ----------------------------------------


def test_lan_url_is_absent_while_inactive(client):
    # NOTE: showing an address before the server is actually reachable there
    # would be a link that doesn't work yet.
    assert client.get("/api/remote-access").json()["lan_url"] is None


def test_lan_url_appears_once_active(client):
    password = _enable_remote_access(client)
    client.post("/api/login", json={"password": password})
    lan_url = client.get("/api/remote-access").json()["lan_url"]
    assert lan_url is None or lan_url.startswith("http://"), lan_url
    # NOTE: lan_ip() can legitimately return None in a network-less sandbox -
    # this only asserts the SHAPE is right when an address is available.


# --- connected devices ---------------------------------------------------------


@pytest.mark.parametrize(
    "user_agent,expected",
    [
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36",
            "Chrome · Windows",
        ),
        (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
            "Safari · iOS",
        ),
        ("Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0", "Firefox · Linux"),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
            "Edge · Windows",  # NOTE: Edge's UA also contains "Chrome/" and "Safari/" - must not misclassify
        ),
        ("", "?"),
        ("SomeWeirdBotThatNobodyRecognises/1.0", "SomeWeirdBotThatNobodyRecognises/1.0"),
    ],
)
def test_describe_user_agent(user_agent, expected):
    assert auth.describe_user_agent(user_agent) == expected


def test_a_logged_in_session_shows_up_in_the_devices_list(client):
    password = _enable_remote_access(client)
    client.post(
        "/api/login",
        json={"password": password},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0 Safari/537.36"},
    )
    sessions = client.get("/api/remote-access/sessions").json()["sessions"]
    assert len(sessions) == 1
    assert sessions[0]["is_current"] is True
    assert sessions[0]["device"] == "Chrome · Windows"
    assert "id" in sessions[0] and sessions[0]["id"]


def test_two_devices_each_see_the_other_as_not_current(client):
    password = _enable_remote_access(client)
    client.post("/api/login", json={"password": password}, headers={"User-Agent": "device-A"})

    other_device = TestClient(app_module.app)  # NOTE: its own, separate cookie jar - a second browser
    other_device.post("/api/login", json={"password": password}, headers={"User-Agent": "device-B"})

    seen_by_first = {s["device"]: s["is_current"] for s in client.get("/api/remote-access/sessions").json()["sessions"]}
    seen_by_second = {
        s["device"]: s["is_current"] for s in other_device.get("/api/remote-access/sessions").json()["sessions"]
    }
    assert seen_by_first == {"device-A": True, "device-B": False}
    assert seen_by_second == {"device-A": False, "device-B": True}


def test_revoking_another_devices_session_signs_it_out_but_not_you(client):
    password = _enable_remote_access(client)
    client.post("/api/login", json={"password": password}, headers={"User-Agent": "this-device"})

    other_device = TestClient(app_module.app)
    other_device.post("/api/login", json={"password": password}, headers={"User-Agent": "other-device"})
    assert other_device.get("/api/history").status_code == 200

    sessions = client.get("/api/remote-access/sessions").json()["sessions"]
    other_id = next(s["id"] for s in sessions if s["device"] == "other-device")

    res = client.delete(f"/api/remote-access/sessions/{other_id}")
    assert res.status_code == 200

    assert other_device.get("/api/history").status_code == 401, "the revoked device must be signed out"
    assert client.get("/api/history").status_code == 200, "revoking someone else must not sign YOU out"


def test_revoking_an_unknown_session_id_is_not_an_error(client):
    password = _enable_remote_access(client)
    client.post("/api/login", json={"password": password})
    assert client.delete("/api/remote-access/sessions/does-not-exist").status_code == 200
