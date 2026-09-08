#!/usr/bin/env bash
# Instala agent-kit no PATH (macOS, Linux, WSL)
set -euo pipefail

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
