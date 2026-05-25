#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/test_api_local.sh
#   BASE_URL="http://127.0.0.1:8000" bash scripts/test_api_local.sh

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
API_BASE="${BASE_URL}/api"

USER_NAME="user_$(date +%s)"
USER_EMAIL="${USER_NAME}@example.com"
USER_PASS="User@123456"
USER_NEW_PASS="User@1234567"

ADMIN_NAME="${ADMIN_NAME:-admin}"
ADMIN_PASS="${ADMIN_PASS:-Admin@123456}"

PASS_COUNT=0
FAIL_COUNT=0

say() { echo -e "\n[$1] $2"; }

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  echo "✅ $1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  echo "❌ $1"
}

http_call() {
  # Output format:
  # line1 -> body
  # line2 -> http_status
  local method="$1"
  local url="$2"
  local token="${3:-}"
  local data="${4:-}"
  local tmp
  tmp="$(mktemp)"

  if [[ -n "${token}" ]]; then
    if [[ -n "${data}" ]]; then
      code="$(curl -sS -m 10 -o "${tmp}" -w "%{http_code}" -X "${method}" "${url}" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${token}" \
        -d "${data}")"
    else
      code="$(curl -sS -m 10 -o "${tmp}" -w "%{http_code}" -X "${method}" "${url}" \
        -H "Authorization: Bearer ${token}")"
    fi
  else
    if [[ -n "${data}" ]]; then
      code="$(curl -sS -m 10 -o "${tmp}" -w "%{http_code}" -X "${method}" "${url}" \
        -H "Content-Type: application/json" \
        -d "${data}")"
    else
      code="$(curl -sS -m 10 -o "${tmp}" -w "%{http_code}" -X "${method}" "${url}")"
    fi
  fi

  body="$(cat "${tmp}")"
  rm -f "${tmp}"
  printf "%s\n%s\n" "${body}" "${code}"
}

extract_json_field() {
  local json="$1"
  local key_path="$2"
  python3 - "$json" "$key_path" <<'PY'
import json, sys
raw = sys.argv[1]
path = sys.argv[2].split(".")
try:
    obj = json.loads(raw)
    for p in path:
        if p.isdigit():
            obj = obj[int(p)]
        else:
            obj = obj[p]
    if obj is None:
        print("")
    else:
        print(obj)
except Exception:
    print("")
PY
}

assert_http_2xx() {
  local code="$1"
  local title="$2"
  if [[ "${code}" =~ ^2 ]]; then
    pass "${title}"
  else
    fail "${title} (HTTP ${code})"
  fi
}

assert_http_eq() {
  local code="$1"
  local expected="$2"
  local title="$3"
  if [[ "${code}" == "${expected}" ]]; then
    pass "${title}"
  else
    fail "${title} (HTTP ${code}, expect ${expected})"
  fi
}

say "INFO" "BASE_URL=${BASE_URL}"

# 0) health
say "STEP 0" "Health check"
resp="$(http_call GET "${BASE_URL}/health")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "GET /health"

# 1) register
say "STEP 1" "Register normal user"
payload="$(cat <<EOF
{"username":"${USER_NAME}","email":"${USER_EMAIL}","password":"${USER_PASS}"}
EOF
)"
resp="$(http_call POST "${API_BASE}/auth/register" "" "${payload}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "POST /api/auth/register"

# 2) login user
say "STEP 2" "Login normal user"
payload="$(cat <<EOF
{"username":"${USER_NAME}","password":"${USER_PASS}"}
EOF
)"
resp="$(http_call POST "${API_BASE}/auth/login" "" "${payload}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "POST /api/auth/login (normal)"
USER_ACCESS="$(extract_json_field "${body}" "data.access_token")"
USER_REFRESH="$(extract_json_field "${body}" "data.refresh_token")"
if [[ -n "${USER_ACCESS}" && -n "${USER_REFRESH}" ]]; then
  pass "Extract normal user tokens"
else
  fail "Extract normal user tokens"
fi

# 3) auth me
say "STEP 3" "Get current user"
resp="$(http_call GET "${API_BASE}/auth/me" "${USER_ACCESS}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "GET /api/auth/me"

# 4) refresh token
say "STEP 4" "Refresh token"
payload="$(cat <<EOF
{"refresh_token":"${USER_REFRESH}"}
EOF
)"
resp="$(http_call POST "${API_BASE}/auth/refresh" "" "${payload}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "POST /api/auth/refresh"
USER_ACCESS_NEW="$(extract_json_field "${body}" "data.access_token")"
if [[ -n "${USER_ACCESS_NEW}" ]]; then
  USER_ACCESS="${USER_ACCESS_NEW}"
  pass "Extract refreshed access token"
else
  fail "Extract refreshed access token"
fi

# 5) update password
say "STEP 5" "Update password"
payload="$(cat <<EOF
{"old_password":"${USER_PASS}","new_password":"${USER_NEW_PASS}"}
EOF
)"
resp="$(http_call PUT "${API_BASE}/auth/password" "${USER_ACCESS}" "${payload}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "PUT /api/auth/password"

# 6) user profile
say "STEP 6" "Get/update user profile"
resp="$(http_call GET "${API_BASE}/users/me" "${USER_ACCESS}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "GET /api/users/me"
payload="$(cat <<EOF
{"email":"updated_${USER_EMAIL}"}
EOF
)"
resp="$(http_call PUT "${API_BASE}/users/me" "${USER_ACCESS}" "${payload}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "PUT /api/users/me"

# 7) normal user forbidden admin
say "STEP 7" "Normal user should be forbidden for admin APIs"
resp="$(http_call GET "${API_BASE}/admin/users" "${USER_ACCESS}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_eq "${code}" "400" "GET /api/admin/users forbidden for normal user"

# 8) login admin
say "STEP 8" "Login admin and test admin APIs"
payload="$(cat <<EOF
{"username":"${ADMIN_NAME}","password":"${ADMIN_PASS}"}
EOF
)"
resp="$(http_call POST "${API_BASE}/auth/login" "" "${payload}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "POST /api/auth/login (admin)"
ADMIN_ACCESS="$(extract_json_field "${body}" "data.access_token")"
if [[ -n "${ADMIN_ACCESS}" ]]; then
  pass "Extract admin token"
else
  fail "Extract admin token"
fi

resp="$(http_call GET "${API_BASE}/admin/users" "${ADMIN_ACCESS}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "GET /api/admin/users (admin)"

resp="$(http_call GET "${API_BASE}/admin/system-configs" "${ADMIN_ACCESS}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "GET /api/admin/system-configs (admin)"

payload='{"config_value":"true"}'
resp="$(http_call PUT "${API_BASE}/admin/system-configs/test_switch" "${ADMIN_ACCESS}" "${payload}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "PUT /api/admin/system-configs/{key} (admin)"

resp="$(http_call GET "${API_BASE}/admin/ai-logs" "${ADMIN_ACCESS}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "GET /api/admin/ai-logs (admin)"

resp="$(http_call GET "${API_BASE}/admin/ocr-logs" "${ADMIN_ACCESS}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "GET /api/admin/ocr-logs (admin)"

resp="$(http_call GET "${API_BASE}/admin/system-logs" "${ADMIN_ACCESS}")"
body="$(echo "${resp}" | sed -n '1p')"
code="$(echo "${resp}" | sed -n '2p')"
assert_http_2xx "${code}" "GET /api/admin/system-logs (admin)"

say "RESULT" "PASS=${PASS_COUNT} FAIL=${FAIL_COUNT}"
if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi

echo "All tests passed."
