#!/usr/bin/env bash
# Run display-fix automatically after login (systemd user timer).
#   ./install-autostart.sh            install + enable
#   ./install-autostart.sh --remove   disable + remove
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
unitdir="$HOME/.config/systemd/user"

if [ "${1:-}" = "--remove" ]; then
  systemctl --user disable --now display-fix.timer 2>/dev/null || true
  rm -f "$unitdir/display-fix.service" "$unitdir/display-fix.timer"
  systemctl --user daemon-reload
  echo "Removed display-fix autostart"; exit 0
fi

mkdir -p "$unitdir"
# units cannot use relative paths, so substitute the repo location into the templates
for u in display-fix.service display-fix.timer; do
  sed "s|@REPO@|$repo|g" "$(dirname "$0")/systemd/$u" > "$unitdir/$u"
done
systemctl --user daemon-reload
# --now: also start counting immediately, so the first run happens ~10 s from now
systemctl --user enable --now display-fix.timer
echo "Enabled. Next runs:"; systemctl --user list-timers display-fix.timer --no-pager
