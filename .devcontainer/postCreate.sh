#!/usr/bin/env bash
set -euo pipefail

# ─── 0. Perms dos paths user-level (bind mounts criam pais como root) ──
# CRÍTICO: chown NÃO recursivo. Os filhos $HOME/.local/share/opencode e
# $HOME/.config/opencode são bind mounts vindos do macOS host (Docker
# Desktop usa virtiofs/gRPC-FUSE), que bloqueia chown nesses paths mesmo
# com sudo (retorna EPERM). Com `set -euo pipefail` o primeiro EPERM mata
# o script. Só precisamos corrigir os diretórios que CRIAMOS com sudo
# mkdir aqui; os binds já vêm com UID/GID corretos da fonte.
sudo mkdir -p "$HOME/.local/bin" "$HOME/.local/state" "$HOME/.local/share" "$HOME/.config"
sudo chown "$(id -u):$(id -g)" \
  "$HOME/.local" \
  "$HOME/.local/bin" \
  "$HOME/.local/state" \
  "$HOME/.local/share" \
  "$HOME/.config"

# ─── 0.4. Detecta e renomeia configs legacy do opencode ──────────────
# opencode pré-1.15 usava schema v1 com chaves `telemetry`, `providers`,
# `sessions` em ~/.config/opencode/opencode.jsonc. opencode 1.15+ rejeita
# essas chaves com ConfigInvalidError → quebra TODO boot da TUI
# (config.providers, provider.list, app.agents, config.get falham em
# cascata), MESMO com um ~/.config/opencode/opencode.json (moderno)
# válido. opencode lê AMBOS .json e .jsonc da pasta global. Como
# ~/.config/opencode é bind RW do host, esses arquivos zumbi sobrevivem
# entre projetos e versões. Detecta pelas chaves legacy e renomeia pra
# .LEGACY-BAK (preserva pra inspeção; não deleta).
for f in opencode.jsonc oh-my-opencode.jsonc; do
  legacy_path="$HOME/.config/opencode/$f"
  if [ -f "$legacy_path" ] && grep -qE '"(telemetry|providers|sessions)"' "$legacy_path" 2>/dev/null; then
    echo "[postCreate] WARN: $legacy_path tem chaves legacy (schema v1). Renomeando pra .LEGACY-BAK"
    mv "$legacy_path" "${legacy_path}.LEGACY-BAK"
  fi
done

# ─── 0.5. uv (instalado do astral.sh; sem features ghcr.io) ──────────
if ! command -v uv >/dev/null 2>&1; then
  echo "==> Installing uv from astral.sh..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
else
  echo "==> uv already present."
fi

# ─── 0.6. bun (instalado do bun.sh; sem features ghcr.io) ───────────
if ! command -v bun >/dev/null 2>&1; then
  echo "==> Installing bun from bun.sh..."
  curl -fsSL https://bun.sh/install | bash
  export BUN_INSTALL="$HOME/.bun"
  export PATH="$BUN_INSTALL/bin:$PATH"
else
  echo "==> bun already present."
fi

# ─── 0.7. gh CLI (apt repo oficial de cli.github.com) ───────────────
if ! command -v gh >/dev/null 2>&1; then
  echo "==> Installing gh CLI from cli.github.com..."
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
  sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
  # GOTCHA da imagem python:1-3.12-bookworm: vem com
  # /etc/apt/sources.list.d/yarn.list apontando pra dl.yarnpkg.com com chave
  # GPG rotacionada. Isso faz `apt-get update` retornar exit 100
  # (E: repository is not signed). Se a gente usasse `update && install`, o
  # `&&` pularia o install silenciosamente E `set -e` NÃO mata em compound
  # `&&` (gotcha POSIX/bash documentado). Fix em duas camadas:
  #   (1) remove yarn.list antes do update (causa raiz);
  #   (2) separa update e install (defesa em profundidade pra qualquer outro
  #       repo problemático no futuro matar o script via `set -e`).
  sudo rm -f /etc/apt/sources.list.d/yarn.list
  sudo apt-get update -qq
  sudo apt-get install -y -qq gh
else
  echo "==> gh CLI already present."
fi

# ─── 0.8. ripgrep (necessário pelo scripts/audit.sh do Step 7) ──────
# audit.sh roda 10 greps via `rg` pra detectar HARD RULE violations
# (HR-2/5/6/8/11/14/16/19). Sem ripgrep, cada check falha com
# `rg: command not found` (exit 127), MAS a estrutura `! rg ... && echo ok`
# do script lê exit 127 como "nenhum match" e imprime `[audit] ok` —
# FALSO POSITIVO silencioso que faz commits autônomos passarem na gate
# do Step 4 (/commit). Observado May 2026 no primeiro bootstrap do
# devcontainer (rg não estava no apt cache do python:1-3.12-bookworm).
if ! command -v rg >/dev/null 2>&1; then
  echo "==> Installing ripgrep from apt..."
  sudo apt-get install -y -qq ripgrep
