# night-light

A [pop-launcher](https://github.com/pop-os/launcher) plugin to toggle GNOME Night Light and set its warmth.

Press **Super**, type `night`, pick an entry, hit **Enter**:

- **Turn Night Light on/off** (the entry shows the current state, schedule and temperature)
- **Very warm / Warm / Mild** sets the colour temperature (1700 / 2700 / 3700 K) and switches Night Light on
- **Use sunset to sunrise** appears only if a custom schedule is set

Note: with the automatic schedule the screen only turns warm after sunset, so toggling during the day
has no visible effect until then.

## Requirements

GNOME with `gsettings` (schema `org.gnome.settings-daemon.plugins.color`). Not available on COSMIC.
