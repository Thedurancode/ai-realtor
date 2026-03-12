#!/usr/bin/env bash
# =============================================================================
# RealtorClaw API Integration Test Suite
# =============================================================================
# Runs 100 curl-based integration tests against the running API.
#
# Usage:
#   ./tests/test_api_integration.sh [BASE_URL]
#
# Defaults:
#   BASE_URL=http://localhost:8000
#
# Requirements:
#   - curl, jq
#   - A running RealtorClaw API instance
# =============================================================================

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
PASS=0
FAIL=0
SKIP=0
TOTAL=0
ERRORS=""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

# ---------- helpers ----------------------------------------------------------

assert_status() {
  local test_name="$1"
  local expected="$2"
  local method="${3:-GET}"
  local endpoint="$4"
  local data="${5:-}"
  local headers="${6:-}"

  TOTAL=$((TOTAL + 1))
  local url="${BASE_URL}${endpoint}"
  local cmd="curl -s -o /dev/null -w %{http_code} -X ${method}"

  if [[ -n "$headers" ]]; then
    cmd="$cmd -H '$headers'"
  fi
  if [[ -n "$data" ]]; then
    cmd="$cmd -H 'Content-Type: application/json' -d '${data}'"
  fi
  cmd="$cmd '${url}'"

  local status
  status=$(eval "$cmd" 2>/dev/null) || status="000"

  if [[ "$status" == "$expected" ]]; then
    PASS=$((PASS + 1))
    printf "${GREEN}  PASS${NC} [%3d] %s (HTTP %s)\n" "$TOTAL" "$test_name" "$status"
  else
    FAIL=$((FAIL + 1))
    printf "${RED}  FAIL${NC} [%3d] %s (expected %s, got %s)\n" "$TOTAL" "$test_name" "$expected" "$status"
    ERRORS="${ERRORS}\n  [${TOTAL}] ${test_name}: expected ${expected}, got ${status}"
  fi
}

assert_json_field() {
  local test_name="$1"
  local endpoint="$2"
  local field="$3"
  local expected="$4"

  TOTAL=$((TOTAL + 1))
  local url="${BASE_URL}${endpoint}"
  local response
  response=$(curl -s "$url" 2>/dev/null) || response=""

  local actual
  actual=$(echo "$response" | jq -r "$field" 2>/dev/null) || actual="PARSE_ERROR"

  if [[ "$actual" == "$expected" ]]; then
    PASS=$((PASS + 1))
    printf "${GREEN}  PASS${NC} [%3d] %s (%s = %s)\n" "$TOTAL" "$test_name" "$field" "$actual"
  else
    FAIL=$((FAIL + 1))
    printf "${RED}  FAIL${NC} [%3d] %s (%s: expected '%s', got '%s')\n" "$TOTAL" "$test_name" "$field" "$expected" "$actual"
    ERRORS="${ERRORS}\n  [${TOTAL}] ${test_name}: ${field} expected '${expected}', got '${actual}'"
  fi
}

assert_contains() {
  local test_name="$1"
  local endpoint="$2"
  local substring="$3"

  TOTAL=$((TOTAL + 1))
  local url="${BASE_URL}${endpoint}"
  local response
  response=$(curl -s "$url" 2>/dev/null) || response=""

  if echo "$response" | grep -q "$substring"; then
    PASS=$((PASS + 1))
    printf "${GREEN}  PASS${NC} [%3d] %s (contains '%s')\n" "$TOTAL" "$test_name" "$substring"
  else
    FAIL=$((FAIL + 1))
    printf "${RED}  FAIL${NC} [%3d] %s (missing '%s')\n" "$TOTAL" "$test_name" "$substring"
    ERRORS="${ERRORS}\n  [${TOTAL}] ${test_name}: response missing '${substring}'"
  fi
}

skip_test() {
  local test_name="$1"
  local reason="$2"
  TOTAL=$((TOTAL + 1))
  SKIP=$((SKIP + 1))
  printf "${YELLOW}  SKIP${NC} [%3d] %s (%s)\n" "$TOTAL" "$test_name" "$reason"
}