else
  echo "==> ripgrep already present."
fi

# git já vem no python:1-3.12-bookworm (versão >=2.39); pulamos o feature.

# ─── 1. Git identity local do agente (NÃO é o do humano) ────────────
# git-keeper assina commits autônomos como omo-agent. O ~/.gitconfig do
# host (bind readonly) continua sendo a identidade do Chicão.
if [ -d "$PWD/.git" ]; then
  git config user.name  "omo-agent"
  git config user.email "omo-agent@ado-odata-async.local"
fi

# ─── 2. opencode CLI + omo via bun ──────────────────────────────────
if ! command -v opencode >/dev/null 2>&1; then
  echo "==> Installing opencode CLI..."
  bun install -g opencode-ai
else
  echo "==> opencode CLI already present."
fi

# omo (oh-my-openagent): instala o binário `omo` E faz wiring do plugin
# em ~/.config/opencode/opencode.json (ambos numa tacada via `bunx`).
#
# COMANDO CANON: `bunx oh-my-openagent install ...`
# Confirmado em README + docs/guide/installation.md (May 2026):
#   1. Baixa o binário standalone do omo pra plataforma (11 platform
#      binaries shipados: macOS/Linux/Windows em ARM64/x64/musl)
#   2. Wira o plugin entry em ~/.config/opencode/opencode.json
#   3. "Use Bun only for installation. Do not use npm/yarn/pnpm." — docs.
#
# NÃO USAR (anti-patterns observados May 2026):
#   - `bun install -g oh-my-openagent` → instala o pacote npm mas NÃO
#     cria o symlink `~/.bun/bin/omo` de forma confiável (bun 1.3.14 +
#     oh-my-openagent 2.0.0). Sintoma: bootstrap reporta GREEN, `which<br>#     omo` retorna vazio.
#   - Teste `bunx --bun omo --version` → retornava exit 0 mesmo SEM omo
#     instalado, porque bunx fetcha um pacote `omo` legacy não-relacionado
#     do npm registry. O `if !` antigo achava que tava tudo certo e pulava
#     o install. Resultado em cascata: agentes omo (atlas, hephaestus,
#     sisyphus, oracle, prometheus, metis, librarian) indisponíveis em
#     RUNTIME, descoberto só na primeira invocação dos commands
#     /spec-check, /test-first, /implement, /review.
#   - Tampouco existe `scripts/install.sh` no repo — é alucinação de LLM
#     ao mimicar o padrão `curl ... | bash` de outros installers.
#
# Flags non-interactive (modo CI/devcontainer): `--no-tui` pula o wizard
# interativo (Ink TUI). Cada subscription DEVE ser respondida explicitamente.
# Schema conforme docs/guide/installation.md (May 2026):
#   bunx oh-my-openagent install --no-tui \
#     --claude=<yes|no|max20>   (OBRIGATÓRIO)
#     --gemini=<yes|no>         (OBRIGATÓRIO)
#     --copilot=<yes|no>        (OBRIGATÓRIO)
#     [--openai=<yes|no>]
#     [--opencode-go=<yes|no>]
#     [--opencode-zen=<yes|no>]
#     [--zai-coding-plan=<yes|no>]
#     [--kimi-for-coding=<yes|no>]
#     [--vercel-ai-gateway=<yes|no>]
#     [--skip-auth]    — pula `opencode auth login` (faz manual depois)
# Aqui vai TUDO `=no` (free Zen models only: big-pickle,
# deepseek-v4-flash-free, nemotron-3-super-free, acessíveis via
# `opencode auth login` ao provider opencode sem subscription paga).
# Anti-pattern observado May 2026: tentar `--yes` (não existe) → erro
# `unknown option '--yes'` mata o install antes do binário baixar.
if ! command -v omo >/dev/null 2>&1 && ! command -v oh-my-opencode >/dev/null 2>&1; then
  echo "==> Installing oh-my-openagent (omo + plugin wiring) via bunx..."
  bunx oh-my-openagent install --no-tui \
    --claude=no \
    --gemini=no \
    --copilot=no \
    --openai=no \
    --opencode-go=no \
    --opencode-zen=no \
    --zai-coding-plan=no \
    --kimi-for-coding=no \
    --vercel-ai-gateway=no \
    --skip-auth
  # FAIL-FAST: verifica que o binário ficou no PATH antes de seguir.
  # Sem isso, falha silenciosa do installer (e.g. flag renomeada,
  # rate-limit do registry npm, schema change) só seria detectada pelo
  # usuário rodando `omo agents list` depois.
  # NOTA naming (docs/reference/configuration.md, May 2026): "the
  # published package and CLI binary remain `oh-my-opencode`. OpenCode
  # plugin registration prefers `oh-my-openagent`". Por isso testamos
  # AMBOS os nomes — o binário real pode ser `oh-my-opencode` e não
  # existir alias `omo` por default.
  command -v omo >/dev/null 2>&1 || command -v oh-my-opencode >/dev/null 2>&1 || {
    echo "[postCreate] ERROR: 'bunx oh-my-openagent install' rodou mas nem omo nem oh-my-opencode estão no PATH."
    echo "  Cheque:"
    echo "    ls -la ~/.bun/bin/ | grep -i 'oh-my\|omo'"
    echo "    echo \$PATH (deve conter /home/vscode/.bun/bin)"
    echo "  Rode manual no terminal pra ver o erro real:"
    echo "    bunx oh-my-openagent install --no-tui --claude=no --gemini=no --copilot=no --openai=no --opencode-go=no --opencode-zen=no --zai-coding-plan=no --kimi-for-coding=no --vercel-ai-gateway=no --skip-auth"
    exit 1
  }
