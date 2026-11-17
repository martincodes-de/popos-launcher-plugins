# popos-launcher-plugins

Small [pop-launcher](https://github.com/pop-os/launcher) plugins for Pop!_OS (Super key launcher).

| Plugin | Trigger | What it does |
|---|---|---|
| [audio-switch](audio-switch/) | `audio`, `out`, `mic` | Switch audio output and microphone |
| [proj](proj/) | `proj` | Open a folder from `~/projects` in PhpStorm |

## Install

```sh
./install.sh            # all plugins
./install.sh proj       # just one
```

Symlinks each plugin folder to `~/.local/share/pop-launcher/plugins/`. No sudo needed.
