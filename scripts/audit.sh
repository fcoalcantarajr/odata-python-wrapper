#!/usr/bin/env bash
set -euo pipefail

FAIL=0
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

# Exclusões globais aplicadas a TODOS os checks. `.venv/` é o vilão clássico:
# cada pacote Python instalado tem um METADATA com 'pip install <pkg>' no README
# e isso disparava HR-2 com 12+ falsos positivos após o primeiro `uv sync` (May
# 2026: yarl, typing_inspection, annotated_types, pathspec, identify, ruff,
# pydantic, hypothesis, python_dateutil, packaging, pytest_cov, cfgv).
# Outras diretórias são build/cache artifacts — não código nosso, não audita.
# Quando adicionar novo check(), passe ${EXCLUDES[@]} ou re-introduz o bug.
EXCLUDES=(
  --glob '!.git'
  --glob '!.venv'
  --glob '!node_modules'
  --glob '!dist'
  --glob '!build'
  --glob '!*.egg-info'
  --glob '!htmlcov'
  --glob '!.pytest_cache'
  --glob '!.mypy_cache'
  --glob '!.ruff_cache'
  --glob '!.hypothesis'
  --glob '!__pycache__'
)

# Fail-fast: rg não pode estar ausente. Sem isso, `! rg ...` interpreta exit 127
# como 'nenhum match' e imprime `[audit] ok` → falso positivo silencioso em
# todo check, gate de /commit do Step 4 passa em qualquer coisa proibida.
command -v rg >/dev/null 2>&1 || { echo "[audit] FATAL: ripgrep (rg) ausente. apt-get install -y ripgrep"; exit 2; }

check() {
  local label="$1" pattern="$2" scope="$3"
  if rg --hidden --glob "$scope" "${EXCLUDES[@]}" -nP "$pattern" -q .; then
    echo "[audit] FAIL: $label"
    rg --hidden --glob "$scope" "${EXCLUDES[@]}" -nP "$pattern" .
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

exit $FAIL
