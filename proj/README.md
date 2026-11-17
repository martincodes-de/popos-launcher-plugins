# proj-launcher

A [pop-launcher](https://github.com/pop-os/launcher) plugin to open projects from `~/projects` in PhpStorm.

Press **Super**, type `proj`, pick a folder, hit **Enter**. `proj ber` filters by name.
Without a filter only the 7 most recently used projects are shown (by `.idea/workspace.xml` mtime);
any filter text searches all folders. Change `RECENT_LIMIT` in `proj.py` to adjust.

## Requirements

`python3` and PhpStorm available as `phpstorm` (e.g. `/snap/bin/phpstorm`).