else
  echo "==> omo (ou oh-my-opencode) already present."
fi

# ─── 2.5. Verifica omo plugin wiring no opencode.json ─────────────
# O installer oficial do bloco 2 (curl pipe) já grava o plugin entry em
# ~/.config/opencode/opencode.json (bind RW persiste entre rebuilds).
# Este bloco só VERIFICA — não tenta re-wirar (evita race-condition
# com installer mais novo que use schema diferente). Se o installer
# falhou parcialmente (binário OK mas plugin não wirado), avisa pra
# debug manual antes de o usuário descobrir só na primeira invocação
# de @atlas/@hephaestus/@sisyphus dentro do opencode.
OPENCODE_JSON="$HOME/.config/opencode/opencode.json"
if [ ! -f "$OPENCODE_JSON" ] || ! grep -q 'oh-my-open' "$OPENCODE_JSON" 2>/dev/null; then
  echo "[postCreate] WARN: $OPENCODE_JSON sem plugin entry 'oh-my-open*'."
  echo "  Agentes @atlas/@hephaestus/@sisyphus/@oracle/@prometheus/@metis/@librarian"
  echo "  vão falhar com 'unknown agent' nos commands /spec-check, /test-first,"
  echo "  /implement, /review."
  echo "  Fix manual: bunx oh-my-openagent install (responda as 9 perguntas)."
else
  echo "==> omo plugin wired in $OPENCODE_JSON"
fi

# ─── 2.6. TUI plugin wiring em tui.json (separado do server plugin) ──
# omo tem DOIS plugins: o server plugin em opencode.json (wirado pelo
# installer no bloco 2) E o TUI plugin "oh-my-openagent/tui" em
# ~/.config/opencode/tui.json (Roles · Models sidebar + TUI-only
# commands). O installer com `--no-tui` PULA o wiring do tui.json
# (confirmado May 2026: `bunx oh-my-opencode doctor` reporta "TUI
# plugin entry missing from tui.json" depois do install non-interactive).
# Sem isso, a sidebar de Roles não aparece no opencode TUI — commands
# do Step 4 (/spec-check, /test-first, etc.) continuam funcionando via
# CLI, mas a UX TUI fica mutilada.
# Fix idempotente via jq: cria tui.json se não existe, senão adiciona
# o entry preservando outros plugins (unique evita duplicar em re-runs).
TUI_JSON="$HOME/.config/opencode/tui.json"
if [ ! -f "$TUI_JSON" ]; then
  echo '{"plugin": ["oh-my-openagent/tui"]}' > "$TUI_JSON"
  echo "==> Created $TUI_JSON with oh-my-openagent/tui plugin"
elif ! grep -q 'oh-my-openagent/tui' "$TUI_JSON" 2>/dev/null; then
  if command -v jq >/dev/null 2>&1; then
    jq '.plugin = ((.plugin // []) + ["oh-my-openagent/tui"] | unique)' \
      "$TUI_JSON" > "$TUI_JSON.tmp" && mv "$TUI_JSON.tmp" "$TUI_JSON"
    echo "==> Added oh-my-openagent/tui to $TUI_JSON"
  else
    echo "[postCreate] WARN: jq não disponível pra editar $TUI_JSON. Adicione manual:"
    echo "  echo '{\"plugin\": [\"oh-my-openagent/tui\"]}' > $TUI_JSON"
  fi
