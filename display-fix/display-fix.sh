#!/bin/bash
LOGDIR="${XDG_STATE_HOME:-$HOME/.local/state}/display-fix"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/display-$(date +%Y%m%d_%H%M%S).txt"
# keep only the 20 newest logs
ls -1t "$LOGDIR"/display-*.txt 2>/dev/null | tail -n +21 | xargs -r rm --
# the launcher has no terminal: only wait for Enter when run interactively
pause() { [ -t 0 ] && read; return 0; }

log() { echo "$1" | tee -a "$LOG"; }

log "=== DISPLAY FIX $(date) ==="
log ""

# Alle verbundenen Ports erkennen
log "--- Erkannte Displays ---"
CONNECTED=$(xrandr --query | grep " connected" | awk '{print $1}')
ACTIVE=$(xrandr --query | grep " connected" | grep -v "connected (" | awk '{print $1, $3}')
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
done < <(xrandr --query | grep " connected")

if [ -z "$INACTIVE" ]; then
    log "Alle verbundenen Displays sind aktiv. Nichts zu tun."
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
done < <(xrandr --query | grep " connected")

log "Platziere neue Displays ab X=$RIGHTMOST"
log ""

FIXED=0
for PORT in $INACTIVE; do
    log "Aktiviere $PORT bei ${RIGHTMOST}+0..."

    # Bevorzugte Auflösung aus EDID lesen (erste Zeile mit *)
    PREF_RES=$(xrandr --query | awk "/^$PORT /{found=1} found && /\*/{print \$1; exit}")
    # Fallback: erste verfügbare Auflösung
    [ -z "$PREF_RES" ] && PREF_RES=$(xrandr --query | awk "/^$PORT /{found=1; next} found && /^\s+[0-9]/{print \$1; exit}")

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
        ACTIVE_PORTS=$(xrandr --query | grep " connected" | grep -E "[0-9]+x[0-9]+\+[0-9]+\+[0-9]+" | awk '{print $1}')

        CMD="xrandr"
        X_POS=0
        for AP in $ACTIVE_PORTS; do
            RES=$(xrandr --query | awk "/^$AP /{found=1} found && /\*/{print \$1; exit}")
            [ -z "$RES" ] && RES=$(xrandr --query | awk "/^$AP /{found=1; next} found && /^\s+[0-9]/{print \$1; exit}")
            CMD="$CMD --output $AP --mode $RES --pos ${X_POS}x0"
            W=$(echo "$RES" | cut -dx -f1)
            X_POS=$((X_POS + W))
        done
        RES2=$(xrandr --query | awk "/^$PORT /{found=1; next} found && /^\s+[0-9]/{print \$1; exit}")
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

log "=== Ergebnis: $FIXED Display(s) aktiviert ==="
log "Log gespeichert: $LOG"
echo ""
echo "Drücke Enter zum Beenden..."
pause
