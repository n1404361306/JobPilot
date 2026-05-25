#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.request


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
API_BASE = f"{BASE_URL}/api"

ADMIN_NAME = os.getenv("ADMIN_NAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "Admin@123456")

USER_NAME = f"user_{int(time.time())}"
USER_EMAIL = f"{USER_NAME}@example.com"
USER_PASS = "User@123456"
USER_NEW_PASS = "User@1234567"

PASS_COUNT = 0
FAIL_COUNT = 0


def say(tag: str, msg: str) -> None:
    print(f"\n[{tag}] {msg}")


def pass_case(name: str) -> None:
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"✅ {name}")


def fail_case(name: str, detail: str = "") -> None:
    global FAIL_COUNT
    FAIL_COUNT += 1
    if detail:
        print(f"❌ {name} ({detail})")
    else:
        print(f"❌ {name}")


def http_call(method: str, url: str, token: str = "", payload: dict = None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url=url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return resp.getcode(), body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return e.code, body
    except Exception as e:
        return 0, str(e)


def assert_2xx(code: int, title: str) -> None:
    if 200 <= code < 300:
        pass_case(title)
    else:
        fail_case(title, f"HTTP {code}")


def assert_eq(code: int, expected: int, title: str) -> None:
    if code == expected:
        pass_case(title)
    else:
        fail_case(title, f"HTTP {code}, expect {expected}")


def get_json_field(text: str, *path):
    try:
        obj = json.loads(text)
        for p in path:
            obj = obj[p]
        return obj
    except Exception:
        return ""


def main() -> int:
    global USER_PASS
    say("INFO", f"BASE_URL={BASE_URL}")

    # 0) health
    say("STEP 0", "Health check")
    code, body = http_call("GET", f"{BASE_URL}/health")
    assert_2xx(code, "GET /health")

    # 1) register
    say("STEP 1", "Register normal user")
    code, body = http_call(
        "POST",
        f"{API_BASE}/auth/register",
        payload={"username": USER_NAME, "email": USER_EMAIL, "password": USER_PASS},
    )
    assert_2xx(code, "POST /api/auth/register")

    # 2) login normal user
    say("STEP 2", "Login normal user")
    code, body = http_call(
        "POST",
        f"{API_BASE}/auth/login",
        payload={"username": USER_NAME, "password": USER_PASS},
    )
    assert_2xx(code, "POST /api/auth/login (normal)")
    user_access = get_json_field(body, "data", "access_token")
    user_refresh = get_json_field(body, "data", "refresh_token")
    if user_access and user_refresh:
        pass_case("Extract normal user tokens")
    else:
        fail_case("Extract normal user tokens")

    # 3) auth me
    say("STEP 3", "Get current user")
    code, body = http_call("GET", f"{API_BASE}/auth/me", token=user_access)
    assert_2xx(code, "GET /api/auth/me")

    # 4) refresh
    say("STEP 4", "Refresh token")
    code, body = http_call(
        "POST",
        f"{API_BASE}/auth/refresh",
        payload={"refresh_token": user_refresh},
    )
    assert_2xx(code, "POST /api/auth/refresh")
    refreshed_access = get_json_field(body, "data", "access_token")
    if refreshed_access:
        user_access = refreshed_access
        pass_case("Extract refreshed access token")
    else:
        fail_case("Extract refreshed access token")

    # 5) update password
    say("STEP 5", "Update password")
    code, body = http_call(
        "PUT",
        f"{API_BASE}/auth/password",
        token=user_access,
        payload={"old_password": USER_PASS, "new_password": USER_NEW_PASS},
    )
    assert_2xx(code, "PUT /api/auth/password")
    USER_PASS = USER_NEW_PASS

    # 6) user profile
    say("STEP 6", "Get/update user profile")
    code, body = http_call("GET", f"{API_BASE}/users/me", token=user_access)
    assert_2xx(code, "GET /api/users/me")
    code, body = http_call(
        "PUT",
        f"{API_BASE}/users/me",
        token=user_access,
        payload={"email": f"updated_{USER_EMAIL}"},
    )
    assert_2xx(code, "PUT /api/users/me")

    # 7) forbidden admin
    say("STEP 7", "Normal user forbidden for admin APIs")
    code, body = http_call("GET", f"{API_BASE}/admin/users", token=user_access)
    assert_eq(code, 400, "GET /api/admin/users forbidden for normal user")

    # 8) admin login and admin apis
    say("STEP 8", "Login admin and test admin APIs")
    code, body = http_call(
        "POST",
        f"{API_BASE}/auth/login",
        payload={"username": ADMIN_NAME, "password": ADMIN_PASS},
    )
    assert_2xx(code, "POST /api/auth/login (admin)")
    admin_access = get_json_field(body, "data", "access_token")
    if admin_access:
        pass_case("Extract admin token")
    else:
        fail_case("Extract admin token")

    code, body = http_call("GET", f"{API_BASE}/admin/users", token=admin_access)
    assert_2xx(code, "GET /api/admin/users (admin)")

    code, body = http_call("GET", f"{API_BASE}/admin/system-configs", token=admin_access)
    assert_2xx(code, "GET /api/admin/system-configs (admin)")

    code, body = http_call(
        "PUT",
        f"{API_BASE}/admin/system-configs/test_switch",
        token=admin_access,
        payload={"config_value": "true"},
    )
    assert_2xx(code, "PUT /api/admin/system-configs/{key} (admin)")

    code, body = http_call("GET", f"{API_BASE}/admin/ai-logs", token=admin_access)
    assert_2xx(code, "GET /api/admin/ai-logs (admin)")

    code, body = http_call("GET", f"{API_BASE}/admin/ocr-logs", token=admin_access)
    assert_2xx(code, "GET /api/admin/ocr-logs (admin)")

    code, body = http_call("GET", f"{API_BASE}/admin/system-logs", token=admin_access)
    assert_2xx(code, "GET /api/admin/system-logs (admin)")

    say("RESULT", f"PASS={PASS_COUNT} FAIL={FAIL_COUNT}")
    if FAIL_COUNT > 0:
        return 1
    print("All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
