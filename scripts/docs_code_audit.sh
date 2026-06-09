#!/usr/bin/env bash
# scripts/docs_code_audit.sh — converged docs+code audit gate
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

FAIL=0

echo "=== Code Gates ==="

# 1. ruff
echo -n "ruff check ... "
if uv run ruff check . >/dev/null 2>&1; then echo "ok"; else echo "FAIL"; FAIL=1; fi

# 2. mypy
echo -n "mypy --strict ... "
if uv run mypy src/ >/dev/null 2>&1; then echo "ok"; else echo "FAIL"; FAIL=1; fi

# 3. pytest
echo -n "pytest ... "
if uv run pytest -q --tb=no >/dev/null 2>&1; then echo "ok"; else echo "FAIL"; FAIL=1; fi

# 4. coverage
echo -n "coverage ... "
if uv run pytest --cov=ado_odata_async --cov-fail-under=85 -q --tb=no >/dev/null 2>&1; then echo "ok"; else echo "FAIL"; FAIL=1; fi

# 5. audit.sh
echo -n "audit.sh ... "
if bash scripts/audit.sh >/dev/null 2>&1; then echo "ok"; else echo "FAIL"; FAIL=1; fi

echo ""
echo "=== Doc Gates ==="

# 6. public API signature
echo -n "public API signature ... "
CURRENT_SIG=$(python3 -c "import base64; import sys; sys.path.insert(0, 'src'); from ado_odata_async import __all__; print(base64.b64encode(str(sorted(__all__)).encode()).decode())" 2>/dev/null || echo "ERROR")
if [ -f .refactor_baseline.env ]; then
    BASELINE_SIG=$(grep "^PUBLIC_API_SIGNATURE=" .refactor_baseline.env | sed 's/^PUBLIC_API_SIGNATURE=//' | tr -d '\n')
    if [ "$CURRENT_SIG" = "$BASELINE_SIG" ]; then
        echo "ok (unchanged)"
    else
        echo "FAIL (signature changed!)"
        FAIL=1
    fi
else
    echo "skip (no baseline)"
fi

# 7. HANDOFF.md link check
echo -n "HANDOFF.md -> AGENTS.md ... "
if grep -q '\[AGENTS.md\](\.\.\/AGENTS.md)' docs/HANDOFF.md; then
    echo "ok"
else
    echo "FAIL (link not fixed)"
    FAIL=1
fi

echo ""
if [ $FAIL -eq 0 ]; then
    echo "AUDIT PASSED"
    exit 0
else
    echo "AUDIT FAILED"
    exit 1
fi
