#!/usr/bin/env bash
# Symlink every plugin folder into pop-launcher's user plugin dir (edits apply immediately).
# Usage: ./install.sh [plugin ...]   (default: all)
set -euo pipefail
src="$(cd "$(dirname "$0")" && pwd)"
dst="$HOME/.local/share/pop-launcher/plugins"
mkdir -p "$dst"
plugins=("$@")
# a plugin is any subfolder that contains a plugin.ron
[ ${#plugins[@]} -eq 0 ] && for d in "$src"/*/; do [ -f "$d/plugin.ron" ] && plugins+=("$(basename "$d")"); done
for p in "${plugins[@]}"; do
  ln -sfn "$src/$p" "$dst/$p"
  echo "Installed: $dst/$p -> $src/$p"
done
pkill pop-launcher 2>/dev/null || true   # launcher respawns on next Super press
