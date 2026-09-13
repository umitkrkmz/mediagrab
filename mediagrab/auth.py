"""Password hashing and in-memory sessions for the optional LAN login gate.

NOTE: stdlib-only on purpose (hashlib/hmac/secrets), matching the project's
"think twice before adding a dependency" rule - a single shared password for
a single-household app doesn't need a package for this.

Sessions live only in memory, exactly like the in-process `jobs` dict for
downloads - a server restart means everyone logs in again, which is an
acceptable trade-off for a personal, local tool and avoids ever persisting a
session token to disk.
"""

import hashlib
import hmac
import re
import secrets
import threading
import time
from typing import Optional

# NOTE: OWASP's 2023 minimum for PBKDF2-HMAC-SHA256. This runs once per login
# attempt, not per request (the session cookie is checked with a plain dict
# lookup), so the cost is a non-issue for the one-user-at-a-time case this
# is built for.
_PBKDF2_ITERATIONS = 260_000

SESSION_COOKIE_NAME = "mediagrab_session"
_SESSION_TTL_SECONDS = 30 * 24 * 3600  # 30 days - a "remember me" by default, there's no separate login/no-login mode

_sessions_lock = threading.Lock()
# NOTE: keyed by the real session TOKEN (the secret in the cookie), but that
# token is never handed back out anywhere - the "id" field below is a
# separate, non-secret handle the Settings UI can safely display and use to
# ask for a specific session to be revoked, without exposing (or needing)
# the credential itself.
_sessions: dict[str, dict] = {}


def hash_password(password: str) -> tuple[str, str]:
    """Returns (salt_hex, hash_hex) for storing in settings.json."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ITERATIONS)
    return salt, digest.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    """Constant-time check against a stored (salt, hash) pair."""
    if not salt_hex or not hash_hex or not password:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), _PBKDF2_ITERATIONS)
    return hmac.compare_digest(digest.hex(), hash_hex)


def create_session(user_agent: str = "") -> str:
    token = secrets.token_urlsafe(32)
    now = time.time()
    with _sessions_lock:
        _sessions[token] = {
            "id": secrets.token_hex(4),
            "expiry": now + _SESSION_TTL_SECONDS,
            "created_at": now,
            "device": describe_user_agent(user_agent),
        }
    return token


def is_valid_session(token: Optional[str]) -> bool:
    if not token:
        return False
    with _sessions_lock:
        info = _sessions.get(token)
        if info is None:
            return False
        if info["expiry"] < time.time():
            del _sessions[token]
            return False
        return True


def destroy_session(token: Optional[str]) -> None:
    if not token:
        return
    with _sessions_lock:
        _sessions.pop(token, None)


def clear_all_sessions() -> None:
    # NOTE: called whenever the password changes or remote access is turned
    # off - anyone already logged in (a browser that might not be the
    # account holder any more) is signed out immediately rather than staying
    # trusted until their 30-day cookie happens to expire.
    with _sessions_lock:
        _sessions.clear()


def list_sessions(current_token: Optional[str] = None) -> list[dict]:
    """Metadata for every session that's still valid, oldest first.

    Never includes the real token - `id` is the only handle callers get, and
    it isn't a credential (see the module-level note on `_sessions`).
    """
    with _sessions_lock:
        now = time.time()
        current_id = _sessions.get(current_token, {}).get("id") if current_token else None
        live = [info for info in _sessions.values() if info["expiry"] >= now]
    live.sort(key=lambda info: info["created_at"])
    return [
        {
            "id": info["id"],
            "created_at": info["created_at"],
            "device": info["device"],
            "is_current": info["id"] == current_id,
        }
        for info in live
    ]


def destroy_session_by_id(session_id: str) -> None:
    """Revoke one session by its display id - how the Settings UI lets you
    sign out a DIFFERENT device without ever having had access to its cookie.
    """
    with _sessions_lock:
        for token, info in list(_sessions.items()):
            if info["id"] == session_id:
                del _sessions[token]
                return


# NOTE: best-effort and deliberately simple - a short "Chrome · Windows"
# label is plenty for "which of my own devices is this", the goal isn't
# accurate analytics or fingerprinting. Falls back to a trimmed raw string
# for anything it doesn't recognise rather than guessing wrong.
_OS_PATTERNS = (
    (re.compile(r"windows", re.I), "Windows"),
    (re.compile(r"iphone|ipad|ipod", re.I), "iOS"),
    (re.compile(r"android", re.I), "Android"),
    (re.compile(r"mac ?os", re.I), "macOS"),
    (re.compile(r"linux", re.I), "Linux"),
)
_BROWSER_PATTERNS = (
    (re.compile(r"edg/", re.I), "Edge"),
    (re.compile(r"opr/|opera", re.I), "Opera"),
    (re.compile(r"chrome/", re.I), "Chrome"),
    (re.compile(r"firefox/", re.I), "Firefox"),
    (re.compile(r"safari/", re.I), "Safari"),
)


def describe_user_agent(user_agent: str) -> str:
    if not user_agent:
        return "?"
    os_name = next((name for pattern, name in _OS_PATTERNS if pattern.search(user_agent)), None)
    browser_name = next((name for pattern, name in _BROWSER_PATTERNS if pattern.search(user_agent)), None)
    if os_name and browser_name:
        return f"{browser_name} · {os_name}"
    return os_name or browser_name or user_agent[:40]
