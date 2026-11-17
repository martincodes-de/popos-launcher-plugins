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


def xrandr_query():
    return subprocess.run(["xrandr", "--query"], capture_output=True, text=True, check=True).stdout


def outputs():
    """Parse xrandr into {name: {"active": bool, "modes": [(w, h), ...]}} for connected outputs."""
    result, cur = {}, None
    for line in xrandr_query().splitlines():
        if not line.startswith(" "):
            cur = None
            if " connected" in line:
                cur = line.split()[0]
                result[cur] = {"active": bool(GEOMETRY.search(line)), "modes": []}
        elif cur:
            m = re.match(r"\s+(\d+)x(\d+)", line)
            if m:
                result[cur]["modes"].append((int(m[1]), int(m[2])))
    return result


def inactive_ports():
    return [n for n, o in outputs().items() if not o["active"]]


def run_xrandr(args):
    # DISPLAY_FIX_DRY_RUN=1 prints the command instead of touching the screen (used for testing)
    cmd = ["xrandr", *args]
    if os.environ.get("DISPLAY_FIX_DRY_RUN"):
        return " ".join(cmd)
    subprocess.run(cmd, capture_output=True)
    return None


def presets():
    """Layout presets, only offered when an external monitor is connected.
    Returns [(label, description, xrandr_args)]."""
    outs = outputs()
    internal = next((n for n in outs if n.startswith(("eDP", "LVDS"))), None)
    externals = [n for n in outs if n != internal]
    if not internal or not externals:
        return []
    ext = externals[0]
    off = lambda names: [a for n in names for a in ("--output", n, "--off")]
    items = [
        ("Laptop screen only", "Turn all external monitors off",
         ["--output", internal, "--auto", "--primary", *off(externals)]),
        ("External monitor only", f"Use {ext}, turn {internal} off",
         ["--output", ext, "--auto", "--primary", "--output", internal, "--off"]),
        ("Extend to the right", f"{ext} right of {internal}",
         ["--output", internal, "--auto", "--pos", "0x0",
          "--output", ext, "--auto", "--right-of", internal, "--primary"]),
    ]
    # mirroring needs a mode both screens support, otherwise one image gets cropped/stretched
    common = set(outs[internal]["modes"]) & set(outs[ext]["modes"])
    if common:
        w, h = max(common, key=lambda m: m[0] * m[1])
        mode = f"{w}x{h}"
        items.append(("Mirror displays", f"Same image on both at {mode}",
                      ["--output", internal, "--mode", mode, "--pos", "0x0",
                       "--output", ext, "--mode", mode, "--same-as", internal]))
    return items


def notify(title, body):
    # notify-send is not installed here; talk to the notification daemon directly
    subprocess.run(
        ["gdbus", "call", "--session", "--dest", "org.freedesktop.Notifications",
         "--object-path", "/org/freedesktop/Notifications",
         "--method", "org.freedesktop.Notifications.Notify",
         "Display Fix", "0", "video-display", title, body, "[]", "{}", "5000"],
        capture_output=True,
    )


def entries():
    ports = inactive_ports()
    fix = ("Fix displays",
           ("Inactive: " + ", ".join(ports)) if ports else "All active, laptop screen is kept leftmost",
           None)  # None = run display-fix.sh
    # an inactive monitor is the likely reason for opening this, so put the fix first
    return [fix, *presets()]


def search(query):
    parts = query.split(maxsplit=1)
    needle = parts[1].lower() if len(parts) > 1 else ""
    shown = [e for e in entries() if needle in e[0].lower()]
    for i, (label, desc, _) in enumerate(shown):
        send({"Append": {"id": i, "name": label, "description": desc,
                         "icon": {"Name": "video-display"}}})
    send("Finished")
    return shown


def activate(entry):
    label, _, args = entry
    if args is not None:
        dry = run_xrandr(args)
        notify("Display Fix", dry or label)
        return
    before = inactive_ports()
    subprocess.run([SCRIPT], stdin=subprocess.DEVNULL, capture_output=True)
    after = inactive_ports()
    if not before:
        notify("Display Fix", "All displays active, order checked (laptop screen leftmost).")
    elif after:
        notify("Display Fix", "Still inactive: " + ", ".join(after) + ". See ~/.local/state/display-fix/")
    else:
        notify("Display Fix", "Activated: " + ", ".join(before))


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
                send("Close")   # close the launcher first, the fix can take a moment
                activate(shown[req["Activate"]])
        except Exception:
            send("Finished")


if __name__ == "__main__":
    main()
