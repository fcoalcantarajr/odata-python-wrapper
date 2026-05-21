#!/usr/bin/env bash
set -euo pipefail

FAIL=0
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

check() {
  local label="$1" pattern="$2" scope="$3"
  if rg --hidden --glob '!.git' --glob "$scope" -nP "$pattern" -q .; then
    echo "[audit] FAIL: $label"
    rg --hidden --glob '!.git' --glob "$scope" -nP "$pattern" .
    FAIL=1
  else
    echo "[audit] ok:   $label"
  fi
}

# 1. type: ignore sem código e razão
check "bare # type: ignore (HR-5)"        '# type:\s*ignore(?!\[[\w,-]+\])'             'src/**'
# 2. cast as Any fora de stubs
check "as Any (HR-5)"                      '\bas Any\b'                                  'src/**'
# 3. pip install ou python direto
check "pip install (HR-2)"                 '^\s*pip\s+install\b'                         '**'
check "python direct (HR-2)"               '^\s*python\s+'                               'scripts/**'
# 4. BasicAuth com user não vazio
check "BasicAuth non-empty user (HR-8)"   'BasicAuth\(\s*"[^"]+"\s*,'                  'src/**'
# 5. datetime literal com prefixo
check "datetime literal prefix (HR-11)"   "datetime'"                                   'src/**'
# 6. \$expand=Revisions
check '\$expand=Revisions (HR-14)'         '\\$expand=Revisions'                         'src/**'
# 7. requests/urllib
check "sync requests in src (HR-6)"       '^\s*(import|from)\s+(requests|urllib)\b'    'src/**'
# 8. print(...pat...)
check "PAT leak in print (HR-16)"         'print\([^)]*\bpat\b[^)]*\)'                  'src/**'
# 9. v2.0 literal
check "_odata/v2.0 literal in src (HR-19)" '_odata/v2\.0'                                'src/**'

# 10. HR-22: apenas notion-curator pode ter `mcp:` com `notion` no permission.
check_hr22() {
  local violators
  violators=$(rg --hidden --glob '!.git' --glob '.opencode/agents/*.md' -l 'mcp:' | grep -v 'notion-curator.md' || true)
  if [[ -n "$violators" ]]; then
    echo "[audit] FAIL: HR-22 — only notion-curator may declare mcp permission. Violators:"
    echo "$violators"
    FAIL=1
  else
    echo "[audit] ok:   HR-22 (only notion-curator declares mcp:)"
  fi
}
check_hr22

exit $FAIL