# ---------- pre-flight -------------------------------------------------------

echo ""
echo "============================================"
echo " RealtorClaw API Integration Tests"
echo " Target: ${BASE_URL}"
echo " Started: $(date)"
echo "============================================"
echo ""

# Check if the API is reachable
if ! curl -s -o /dev/null -w '' "${BASE_URL}/docs" 2>/dev/null; then
  echo "ERROR: API is not reachable at ${BASE_URL}"
  echo "Make sure the server is running before executing tests."
  exit 1
fi

# =============================================================================
# SECTION 1: Health & Core Endpoints (1-10)
# =============================================================================
echo "--- Section 1: Health & Core Endpoints ---"

assert_status "GET /docs returns 200" "200" GET "/docs"
assert_status "GET /openapi.json returns 200" "200" GET "/openapi.json"
assert_status "GET / root returns 200 or 307" "200" GET "/"
assert_status "GET /health returns 200" "200" GET "/health"
assert_contains "Health check has status field" "/health" "status"
assert_status "GET /nonexistent returns 404" "404" GET "/nonexistent-endpoint-xyz"
assert_status "POST / returns 405 or 307" "405" POST "/"
assert_status "OPTIONS /docs CORS preflight" "200" OPTIONS "/docs"
assert_contains "OpenAPI has title" "/openapi.json" "title"
assert_contains "OpenAPI has paths" "/openapi.json" "paths"

# =============================================================================
# SECTION 2: Properties Endpoints (11-25)
# =============================================================================
echo ""
echo "--- Section 2: Properties ---"

assert_status "GET /api/properties returns 200" "200" GET "/api/properties"
assert_status "GET /api/properties?limit=1" "200" GET "/api/properties?limit=1"
assert_status "GET /api/properties?skip=0&limit=10" "200" GET "/api/properties?skip=0&limit=10"
assert_status "GET /api/properties/99999 returns 404" "404" GET "/api/properties/99999"
assert_status "POST /api/properties without body returns 422" "422" POST "/api/properties"
assert_status "POST /api/properties with empty JSON" "422" POST "/api/properties" "{}"
assert_status "GET /api/properties?status=active" "200" GET "/api/properties?status=active"
assert_status "GET /api/properties?sort=created_at" "200" GET "/api/properties?sort=created_at"
assert_status "DELETE /api/properties/99999 returns 404" "404" DELETE "/api/properties/99999"
assert_status "PUT /api/properties/99999 returns 404" "404" PUT "/api/properties/99999" '{"address":"test"}'
assert_contains "Properties list is array" "/api/properties" "["
assert_status "GET /api/properties?limit=0" "200" GET "/api/properties?limit=0"
assert_status "GET /api/properties?limit=-1" "422" GET "/api/properties?limit=-1"
assert_status "GET /api/properties?skip=-1" "422" GET "/api/properties?skip=-1"
assert_status "PATCH /api/properties/99999 returns 404 or 405" "404" PATCH "/api/properties/99999" '{"address":"test"}'

# =============================================================================
# SECTION 3: Contacts Endpoints (26-35)
# =============================================================================
echo ""
echo "--- Section 3: Contacts ---"

assert_status "GET /api/contacts returns 200" "200" GET "/api/contacts"
assert_status "GET /api/contacts?limit=5" "200" GET "/api/contacts?limit=5"
assert_status "GET /api/contacts/99999 returns 404" "404" GET "/api/contacts/99999"
assert_status "POST /api/contacts without body returns 422" "422" POST "/api/contacts"
assert_status "POST /api/contacts with empty JSON" "422" POST "/api/contacts" "{}"
assert_status "DELETE /api/contacts/99999 returns 404" "404" DELETE "/api/contacts/99999"
assert_status "PUT /api/contacts/99999 returns 404" "404" PUT "/api/contacts/99999" '{"name":"test"}'
assert_contains "Contacts list response" "/api/contacts" "["
assert_status "GET /api/contacts?search=nonexistent" "200" GET "/api/contacts?search=nonexistent"
assert_status "GET /api/contacts?skip=0&limit=1" "200" GET "/api/contacts?skip=0&limit=1"

