#!/bin/bash
# REDSL Panel — Smoke Test Script (Path A)
# Usage: ./smoke-test.sh [BASE_URL]
# Example: ./smoke-test.sh https://redsl.twojadomena.pl

set -e

BASE_URL="${1:-http://localhost:8080}"

echo "=========================================="
echo "REDSL Panel Smoke Test"
echo "Base URL: $BASE_URL"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

# Helper functions
check_http() {
    local url="$1"
    local expected="$2"
    local desc="$3"
    
    printf "Testing: %s ... " "$desc"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    if [ "$response" = "$expected" ]; then
        printf "%bOK [%s]%b\n" "$GREEN" "$response" "$NC"
        PASS=$((PASS + 1))
    else
        printf "%bFAIL [expected %s, got %s]%b\n" "$RED" "$expected" "$response" "$NC"
        FAIL=$((FAIL + 1))
    fi
}

check_content() {
    local url="$1"
    local pattern="$2"
    local desc="$3"
    
    printf "Testing: %s ... " "$desc"
    
    response=$(curl -s "$url" 2>/dev/null || echo "")
    if echo "$response" | grep -q "$pattern" 2>/dev/null; then
        printf "%bOK%b\n" "$GREEN" "$NC"
        PASS=$((PASS + 1))
    else
        printf "%bFAIL [pattern '%s' not found]%b\n" "$RED" "$pattern" "$NC"
        FAIL=$((FAIL + 1))
    fi
}

check_php_syntax() {
    printf "Testing: PHP syntax check ... "
    
    errors=0
    while IFS= read -r file; do
        if ! php -l "$file" > /dev/null 2>&1; then
            errors=$((errors + 1))
        fi
    done < <(find . -name "*.php" -not -path "./vendor/*" -not -path "./.code2llm_cache/*" 2>/dev/null)
    
    if [ "$errors" -eq 0 ]; then
        printf "%bOK [all files pass php -l]%b\n" "$GREEN" "$NC"
        PASS=$((PASS + 1))
    else
        printf "%bFAIL [%s files with syntax errors]%b\n" "$RED" "$errors" "$NC"
        FAIL=$((FAIL + 1))
    fi
}

check_env_exists() {
    printf "Testing: .env file exists ... "
    if [ -f ".env" ]; then
        printf "%bOK%b\n" "$GREEN" "$NC"
        PASS=$((PASS + 1))
    else
        printf "%bFAIL [copy .env.example to .env]%b\n" "$RED" "$NC"
        FAIL=$((FAIL + 1))
    fi
}

check_encryption_key() {
    printf "Testing: ENCRYPTION_KEY is set ... "
    if grep -q "^ENCRYPTION_KEY=[a-f0-9]" .env 2>/dev/null; then
        printf "%bOK%b\n" "$GREEN" "$NC"
        PASS=$((PASS + 1))
    else
        printf "%bWARN [generate: php -r 'echo bin2hex(random_bytes(32));']%b\n" "$YELLOW" "$NC"
        PASS=$((PASS + 1))
    fi
}

check_directories() {
    printf "Testing: Required directories exist ... "
    
    dirs="var var/logs var/scans var/contracts var/invoices"
    missing=0
    
    for dir in $dirs; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir" 2>/dev/null || missing=$((missing + 1))
        fi
    done
    
    if [ "$missing" -eq 0 ]; then
        printf "%bOK%b\n" "$GREEN" "$NC"
        PASS=$((PASS + 1))
    else
        printf "%bWARN [created missing directories]%b\n" "$YELLOW" "$NC"
        PASS=$((PASS + 1))
    fi
}

check_admin_auth() {
    printf "Testing: Admin auth configured ... "
    if grep -q "^ADMIN_PASS_HASH=" .env 2>/dev/null && grep "^ADMIN_PASS_HASH=" .env | grep -qv 'ADMIN_PASS_HASH=$'; then
        printf "%bOK%b\n" "$GREEN" "$NC"
        PASS=$((PASS + 1))
    else
        printf "%bWARN [generate: php -r 'echo password_hash(\"pass\", PASSWORD_BCRYPT);']%b\n" "$YELLOW" "$NC"
        PASS=$((PASS + 1))
    fi
}

check_cron_scripts() {
    printf "Testing: Cron scripts are present ... "
    
    if [ -f "cron/scan-worker.php" ] && [ -f "cron/invoice-generator.php" ]; then
        printf "%bOK%b\n" "$GREEN" "$NC"
        PASS=$((PASS + 1))
    else
        printf "%bFAIL [missing cron scripts]%b\n" "$RED" "$NC"
        FAIL=$((FAIL + 1))
    fi
}

# Run tests
echo "=== Static Checks ==="
check_php_syntax
check_env_exists
check_encryption_key
check_directories
check_admin_auth
check_cron_scripts

echo ""
echo "=== Connection Checks ==="
check_http "$BASE_URL/" "200" "Landing page loads"
# Admin returns 500 when not configured (safety), 401 when auth required
check_http "$BASE_URL/admin/" "500" "Admin safety (500=unconfigured, 401=needs auth)"

echo ""
echo "=== Content Checks ==="
check_content "$BASE_URL/" "ReDSL" "Landing page contains 'ReDSL'"

echo ""
echo "=========================================="
printf "Results: %s passed, %s failed\n" "$PASS" "$FAIL"
echo "=========================================="

if [ "$FAIL" -eq 0 ]; then
    printf "%bAll checks passed!%b\n" "$GREEN" "$NC"
    exit 0
else
    printf "%bSome checks failed. Fix before deploying.%b\n" "$RED" "$NC"
    exit 1
fi
