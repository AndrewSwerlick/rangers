#!/bin/bash
set -euo pipefail

# Only run in remote Claude Code environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "Installing LaTeX and Pandoc dependencies for TTRPG Rulebook..."

# Install LaTeX (texlive) and Pandoc if not already present
PACKAGES_TO_INSTALL=()

if ! command -v pdflatex &>/dev/null; then
  PACKAGES_TO_INSTALL+=(texlive-latex-base texlive-latex-extra)
fi

if ! command -v latexmk &>/dev/null; then
  PACKAGES_TO_INSTALL+=(latexmk)
fi

if ! command -v pandoc &>/dev/null; then
  PACKAGES_TO_INSTALL+=(pandoc)
fi

if [ ${#PACKAGES_TO_INSTALL[@]} -gt 0 ]; then
  apt-get install -y "${PACKAGES_TO_INSTALL[@]}"
  echo "Installed: ${PACKAGES_TO_INSTALL[*]}"
else
  echo "All dependencies already installed."
fi

echo "Dependencies ready."
echo "  pdflatex: $(pdflatex --version | head -1)"
echo "  latexmk:  $(latexmk --version | head -1)"
echo "  pandoc:   $(pandoc --version | head -1)"