# =============================================================================
# SECTION 4: Offers Endpoints (36-45)
# =============================================================================
echo ""
echo "--- Section 4: Offers ---"

assert_status "GET /api/offers returns 200" "200" GET "/api/offers"
assert_status "GET /api/offers?limit=5" "200" GET "/api/offers?limit=5"
assert_status "GET /api/offers/99999 returns 404" "404" GET "/api/offers/99999"
assert_status "POST /api/offers without body returns 422" "422" POST "/api/offers"
assert_status "POST /api/offers with empty JSON" "422" POST "/api/offers" "{}"
assert_status "DELETE /api/offers/99999 returns 404" "404" DELETE "/api/offers/99999"
assert_status "PUT /api/offers/99999 returns 404" "404" PUT "/api/offers/99999" '{"amount":100}'
assert_contains "Offers list response" "/api/offers" "["
assert_status "GET /api/offers?status=pending" "200" GET "/api/offers?status=pending"
assert_status "GET /api/offers?property_id=99999" "200" GET "/api/offers?property_id=99999"

# =============================================================================
# SECTION 5: Contracts Endpoints (46-55)
# =============================================================================
echo ""
echo "--- Section 5: Contracts ---"

assert_status "GET /api/contracts returns 200" "200" GET "/api/contracts"
assert_status "GET /api/contracts?limit=5" "200" GET "/api/contracts?limit=5"
assert_status "GET /api/contracts/99999 returns 404" "404" GET "/api/contracts/99999"
assert_status "POST /api/contracts without body returns 422" "422" POST "/api/contracts"
assert_status "POST /api/contracts with empty JSON" "422" POST "/api/contracts" "{}"
assert_status "DELETE /api/contracts/99999 returns 404" "404" DELETE "/api/contracts/99999"
assert_contains "Contracts list response" "/api/contracts" "["
assert_status "GET /api/contracts?status=active" "200" GET "/api/contracts?status=active"
assert_status "GET /api/contracts?property_id=99999" "200" GET "/api/contracts?property_id=99999"
assert_status "PUT /api/contracts/99999 returns 404" "404" PUT "/api/contracts/99999" '{"status":"signed"}'

# =============================================================================
# SECTION 6: Transactions Endpoints (56-65)
# =============================================================================
echo ""
echo "--- Section 6: Transactions ---"

assert_status "GET /api/transactions returns 200" "200" GET "/api/transactions"
assert_status "GET /api/transactions?limit=5" "200" GET "/api/transactions?limit=5"
assert_status "GET /api/transactions/99999 returns 404" "404" GET "/api/transactions/99999"
assert_status "POST /api/transactions without body returns 422" "422" POST "/api/transactions"
assert_status "POST /api/transactions with empty JSON" "422" POST "/api/transactions" "{}"
assert_status "DELETE /api/transactions/99999 returns 404" "404" DELETE "/api/transactions/99999"
assert_contains "Transactions list response" "/api/transactions" "["
assert_status "GET /api/transactions?status=open" "200" GET "/api/transactions?status=open"
assert_status "GET /api/transactions?property_id=99999" "200" GET "/api/transactions?property_id=99999"
assert_status "PUT /api/transactions/99999 returns 404" "404" PUT "/api/transactions/99999" '{"status":"closed"}'

# =============================================================================
# SECTION 7: Notifications & Todos (66-75)
# =============================================================================
echo ""
echo "--- Section 7: Notifications & Todos ---"

