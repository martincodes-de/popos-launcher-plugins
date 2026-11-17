# display-fix

A [pop-launcher](https://github.com/pop-os/launcher) plugin that activates monitors which are
connected but inactive (X11 / `xrandr`), e.g. after unplugging and re-plugging a dock or HDMI cable.

Press **Super**, type `display` (or `monitor`), hit **Enter**. The entry shows which outputs are inactive.
New displays are placed to the right of the active ones using their preferred resolution; if that fails, all
outputs are reconfigured in one `xrandr` call as a workaround for pipeline conflicts. A notification shows the result.

Logs go to `~/.local/state/display-fix/` (newest 20 are kept). `display-fix.sh` also works standalone in a terminal.

## Requirements

`xrandr` (X11 session only, not Wayland) and `gdbus` for the notification.
