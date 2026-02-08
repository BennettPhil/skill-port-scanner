#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN="$SCRIPT_DIR/run.sh"
PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

echo "=== port-scanner tests ==="

# Test 1: --help exits 0
echo "[1] --help exits 0"
if "$RUN" --help >/dev/null 2>&1; then
    pass "--help exits 0"
else
    fail "--help exits 0"
fi

# Test 2: text output contains "Port" header
echo "[2] text output contains Port header"
OUTPUT=$("$RUN" --format text 2>&1) || true
if echo "$OUTPUT" | grep -qF "Port"; then
    pass "text output has Port header"
else
    fail "text output has Port header"
fi

# Test 3: json output is valid JSON with "ports" key
echo "[3] json output is valid JSON with ports key"
JSON_OUTPUT=$("$RUN" --format json 2>&1) || true
if echo "$JSON_OUTPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'ports' in d" 2>/dev/null; then
    pass "json output valid with ports key"
else
    fail "json output valid with ports key"
fi

# Test 4: no args runs without error
echo "[4] no args runs without error"
if "$RUN" >/dev/null 2>&1; then
    pass "no args runs fine"
else
    fail "no args runs fine"
fi

# Test 5: --common flag works
echo "[5] --common flag works"
if "$RUN" --common >/dev/null 2>&1; then
    pass "--common runs fine"
else
    fail "--common runs fine"
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