else
  echo "==> TUI plugin already wired in $TUI_JSON"
fi

# ─── 2.7. Pyright LSP server (Python code intel pros agentes omo) ──
# `bunx oh-my-opencode doctor` reporta "No LSP servers detected" se
# nenhum LSP estiver no PATH. opencode usa LSP pra rename, references,
# diagnostics inline e go-to-definition — essencial pros agentes
# @hephaestus (implementer) e @oracle (reviewer) navegarem o código
# durante /implement e /review do Step 4. Pyright é o LSP Python
# oficial da Microsoft (mesmo backbone do Pylance que o devcontainer.json
# já carrega na extensão VS Code). Instala global via bun (mais rápido
# e leve que `uv tool install`).
if ! command -v pyright >/dev/null 2>&1; then
  echo "==> Installing pyright LSP via bun..."
  bun install -g pyright
else
  echo "==> pyright already present."
fi

# ─── 3. Copia configs do opencode pro ~/.config (cp -n, no-clobber) ──
# NOTA Step 6: o formato canônico do opencode 1.15+ é .json (não .jsonc),
# e o `bunx oh-my-openagent install` (bloco 2.5) já cria/mantém o
# ~/.config/opencode/opencode.json moderno com mcp + plugin. O ideal é
# o Step 6 do scaffolding criar .opencode-config/opencode.json (sem c)
# e MERGEAR keys de projeto no global em vez de manter um .jsonc paralelo
# (que vira candidato a zumbi futuro — vide bloco 0.4). Por enquanto,
# cp -n preserva qualquer .jsonc legítimo de projetos antigos sem
# sobrescrever; o bloco 0.4 aborta automaticamente se as chaves
# voltarem a ser schema v1.
mkdir -p "$HOME/.config/opencode"
if [ -f ".opencode-config/opencode.jsonc" ]; then
  cp -n ".opencode-config/opencode.jsonc" "$HOME/.config/opencode/opencode.jsonc" || true
fi
if [ -f ".opencode-config/oh-my-opencode.jsonc" ]; then
  cp -n ".opencode-config/oh-my-opencode.jsonc" "$HOME/.config/opencode/oh-my-opencode.jsonc" || true
fi

# ─── 4. uv sync (se pyproject.toml já existir) ───────────────────────
if [ -f "pyproject.toml" ]; then
  echo "==> uv sync..."
  uv sync --all-extras
  if [ -f ".pre-commit-config.yaml" ]; then
    uv run pre-commit install || echo "[warn] pre-commit install falhou; rode manual depois"
  fi
fi

# ─── 5. Versões ──────────────────────────────────────────────────────
echo ""
echo "=== Versions ==="
echo "python:   $(python --version 2>&1 || echo NOT FOUND)"
echo "uv:       $(uv --version 2>&1 || echo NOT FOUND)"
echo "bun:      $(bun --version 2>&1 || echo NOT FOUND)"
echo "opencode: $(opencode --version 2>&1 || echo NOT FOUND)"
echo "omo:      $(omo --version 2>&1 || oh-my-opencode --version 2>&1 || echo NOT FOUND)"
echo "rg:       $(rg --version 2>&1 | head -1 || echo NOT FOUND)"
echo "pyright:  $(pyright --version 2>&1 || echo NOT FOUND)"
echo "gh:       $(gh --version 2>&1 | head -1 || echo NOT FOUND)"
echo "git:      $(git --version 2>&1 || echo NOT FOUND)"
echo "================"
echo ""

# ─── 6. Próximos passos (banner) ─────────────────────────────────────
cat <<'BANNER'
────────────────────────────────────────────────────────────────────
  ✅ Devcontainer pronto.

  Próximos passos:

  1. Autentique o GitHub CLI (uma vez, pro git-keeper criar PRs):
         gh auth login
     Escolha: GitHub.com → HTTPS → Login with web browser.
     Browser do host abre; cole o código de 8 chars.

  2. Autentique o opencode (uma vez):
         opencode auth login
     Escolha pelo menos um provider FREE (opencode, openrouter).

  3. (Opcional) Autentique o Notion MCP via OAuth (Step 10):
         opencode mcp auth notion
     Token persiste em ~/.local/share/opencode/auth.json (bind RW).

  4. Sanity-check final antes do handoff:
         bunx oh-my-opencode doctor
     Esperado: 0 issues (ou só warnings informativos).

  5. Cole o handoff prompt do Step 9 dentro de `opencode` pra rodar
     o backlog de specs autonomamente.
────────────────────────────────────────────────────────────────────
BANNER
