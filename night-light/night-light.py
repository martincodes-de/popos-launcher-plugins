#!/usr/bin/env python3
"""pop-launcher plugin: switch the screen warm / back to normal (GNOME Night Light).

The default is GNOME's sunset-to-sunrise schedule. "Warm on" is only a temporary override that
a transient systemd timer undoes at the configured end time; "Warm off" returns to the default.
While the screen is warm, three warmth steps are offered.

Protocol: pop-launcher sends one JSON request per line on stdin and expects
JSON responses, one per line, on stdout.
"""
import json
import os
import subprocess
import sys
import time

SCHEMA = "org.gnome.settings-daemon.plugins.color"
# (label, kelvin): lower = warmer. GNOME allows roughly 1700-4700 K. 3700 K felt like
# nothing and 1700 K is too extreme, so the steps cover 3200-2200 K.
PRESETS = [("Low", 3200), ("Medium", 2700), ("High", 2200)]


def send(msg):
    # flush every line, otherwise the launcher never sees the answer
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def get(key):
    return subprocess.run(["gsettings", "get", SCHEMA, key],
                          capture_output=True, text=True, check=True).stdout.strip()


def put(key, value):
    # NIGHT_DRY_RUN=1 prints instead of changing the screen (used for testing)
    cmd = ["gsettings", "set", SCHEMA, key, str(value).lower() if isinstance(value, bool) else str(value)]
    if os.environ.get("NIGHT_DRY_RUN"):
        print(" ".join(cmd), file=sys.stderr)
        return
    subprocess.run(cmd, check=True)


COLOR_DBUS = ["--session", "--dest", "org.gnome.SettingsDaemon.Color",
              "--object-path", "/org/gnome/SettingsDaemon/Color"]
RESTORE_UNIT = "night-light-restore"


def run(cmd):
    # NIGHT_DRY_RUN=1 prints instead of changing the screen (used for testing)
    if os.environ.get("NIGHT_DRY_RUN"):
        print(" ".join(cmd), file=sys.stderr)
        return
    subprocess.run(cmd, capture_output=True)


def cancel_restore():
    run(["systemctl", "--user", "stop", f"{RESTORE_UNIT}.timer"])


def schedule_restore(end_hours):
    """One-shot transient timer: back to the sunset schedule at the end of the override.
    (A manual schedule would otherwise repeat every day from the time of the override.)
    If the session ends before that, the schedule stays manual until "Warm off"."""
    cancel_restore()
    now = time.time()
    t = time.localtime(now)
    end = time.mktime((t.tm_year, t.tm_mon, t.tm_mday, int(end_hours),
                       round((end_hours % 1) * 60), 0, 0, 0, -1))
    if end <= now:
        end += 86400   # the end time already passed today, so it means tomorrow
    when = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end))
    run(["systemd-run", "--user", f"--unit={RESTORE_UNIT}", "--collect", f"--on-calendar={when}",
         "gsettings", "set", SCHEMA, "night-light-schedule-automatic", "true"])


def off_tonight():
    """After returning to the default it may still be night: then GNOME warms the screen
    again at once, so also use its own "disabled until tomorrow" switch."""
    if not os.environ.get("NIGHT_DRY_RUN"):
        time.sleep(0.6)             # give the settings daemon a moment to apply the change
        if not active():
            return
    run(["gdbus", "call", *COLOR_DBUS, "--method", "org.freedesktop.DBus.Properties.Set",
         "org.gnome.SettingsDaemon.Color", "DisabledUntilTomorrow", "<true>"])


def apply(actions):
    for a in actions:
        if a[0] == "restore":
            schedule_restore(a[1])
        elif a[0] == "cancel":
            cancel_restore()
        elif a[0] == "off_tonight":
            off_tonight()
        else:
            put(*a)


def active():
    """True while the screen is really tinted. "Enabled" only means the feature is on: with a
    sunset schedule it is enabled all day but warm only at night. GNOME exposes the real
    state on D-Bus; if that fails we fall back to "enabled"."""
    try:
        out = subprocess.run(
            ["gdbus", "call", "--session", "--dest", "org.gnome.SettingsDaemon.Color",
             "--object-path", "/org/gnome/SettingsDaemon/Color",
             "--method", "org.freedesktop.DBus.Properties.Get",
             "org.gnome.SettingsDaemon.Color", "NightLightActive"],
            capture_output=True, text=True, check=True).stdout
        return "true" in out
    except Exception:
        return get("night-light-enabled") == "true"


def hhmm(hours):
    """GNOME stores times as float hours: 6.5 -> '6:30'."""
    h = int(hours); m = round((hours - h) * 60)
    return f"{h}:{m:02d}"


def entries():
    """[(label, description, actions)]; actions are (key, value) pairs or special tuples."""
    kelvin = int(get("night-light-temperature").split()[-1])   # "uint32 2211" -> 2211
    if active():
        # back to the default (sunset schedule); if it is night right now, also skip tonight
        items = [("Warm off", f"Back to normal colours (now {kelvin} K)",
                  [("cancel",), ("night-light-schedule-automatic", True),
                   ("night-light-enabled", True), ("off_tonight",)])]
        for label, k in PRESETS:
            mark = " \u00b7 current" if k == kelvin else ""
            # the step only sets the warmth: the screen is already warm, nothing else changes
            items.append((label, f"Warmth {k} K" + mark, [("night-light-temperature", k)]))
        return items
    # Not warm right now. The sunset schedule would do nothing during the day, so override it
    # with a manual schedule that started one minute ago and ends at the configured end time.
    # A start later than the end is read by GNOME as "overnight".
    now = time.localtime()
    start = max(0.0, round(now.tm_hour + now.tm_min / 60 - 1 / 60, 2))
    end = float(get("night-light-schedule-to"))
    return [("Warm on", f"Warm now until {hhmm(end)}, then back to sunset schedule",
             [("night-light-schedule-automatic", False), ("night-light-schedule-from", start),
              ("night-light-enabled", True), ("restore", end)])]


def search(query):
    parts = query.split(maxsplit=1)
    needle = parts[1].lower() if len(parts) > 1 else ""
    shown = [e for e in entries() if needle in e[0].lower()]
    for i, (label, desc, _) in enumerate(shown):
        send({"Append": {"id": i, "name": label, "description": desc,
                         "icon": {"Name": "night-light-symbolic"}}})
    send("Finished")
    return shown


def main():
    shown = []  # Activate(id) is an index into the list of the last search
    for line in sys.stdin:
        try:
            req = json.loads(line)
            if req == "Exit":
                break
            if isinstance(req, dict) and "Search" in req:
                shown = search(req["Search"])
            elif isinstance(req, dict) and "Activate" in req:
                send("Close")   # close the launcher first, the change can take a moment
                apply(shown[req["Activate"]][2])
        except Exception:
            send("Finished")


if __name__ == "__main__":
    main()
