# display-fix

A [pop-launcher](https://github.com/pop-os/launcher) plugin that activates monitors which are
connected but inactive (X11 / `xrandr`), e.g. after unplugging and re-plugging a dock or HDMI cable.

Press **Super**, type `display` (or `monitor`), hit **Enter**. The entry shows which outputs are inactive.
The built-in laptop screen (`eDP`/`LVDS`) is always moved to the leftmost position afterwards; the order of other screens and vertical offsets stay as they are.
New displays are placed to the right of the active ones using their preferred resolution; if that fails, all
outputs are reconfigured in one `xrandr` call as a workaround for pipeline conflicts. A notification shows the result.

Further entries appear when an external monitor is connected: **Laptop screen only**, **External monitor only**,
**Extend to the right** and **Mirror displays** (at the largest resolution both screens support).
`display mirror` filters the list.

Logs go to `~/.local/state/display-fix/` (newest 20 are kept). `display-fix.sh` also works standalone in a terminal.

## Run automatically after login

```sh
display-fix/install-autostart.sh            # enable
display-fix/install-autostart.sh --remove   # disable
```

Installs a systemd user timer that runs the fix 10 seconds, 2 minutes and 10 minutes after the graphical
session starts. The later runs catch docks and adapters that are detected late. Check with
`systemctl --user list-timers display-fix.timer`.

## Requirements

`xrandr` (X11 session only, not Wayland) and `gdbus` for the notification.
