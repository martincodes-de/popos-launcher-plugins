#!/usr/bin/env bash
# Installer for the pop-launcher plugins in this repo.
#
#   ./install.sh                 install all plugins
#   ./install.sh proj            install only the named plugin(s)
#   ./install.sh --uninstall     remove all (or the named) plugins again
#   ./install.sh --list          show available plugins
#
# Plugins are symlinked, not copied, so edits in this repo apply immediately.
set -euo pipefail

src="$(cd "$(dirname "$0")" && pwd)"
dst="${XDG_DATA_HOME:-$HOME/.local/share}/pop-launcher/plugins"

# a plugin is any subfolder that contains a plugin.ron
available=()
for d in "$src"/*/; do
  [ -f "$d/plugin.ron" ] && available+=("$(basename "$d")")
done

mode=install
case "${1:-}" in
  --uninstall) mode=uninstall; shift ;;
  --list)      printf '%s\n' "${available[@]}"; exit 0 ;;
  -h|--help)   sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
esac
plugins=("$@")
[ ${#plugins[@]} -eq 0 ] && plugins=("${available[@]}")

# validate names so a typo does not silently do nothing
for p in "${plugins[@]}"; do
  [[ " ${available[*]} " == *" $p "* ]] || { echo "Unknown plugin: $p (available: ${available[*]})" >&2; exit 1; }
done

check_deps() {
  local missing=0
  command -v pop-launcher >/dev/null || { echo "warning: pop-launcher not found (is this Pop!_OS?)" >&2; missing=1; }
  command -v python3 >/dev/null || { echo "error: python3 is required" >&2; exit 1; }
  for p in "${plugins[@]}"; do
    case "$p" in
      audio-switch) command -v pactl >/dev/null || { echo "warning: audio-switch needs pactl" >&2; missing=1; } ;;
      proj) command -v phpstorm >/dev/null || [ -x /snap/bin/phpstorm ] || { echo "warning: proj needs PhpStorm" >&2; missing=1; } ;;
    esac
  done
  return 0
}

if [ "$mode" = install ]; then
  check_deps
  mkdir -p "$dst"
  for p in "${plugins[@]}"; do
    chmod +x "$src/$p"/*.py 2>/dev/null || true   # plugin binaries must be executable
    ln -sfn "$src/$p" "$dst/$p"
    echo "Installed: $p"
  done
else
  for p in "${plugins[@]}"; do
    # only remove links that point into this repo, never foreign files
    if [ -L "$dst/$p" ] && [ "$(readlink "$dst/$p")" = "$src/$p" ]; then
      rm "$dst/$p"; echo "Removed: $p"
    else
      echo "Skipped: $p (not installed from this repo)"
    fi
  done
fi

# the launcher respawns on the next Super press and then picks up the changes
pkill pop-launcher 2>/dev/null || true
