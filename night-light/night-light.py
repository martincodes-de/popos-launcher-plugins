#!/usr/bin/env python3
"""pop-launcher plugin: toggle GNOME Night Light and choose its colour temperature.

Protocol: pop-launcher sends one JSON request per line on stdin and expects
JSON responses, one per line, on stdout.
"""
import json
import os
import subprocess
import sys
import time

SCHEMA = "org.gnome.settings-daemon.plugins.color"
# (label, kelvin): lower = warmer. GNOME allows roughly 1700-4700 K.
PRESETS = [("Very warm", 1700), ("Warm", 2700)]


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


def state():
    enabled = get("night-light-enabled") == "true"
    auto = get("night-light-schedule-automatic") == "true"
    kelvin = int(get("night-light-temperature").split()[-1])   # "uint32 2211" -> 2211
    return enabled, auto, kelvin


def hhmm(hours):
    """GNOME stores times as float hours: 6.5 -> '6:30'."""
    h = int(hours); m = round((hours - h) * 60)
    return f"{h}:{m:02d}"


def entries():
    """[(label, description, action)], action is a list of (key, value) to set."""
    enabled, auto, kelvin = state()
    schedule = "sunset to sunrise" if auto else "custom schedule"
    toggle = ("Turn Night Light off" if enabled else "Turn Night Light on",
              f"Currently {'on' if enabled else 'off'}, {schedule}, {kelvin} K",
              [("night-light-enabled", not enabled)])
    # "warm now": sunset-based schedules do nothing during the day, so switch to a manual
    # schedule that starts one minute ago and ends at the configured end time (usually
    # the next morning). A start later than the end is read by GNOME as "overnight".
    now = time.localtime()
    start = max(0.0, round(now.tm_hour + now.tm_min / 60 - 1 / 60, 2))
    end = float(get("night-light-schedule-to"))
    warm_now = ("Warm now", f"Until {hhmm(end)}, replaces the sunset schedule",
                [("night-light-schedule-automatic", False),
                 ("night-light-schedule-from", start),
                 ("night-light-enabled", True)])
    # the first entries are what is shown without a filter, the rest only when you type
    items = [toggle, warm_now]
    presets = []
    for label, k in PRESETS:
        mark = " · current" if k == kelvin else ""
        # choosing a warmth also switches the feature on, otherwise nothing would change
        presets.append((f"{label} ({k} K)", "Set colour temperature" + mark,
                      [("night-light-temperature", k), ("night-light-enabled", True)]))
    back = ("Use sunset to sunrise", "Switch back to the automatic schedule",
            [("night-light-schedule-automatic", True)])
    # after "Warm now" the way back is more useful than offering "Warm now" again
    if not auto:
        # order matters: the first entries (see default_count) are what you see without a filter
        return [toggle, back] + presets + [warm_now]
    return items + presets


def default_count():
    """How many entries to show without a filter: toggle + one more, and the warmth presets
    only while Night Light is on (they change nothing visible while it is off)."""
    enabled, _, _ = state()
    return 2 + (len(PRESETS) if enabled else 0)


def search(query):
    parts = query.split(maxsplit=1)
    needle = parts[1].lower() if len(parts) > 1 else ""
    items = entries()
    # with a filter search everything (e.g. "night warm" also finds presets while it is off)
    shown = [e for e in items if needle in e[0].lower()] if needle else items[:default_count()]
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
                for key, value in shown[req["Activate"]][2]:
                    put(key, value)
                send("Close")
        except Exception:
            send("Finished")


if __name__ == "__main__":
    main()
