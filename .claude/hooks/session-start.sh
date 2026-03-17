#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo '{"async": true, "asyncTimeout": 600000}'

# Add nix to PATH
export PATH="/nix/var/nix/profiles/default/bin:$PATH"

# Capture the nix develop environment and persist it for the session
echo "Loading nix develop environment from flake..."
nix develop "$CLAUDE_PROJECT_DIR" --command env \
  | grep -E '^[A-Za-z_][A-Za-z0-9_]*=' \
  | while IFS= read -r line; do
      var="${line%%=*}"
      val="${line#*=}"
      printf 'export %s=%q\n' "$var" "$val"
    done >> "$CLAUDE_ENV_FILE"

echo "Nix develop environment ready."
