"""
Session persistence and inactivity timeout using browser cookies.

Cookie value is a base64-encoded JSON payload signed with HMAC-SHA256.
Stores: email, role, display name, news_views counter, login timestamp,
        last_activity timestamp, and the HMAC signature.

The INACTIVITY_TIMEOUT is enforced both server-side (session_state) and
inside the cookie value so that the timeout survives a full page refresh.

Uses streamlit-cookies-controller (CookieController) instead of the older
extra_streamlit_components CookieManager.  The cm argument accepted by every
public function below should be a CookieController instance.
"""

import hmac
import hashlib
import json
import base64
import os
import time

import streamlit as st

COOKIE_NAME = "mml_session"
INACTIVITY_TIMEOUT = 600       # 10 minutes in seconds
_COOKIE_REFRESH_INTERVAL = 60  # refresh cookie's last_activity every 60 s

# How long the browser should keep the cookie between visits.
# The server-side inactivity check enforces the 10-minute idle limit;
# the cookie itself lasts 7 days so it survives machine restarts / sleeps.
COOKIE_MAX_AGE = 7 * 24 * 3600  # 7 days in seconds

# Override with the MYMAINTLOG_SECRET environment variable in production.
_SECRET = os.environ.get("MYMAINTLOG_SECRET", "mymaintlog-dev-key-change-in-prod")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sign(email: str, login_ts: float) -> str:
    msg = f"{email}:{int(login_ts)}"
    return hmac.new(_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()


def _encode(payload: dict) -> str:
    return base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).decode()


def _decode(value: str) -> dict:
    # Add padding so base64 decode doesn't fail on truncated strings
    return json.loads(base64.urlsafe_b64decode(value + "==").decode())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def make_session_cookie(email: str, role: str, name: str, news_views: int) -> str:
    """Create a signed cookie value for a new login session."""
    now = time.time()
    payload = {
        "e": email,
        "r": role,
        "n": name,
        "v": news_views,
        "ts": now,    # login timestamp — used in HMAC
        "la": now,    # last_activity
        "s": _sign(email, now),
    }
    return _encode(payload)


def _refresh_la(cookie_val: str) -> str:
    """Return a new cookie string with last_activity updated to now."""
    try:
        payload = _decode(cookie_val)
        payload["la"] = time.time()
        return _encode(payload)
    except Exception:
        return cookie_val


def _validate(value: str):
    """Decode and validate cookie. Returns payload dict or None."""
    try:
        payload = _decode(value)
        if not hmac.compare_digest(_sign(payload["e"], payload["ts"]), payload["s"]):
            return None
        if time.time() - payload.get("la", payload["ts"]) > INACTIVITY_TIMEOUT:
            return None  # timed out
        return payload
    except Exception:
        return None


def try_restore_session(cm) -> bool:
    """
    Attempt to restore an authenticated session from the browser cookie.
    cm must be a CookieController instance.
    Returns True if a valid, non-expired session was found and restored.
    """
    if st.session_state.get("authenticated"):
        return True

    # Prevent restoring session immediately after an explicit logout or timeout
    if st.session_state.get("_do_not_restore"):
        val = cm.get(COOKIE_NAME)
        if not val:
            # Cookie is gone — safe to clear the block flag
            st.session_state.pop("_do_not_restore", None)
        return False

    val = cm.get(COOKIE_NAME)
    if not val:
        return False

    payload = _validate(val)
    if payload is None:
        # Cookie is invalid or timed out — delete it
        try:
            cm.remove(COOKIE_NAME)
            st.session_state["_do_not_restore"] = True
        except Exception:
            pass
        return False

    # Restore session
    st.session_state.update({
        "authenticated": True,
        "user_email": payload["e"],
        "user_role": payload["r"],
        "user_name": payload["n"],
        "news_views": payload.get("v", 0),
        "last_activity": time.time(),
        "_cookie_refreshed_at": time.time(),
    })
    # Refresh the cookie's last_activity so the 10-min window slides forward
    try:
        cm.set(COOKIE_NAME, _refresh_la(val), max_age=COOKIE_MAX_AGE)
    except Exception:
        pass
    return True


def refresh_cookie_if_needed(cm):
    """
    Periodically write an updated last_activity into the browser cookie.
    Throttled to once per _COOKIE_REFRESH_INTERVAL to minimise extra reruns.
    """
    now = time.time()
    if now - st.session_state.get("_cookie_refreshed_at", 0) < _COOKIE_REFRESH_INTERVAL:
        return
    try:
        val = cm.get(COOKIE_NAME)
        if not val:
            return
        cm.set(COOKIE_NAME, _refresh_la(val), max_age=COOKIE_MAX_AGE)
        st.session_state["_cookie_refreshed_at"] = now
    except Exception:
        pass


def do_logout(cm):
    """
    Explicitly log out: delete cookie and clear all auth state.
    Sets _do_not_restore to prevent the cookie from being re-read on the
    next render before the browser deletion has propagated.
    """
    st.session_state["_do_not_restore"] = True
    try:
        cm.remove(COOKIE_NAME)
    except Exception:
        pass
    for k in ("authenticated", "user_email", "user_role", "user_name",
               "news_views", "last_activity", "_cookie_refreshed_at"):
        st.session_state.pop(k, None)
    st.session_state["authenticated"] = False
