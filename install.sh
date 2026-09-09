#!/usr/bin/env bash
# Instala agent-kit no PATH (macOS, Linux, WSL)
set -euo pipefail

if [ "${1:-}" = "--remote" ]; then
  command -v git >/dev/null 2>&1 || { echo "Git não encontrado" >&2; exit 1; }
  REMOTE_ROOT="${AGENT_KIT_HOME:-$HOME/.local/share/agent-kit}"
  REPO_URL="${AGENT_KIT_REPO:-https://github.com/Nicolas25vlad/agent-kit.git}"
  REF="${AGENT_KIT_REF:-main}"

  if [ -d "$REMOTE_ROOT/.git" ]; then
    git -C "$REMOTE_ROOT" fetch --quiet origin "$REF"
    git -C "$REMOTE_ROOT" checkout --quiet --force "$REF"
    git -C "$REMOTE_ROOT" reset --quiet --hard "origin/$REF"
  else
    mkdir -p "$(dirname "$REMOTE_ROOT")"
    git clone --quiet --branch "$REF" "$REPO_URL" "$REMOTE_ROOT"
  fi

  exec bash "$REMOTE_ROOT/install.sh"
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_NAME="agent"
INSTALL_DIR="${AGENT_KIT_BIN:-$HOME/.local/bin}"

mkdir -p "$INSTALL_DIR"

# Wrapper que aponta para este repo (atualiza com git pull, sem reinstall)
WRAPPER="$INSTALL_DIR/$BIN_NAME"
cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
exec "$ROOT/bin/agent" "\$@"
EOF
chmod +x "$WRAPPER"
chmod +x "$ROOT/bin/agent"

# PATH hint
case ":$PATH:" in
  *":$INSTALL_DIR:"*) ;;
  *)
    SHELL_RC=""
    if [ -n "${ZSH_VERSION:-}" ] || [ "$(basename "${SHELL:-}")" = "zsh" ]; then
      SHELL_RC="$HOME/.zshrc"
    elif [ -n "${BASH_VERSION:-}" ] || [ "$(basename "${SHELL:-}")" = "bash" ]; then
      SHELL_RC="$HOME/.bashrc"
    fi
    if [ -n "$SHELL_RC" ] && ! grep -q 'agent-kit' "$SHELL_RC" 2>/dev/null; then
      echo "" >> "$SHELL_RC"
      echo "# agent-kit" >> "$SHELL_RC"
      echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$SHELL_RC"
      echo "Adicionado $INSTALL_DIR ao PATH em $SHELL_RC"
    fi
    ;;
esac

echo "agent-kit instalado: $WRAPPER"
echo "Teste: agent repo info"
