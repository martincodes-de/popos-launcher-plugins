#!/usr/bin/env python3
"""pop-launcher plugin: open a folder from ~/projects in PhpStorm.

Protocol: pop-launcher sends one JSON request per line on stdin and expects
JSON responses, one per line, on stdout.
"""
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.expanduser("~/projects")
# the launcher's PATH may not contain /snap/bin, so fall back to the absolute path
# without a filter only show the N most recently used projects; typing a filter searches all
RECENT_LIMIT = 7
PHPSTORM = shutil.which("phpstorm") or "/snap/bin/phpstorm"


def send(msg):
    # flush every line, otherwise the launcher never sees the answer
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def last_used(path):
    # PhpStorm rewrites workspace.xml whenever a project is used, so it is a
    # better "recently opened" signal than the folder's own mtime
    ws = os.path.join(path, ".idea", "workspace.xml")
    try:
        return os.path.getmtime(ws if os.path.exists(ws) else path)
    except OSError:
        return 0


def projects():
    try:
        entries = [e for e in os.scandir(ROOT) if e.is_dir() and not e.name.startswith(".")]
    except OSError:
        return []
    return sorted(entries, key=lambda e: last_used(e.path), reverse=True)


def search(query):
    parts = query.split(maxsplit=1)
    needle = parts[1].lower() if len(parts) > 1 else ""
    # Activate(id) is an index into this list, so keep it
    shown = [e for e in projects() if needle in e.name.lower()]
    if not needle:
        shown = shown[:RECENT_LIMIT]
    for i, e in enumerate(shown):
        send({
            "Append": {
                "id": i,
                "name": e.name,
                "description": e.path.replace(os.path.expanduser("~"), "~"),
                "icon": {"Name": "folder"},
            }
        })
    send("Finished")
    return shown


def activate(entry):
    # detach fully: the IDE must outlive the plugin and not block on its output
    subprocess.Popen(
        [PHPSTORM, entry.path],
        start_new_session=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


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
                activate(shown[req["Activate"]])
                send("Close")
        except Exception:
            send("Finished")


if __name__ == "__main__":
    main()
