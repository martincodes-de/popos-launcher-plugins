#!/usr/bin/env python3
"""pop-launcher plugin: activate monitors that are connected but inactive (X11, xrandr).

Protocol: pop-launcher sends one JSON request per line on stdin and expects
JSON responses, one per line, on stdout.
"""
import json
import os
import re
import subprocess
import sys

SCRIPT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "display-fix.sh")
# an active output has a geometry like 1920x1080+0+0 after "connected"
GEOMETRY = re.compile(r"\d+x\d+\+\d+\+\d+")


def send(msg):
    # flush every line, otherwise the launcher never sees the answer
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def inactive_ports():
    out = subprocess.run(["xrandr", "--query"], capture_output=True, text=True, check=True).stdout
    return [l.split()[0] for l in out.splitlines()
            if " connected" in l and not GEOMETRY.search(l)]


def notify(title, body):
    # notify-send is not installed here; talk to the notification daemon directly
    subprocess.run(
        ["gdbus", "call", "--session", "--dest", "org.freedesktop.Notifications",
         "--object-path", "/org/freedesktop/Notifications",
         "--method", "org.freedesktop.Notifications.Notify",
         "Display Fix", "0", "video-display", title, body, "[]", "{}", "5000"],
        capture_output=True,
    )


def search():
    ports = inactive_ports()
    send({
        "Append": {
            "id": 0,
            "name": "Fix displays",
            "description": ("Inactive: " + ", ".join(ports)) if ports else "All connected displays are active",
            "icon": {"Name": "video-display"},
        }
    })
    send("Finished")


def activate():
    before = inactive_ports()
    subprocess.run([SCRIPT], stdin=subprocess.DEVNULL, capture_output=True)
    after = inactive_ports()
    if not before:
        notify("Display Fix", "Nothing to do: all connected displays are active.")
    elif after:
        notify("Display Fix", "Still inactive: " + ", ".join(after) + ". See ~/.local/state/display-fix/")
    else:
        notify("Display Fix", "Activated: " + ", ".join(before))


def main():
    for line in sys.stdin:
        try:
            req = json.loads(line)
            if req == "Exit":
                break
            if isinstance(req, dict) and "Search" in req:
                search()
            elif isinstance(req, dict) and "Activate" in req:
                send("Close")   # close the launcher first, the fix can take a moment
                activate()
        except Exception:
            send("Finished")


if __name__ == "__main__":
    main()
