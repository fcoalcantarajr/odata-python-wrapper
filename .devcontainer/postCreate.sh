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

if ! bunx --bun omo --version >/dev/null 2>&1; then
  echo "==> Installing oh-my-openagent (omo)..."
  bun install -g oh-my-openagent
fi

# ─── 3. Copia configs do opencode pro ~/.config (cp -n, no-clobber) ──
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
python --version || true
uv --version || true
bun --version || true
opencode --version || true
bunx --bun omo --version 2>/dev/null || echo "omo: NOT FOUND"
git --version || true
echo "================"
echo ""

# ─── 6. Próximos passos (banner) ─────────────────────────────────────
cat <<'BANNER'
────────────────────────────────────────────────────────────────────
  ✅ Devcontainer pronto.

  Próximos passos:

  1. Autentique o opencode (uma vez):
         opencode auth login
     Escolha pelo menos um provider FREE (opencode, openrouter).

  2. (Opcional) Autentique o Notion MCP via OAuth (Step 10):
         opencode mcp auth notion
     Token persiste em ~/.local/share/opencode/auth.json (bind RW).

  3. Cole o handoff prompt do Step 9 dentro de `opencode` pra rodar
     o backlog de specs autonomamente.
────────────────────────────────────────────────────────────────────
BANNER

# ─── 7. Step 6: copy opencode + omo configs to host-mounted volumes ──
OPENCODE_DIR="$HOME/.config/opencode"
OMO_DIR="$HOME/.config/oh-my-openagent"
mkdir -p "$OPENCODE_DIR" "$OMO_DIR"

for pair in \
  ".opencode-config/opencode.jsonc:$OPENCODE_DIR/opencode.jsonc" \
  ".opencode-config/oh-my-opencode.jsonc:$OMO_DIR/config.jsonc"; do
  src="${pair%%:*}"
  dst="${pair##*:}"
  if [[ -f "$dst" ]]; then
    cp "$dst" "${dst}.bak.$(date +%Y%m%d-%H%M%S)"
    echo "[postCreate] backed up existing $dst"
  fi
  cp "$src" "$dst"
  echo "[postCreate] installed $dst"
done

export OMO_DISABLE_POSTHOG=1
echo 'export OMO_DISABLE_POSTHOG=1' >> "$HOME/.bashrc"

# ─── 8. Step 10: ensure NOTION_TOKEN and NOTION_ROOT_PAGE_ID are set ──
if [[ -z "${NOTION_TOKEN:-}" ]]; then
  echo "[postCreate] WARN: NOTION_TOKEN não setado. notion-curator vai falhar até você preencher .env e rebuild."
fi
if [[ -z "${NOTION_ROOT_PAGE_ID:-}" ]]; then
  echo "[postCreate] WARN: NOTION_ROOT_PAGE_ID não setado. notion-curator vai usar default ruim."
fi

# Quick smoke test pro MCP server (não falha o build se der erro — só reporta).
if command -v npx >/dev/null 2>&1; then
  echo "[postCreate] testing notion MCP server availability..."
  npx -y @notionhq/notion-mcp-server@latest --help >/dev/null 2>&1 && \
    echo "[postCreate] notion-mcp-server ok" || \
    echo "[postCreate] WARN: notion-mcp-server não respondeu ao --help (verifique conexão npm)"
fi