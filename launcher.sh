#!/usr/bin/env bash

# A friendly launcher for non-technical users.
# - Ensures uv is installed
# - Creates a local .venv in this repo
# - Activates it and installs requirements
# - Runs video_watermarker.py

set -euo pipefail

# Determine project root (directory of this script)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Watermarker Launcher ==="

# Ensure common install locations are on PATH so a freshly-installed uv can be found
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$HOME/bin:$PATH"

have_cmd() { command -v "$1" >/dev/null 2>&1; }

install_uv_if_needed() {
  if have_cmd uv; then
    return 0
  fi

  echo "uv not found. Downloading and installing uv..."
  if have_cmd curl; then
    # Official install script from Astral
    if curl -fsSL https://astral.sh/uv/install.sh | sh; then
      # Refresh command hash and PATH in case uv was placed in ~/.local/bin
      hash -r || true
      export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$HOME/bin:$PATH"
    else
      echo "\nFailed to install uv automatically."
      echo "Please install uv manually from https://docs.astral.sh/uv/getting-started/ and re-run this script."
      exit 1
    fi
  else
    echo "curl is required to install uv automatically. Please install curl and re-run."
    exit 1
  fi

  if ! have_cmd uv; then
    echo "uv seems not available on PATH after installation. Try opening a new terminal and re-running."
    exit 1
  fi
}

create_or_activate_venv() {
  # Create the virtual environment in .venv if it does not exist
  if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Creating project virtual environment (.venv) with uv..."
    uv venv "$SCRIPT_DIR/.venv"
  fi

  # Activate the environment
  if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "$SCRIPT_DIR/.venv/bin/activate"
  else
    echo "Could not find activation script at .venv/bin/activate"
    exit 1
  fi
}

deps_installed() {
  # Try importing required packages; if it fails we consider deps missing
  python - <<'PY'
try:
    import cv2  # opencv-python
    import PIL  # Pillow
    import numpy  # numpy
    import inquirer  # inquirer
except Exception:
    raise SystemExit(1)
else:
    raise SystemExit(0)
PY
}

install_deps_if_needed() {
  if deps_installed; then
    return 0
  fi

  if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "Installing Python dependencies with uv (from requirements.txt)..."
    uv pip install -r "$SCRIPT_DIR/requirements.txt"
  else
    if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
      echo "Installing Python dependencies with uv (from pyproject.toml)..."
      uv sync
    else
      echo "No requirements.txt or pyproject.toml found; continuing without dependency install."
    fi
  fi
}

run_app() {
  echo "\nStarting Video Watermarker..."
  python "$SCRIPT_DIR/video_watermarker.py"
}

# Main flow
install_uv_if_needed
create_or_activate_venv
install_deps_if_needed
run_app

# Optional pause when launched via double-click on macOS Finder
case "${TERM_PROGRAM-}${TERM-}" in
  Apple_Terminal*|vscode*|iTerm.app*|xterm*) ;; # likely interactive terminal session
  *)
    # If we can't confidently detect a typical interactive terminal, offer a pause.
    # This keeps the window open for users who double-click the script.
    read -r -p $'\nPress Enter to close...' _ || true
    ;;
esac