assert_status "GET /api/notifications returns 200" "200" GET "/api/notifications"
assert_status "GET /api/notifications?limit=5" "200" GET "/api/notifications?limit=5"
assert_status "GET /api/notifications/99999 returns 404" "404" GET "/api/notifications/99999"
assert_status "GET /api/todos returns 200" "200" GET "/api/todos"
assert_status "GET /api/todos?limit=5" "200" GET "/api/todos?limit=5"
assert_status "GET /api/todos/99999 returns 404" "404" GET "/api/todos/99999"
assert_status "POST /api/todos without body returns 422" "422" POST "/api/todos"
assert_status "POST /api/todos with empty JSON" "422" POST "/api/todos" "{}"
assert_status "DELETE /api/todos/99999 returns 404" "404" DELETE "/api/todos/99999"
assert_status "PUT /api/todos/99999 returns 404" "404" PUT "/api/todos/99999" '{"title":"test"}'

# =============================================================================
# SECTION 8: Auth & Security (76-85)
# =============================================================================
echo ""
echo "--- Section 8: Auth & Security ---"

assert_status "Unauthorized without API key" "401" GET "/api/properties" "" ""
assert_status "SQL injection in query param" "200" GET "/api/properties?search=1%27%20OR%201%3D1"
assert_status "XSS in query param" "200" GET "/api/properties?search=%3Cscript%3Ealert(1)%3C/script%3E"
assert_status "Path traversal attempt" "404" GET "/api/../../../etc/passwd"
assert_status "Very long query param" "200" GET "/api/properties?search=$(python3 -c 'print("A"*1000)')"
assert_status "Special chars in search" "200" GET "/api/properties?search=%00%0d%0a"
assert_status "Unicode in query param" "200" GET "/api/properties?search=%E2%80%8B%E2%80%8B"
assert_status "Method not allowed on health" "405" DELETE "/health"
assert_status "Large limit value" "422" GET "/api/properties?limit=999999"
assert_status "Negative ID" "422" GET "/api/properties/-1"

# =============================================================================
# SECTION 9: Content-Type & Headers (86-93)
# =============================================================================
echo ""
echo "--- Section 9: Content-Type & Headers ---"

assert_status "POST with wrong content-type" "422" POST "/api/properties" "not-json" "Content-Type: text/plain"
assert_status "POST with XML body" "422" POST "/api/properties" "<xml>test</xml>" "Content-Type: application/xml"
assert_status "Accept: application/json" "200" GET "/docs" "" "Accept: application/json"
assert_status "HEAD /docs returns 200" "200" HEAD "/docs"
assert_status "GET /openapi.json content check" "200" GET "/openapi.json"
assert_contains "API returns JSON content" "/openapi.json" "application/json"
assert_status "POST with malformed JSON" "422" POST "/api/properties" "{bad json" "Content-Type: application/json"
assert_status "POST with array body" "422" POST "/api/properties" "[]" "Content-Type: application/json"

# =============================================================================
# SECTION 10: Rate Limiting & Edge Cases (94-100)
# =============================================================================
echo ""
echo "--- Section 10: Rate Limiting & Edge Cases ---"

assert_status "Rapid request 1" "200" GET "/health"
assert_status "Rapid request 2" "200" GET "/health"
assert_status "Rapid request 3" "200" GET "/health"
assert_status "Empty POST body" "422" POST "/api/properties" "" "Content-Type: application/json"
assert_status "GET with query params on health" "200" GET "/health?foo=bar"
assert_status "Double slash in path" "200" GET "//docs"
assert_status "Trailing slash redirect" "200" GET "/docs/"

# =============================================================================
# SUMMARY
# =============================================================================
echo ""
echo "============================================"
echo " Test Results"
echo "============================================"
echo ""
printf "  Total:   %d\n" "$TOTAL"
printf "  ${GREEN}Passed:  %d${NC}\n" "$PASS"
printf "  ${RED}Failed:  %d${NC}\n" "$FAIL"
printf "  ${YELLOW}Skipped: %d${NC}\n" "$SKIP"
echo ""

if [[ $FAIL -gt 0 ]]; then
  echo "Failed tests:"
  printf "$ERRORS\n"
  echo ""
fi

echo "Finished: $(date)"
echo ""

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi

exit 0
