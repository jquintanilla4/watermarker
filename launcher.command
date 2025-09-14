#!/usr/bin/env bash
# macOS double-clickable wrapper to run the main launcher.
# Opens in Terminal when double-clicked.

set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/launcher.sh"

