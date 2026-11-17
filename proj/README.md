# proj

A [pop-launcher](https://github.com/pop-os/launcher) plugin to open projects from `~/projects` in PhpStorm.

Press **Super**, type `proj`, pick a folder, hit **Enter**. `proj ber` filters by name.

Type `projc` instead to open a terminal in the project and start `claude --remote-control` there.

Without a filter only the 7 most recently used projects are shown (by `.idea/workspace.xml` mtime);
any filter text searches all folders. Change `RECENT_LIMIT` in `proj.py` to adjust.

## Requirements

`python3` and PhpStorm available as `phpstorm` (e.g. `/snap/bin/phpstorm`); for `projc` also `gnome-terminal` and the `claude` CLI.
