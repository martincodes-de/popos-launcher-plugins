#!/bin/bash
LOGDIR="${XDG_STATE_HOME:-$HOME/.local/state}/display-fix"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/display-$(date +%Y%m%d_%H%M%S).txt"
# keep only the 20 newest logs
ls -1t "$LOGDIR"/display-*.txt 2>/dev/null | tail -n +21 | xargs -r rm --
# the launcher has no terminal: only wait for Enter when run interactively
# test hook: XR_QUERY_FILE replaces the real xrandr output, XR_DRY_RUN only prints commands
xr_query() { if [ -n "${XR_QUERY_FILE:-}" ]; then cat "$XR_QUERY_FILE"; else xrandr --query; fi; }
xr_apply() { if [ -n "${XR_DRY_RUN:-}" ]; then echo "xrandr $*"; else xrandr "$@"; fi; }
pause() { [ -t 0 ] && read; return 0; }

log() { echo "$1" | tee -a "$LOG"; }

# --- Ordnung: internes Laptop-Display immer ganz links ---
# Reihenfolge der anderen Displays bleibt, vertikale Versätze (Y) bleiben erhalten.
normalize_order() {
    local args
    args=$(xr_query | awk '
        / connected/ && match($0, /[0-9]+x[0-9]+\+[0-9]+\+[0-9]+/) {
            g = substr($0, RSTART, RLENGTH); split(g, a, /[x+]/)
            n++; name[n]=$1; w[n]=a[1]; x[n]=a[3]; y[n]=a[4]
            if ($1 ~ /^(eDP|LVDS)/) int_i = n
        }
        END {
            if (!int_i) exit
            # internal already leftmost? then nothing to do
            for (i = 1; i <= n; i++) if (i != int_i && x[i] < x[int_i]) need = 1
            if (!need) exit
            printf "--output %s --pos 0x%s", name[int_i], y[int_i]
            pos = w[int_i]
            # others in their current left-to-right order
            for (k = 1; k < n; k++) {
                best = 0
                for (i = 1; i <= n; i++) if (i != int_i && !done[i] && (!best || x[i] < x[best])) best = i
                done[best] = 1
                printf " --output %s --pos %dx%s", name[best], pos, y[best]
                pos += w[best]
            }
        }')
    if [ -n "$args" ]; then
        log "--- Laptop-Display steht nicht links, sortiere neu ---"
        log "  xrandr $args"
        # shellcheck disable=SC2086
        xr_apply $args 2>>"$LOG" || log "  FEHLER: Neu-Sortierung fehlgeschlagen"
    fi
}

log "=== DISPLAY FIX $(date) ==="
log ""

# Alle verbundenen Ports erkennen
log "--- Erkannte Displays ---"
CONNECTED=$(xr_query | grep " connected" | awk '{print $1}')
ACTIVE=$(xr_query | grep " connected" | grep -v "connected (" | awk '{print $1, $3}')
log "$ACTIVE"
log ""

# Ports die verbunden aber NICHT aktiv sind (kein WxH+X+Y nach dem Namen)
INACTIVE=""
while IFS= read -r line; do
    PORT=$(echo "$line" | awk '{print $1}')
    # Aktiv = hat Auflösung in der Form 1920x1080+0+0
    if ! echo "$line" | grep -qE "[0-9]+x[0-9]+\+[0-9]+\+[0-9]+"; then
        INACTIVE="$INACTIVE $PORT"
    fi
done < <(xr_query | grep " connected")

if [ -z "$INACTIVE" ]; then
    log "Alle verbundenen Displays sind aktiv."
    normalize_order
    log "=== LOG: $LOG ==="
    echo "Alles OK! Drücke Enter..."
    pause
    exit 0
fi

log "--- Inaktive Displays gefunden: $INACTIVE ---"
log "Versuche zu aktivieren..."
log ""

# Rechteste X-Position ermitteln für Platzierung
RIGHTMOST=0
while IFS= read -r line; do
    # z.B. "1920x1080+1920+0" -> X-Offset + Breite
    GEOM=$(echo "$line" | grep -oE "[0-9]+x[0-9]+\+[0-9]+\+[0-9]+" | head -1)
    if [ -n "$GEOM" ]; then
        W=$(echo "$GEOM" | cut -dx -f1)
        X=$(echo "$GEOM" | cut -d+ -f2)
        END=$((X + W))
        [ "$END" -gt "$RIGHTMOST" ] && RIGHTMOST=$END
    fi
done < <(xr_query | grep " connected")

log "Platziere neue Displays ab X=$RIGHTMOST"
log ""

FIXED=0
for PORT in $INACTIVE; do
    log "Aktiviere $PORT bei ${RIGHTMOST}+0..."

    # Bevorzugte Auflösung aus EDID lesen (erste Zeile mit *)
    PREF_RES=$(xr_query | awk "/^$PORT /{found=1} found && /\*/{print \$1; exit}")
    # Fallback: erste verfügbare Auflösung
    [ -z "$PREF_RES" ] && PREF_RES=$(xr_query | awk "/^$PORT /{found=1; next} found && /^\s+[0-9]/{print \$1; exit}")

    if [ -z "$PREF_RES" ]; then
        log "  WARNUNG: Keine Auflösung für $PORT gefunden — überspringe"
        continue
    fi

    log "  Auflösung: $PREF_RES"

    if xrandr --output "$PORT" --mode "$PREF_RES" --pos "${RIGHTMOST}x0" 2>>"$LOG"; then
        log "  OK: $PORT aktiviert"
        W=$(echo "$PREF_RES" | cut -dx -f1)
        RIGHTMOST=$((RIGHTMOST + W))
        FIXED=$((FIXED + 1))
    else
        log "  FEHLER: $PORT konnte nicht aktiviert werden"
        log "  Versuch: Pipeline-Reset (alle neu konfigurieren)..."

        # Pipeline-Konflikt-Workaround: kurz deaktivieren und neu aktivieren
        ACTIVE_PORTS=$(xr_query | grep " connected" | grep -E "[0-9]+x[0-9]+\+[0-9]+\+[0-9]+" | awk '{print $1}')

        CMD="xrandr"
        X_POS=0
        for AP in $ACTIVE_PORTS; do
            RES=$(xr_query | awk "/^$AP /{found=1} found && /\*/{print \$1; exit}")
            [ -z "$RES" ] && RES=$(xr_query | awk "/^$AP /{found=1; next} found && /^\s+[0-9]/{print \$1; exit}")
            CMD="$CMD --output $AP --mode $RES --pos ${X_POS}x0"
            W=$(echo "$RES" | cut -dx -f1)
            X_POS=$((X_POS + W))
        done
        RES2=$(xr_query | awk "/^$PORT /{found=1; next} found && /^\s+[0-9]/{print \$1; exit}")
        CMD="$CMD --output $PORT --mode $RES2 --pos ${X_POS}x0"

        log "  Führe aus: $CMD"
        if eval "$CMD" 2>>"$LOG"; then
            log "  OK: Pipeline-Reset erfolgreich"
            FIXED=$((FIXED + 1))
        else
            log "  FEHLER: Auch Pipeline-Reset fehlgeschlagen — siehe Log"
        fi
    fi
    log ""
done

normalize_order
log "=== Ergebnis: $FIXED Display(s) aktiviert ==="
log "Log gespeichert: $LOG"
echo ""
echo "Drücke Enter zum Beenden..."
pause
