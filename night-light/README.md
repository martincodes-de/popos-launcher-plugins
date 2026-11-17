# night-light

A [pop-launcher](https://github.com/pop-os/launcher) plugin to toggle GNOME Night Light and set its warmth.

Press **Super**, type `night`, pick an entry, hit **Enter**:

- **Turn Night Light on/off** (the entry shows the current state, schedule and temperature)
- **Warm now** switches to a manual schedule that starts immediately and ends at the configured end time (default 6:00), so you see the effect during the day
- **Very warm / Warm / Mild** sets the colour temperature (1700 / 2700 / 3700 K) and switches Night Light on
- **Use sunset to sunrise** appears after *Warm now* (or any custom schedule) and switches back to the automatic schedule

Note: with the automatic schedule the screen only turns warm after sunset, so toggling during the day
has no visible effect until then. Use *Warm now* for an immediate effect.

## Requirements

GNOME with `gsettings` (schema `org.gnome.settings-daemon.plugins.color`). Not available on COSMIC.
