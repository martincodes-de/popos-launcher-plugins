#!/usr/bin/env python3
"""pop-launcher plugin: switch the default audio output (output and microphone, PulseAudio/PipeWire).

Protocol: pop-launcher sends one JSON request per line on stdin and expects
JSON responses, one per line, on stdout.
"""
import json
import subprocess
import sys


def pactl(*args):
    return subprocess.run(
        ["pactl", *args], capture_output=True, text=True, check=True
    ).stdout


def send(msg):
    # flush every line, otherwise the launcher never sees the answer
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


# Each mode describes how to list, default and move devices.
# "move" re-routes already running streams (playback / recording) so the
# change takes effect immediately instead of only for new streams.
MODES = {
    "output": {"kind": "sinks", "streams": "sink-inputs", "move": "move-sink-input",
               "set": "set-default-sink", "get": "get-default-sink", "icon": "audio-speakers"},
    "input": {"kind": "sources", "streams": "source-outputs", "move": "move-source-output",
              "set": "set-default-source", "get": "get-default-source", "icon": "audio-input-microphone"},
}
TRIGGERS = {"audio": "output", "sound": "output", "out": "output",
            "mic": "input", "input": "input"}


def list_devices(mode):
    devices = json.loads(pactl("-f", "json", "list", mode["kind"]))
    if mode["kind"] == "sources":
        # hide "Monitor of ..." entries: they mirror outputs, they are not microphones
        devices = [d for d in devices if not d.get("monitor_source")]
    default = pactl(mode["get"]).strip()
    return devices, default


def search(query):
    # first word picks what to show: "audio" = outputs AND inputs (umbrella),
    # "out"/"sound" = outputs only, "mic"/"input" = inputs only
    parts = query.split(maxsplit=1)
    trigger = parts[0].lower()
    needle = parts[1].lower() if len(parts) > 1 else ""
    names = ["output", "input"] if trigger == "audio" else [TRIGGERS.get(trigger, "output")]
    # remember the visible order: Activate(id) is an index into this list,
    # so every entry carries its own mode (output vs input)
    shown = []
    for name in names:
        mode = MODES[name]
        devices, default = list_devices(mode)
        for d in devices:
            if needle in d["description"].lower():
                shown.append((mode, d))
                label = "Output" if name == "output" else "Input"
                send({
                    "Append": {
                        "id": len(shown) - 1,
                        "name": d["description"],
                        "description": label + (" \u00b7 active" if d["name"] == default else ""),
                        "icon": {"Name": mode["icon"]},
                    }
                })
    send("Finished")
    return shown


def activate(mode, device):
    pactl(mode["set"], device["name"])
    # also move running streams, otherwise apps keep the old device
    for line in pactl("list", "short", mode["streams"]).splitlines():
        stream_id = line.split("\t", 1)[0]
        subprocess.run(["pactl", mode["move"], stream_id, device["name"]])


def main():
    shown = []
    for line in sys.stdin:
        try:
            req = json.loads(line)
            if req == "Exit":
                break
            if isinstance(req, dict) and "Search" in req:
                shown = search(req["Search"])
            elif isinstance(req, dict) and "Activate" in req:
                activate(*shown[req["Activate"]])
                send("Close")
        except Exception:
            # never crash the plugin; just end the current search cleanly
            send("Finished")


if __name__ == "__main__":
    main()
