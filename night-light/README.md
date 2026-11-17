# night-light

A [pop-launcher](https://github.com/pop-os/launcher) plugin to toggle GNOME Night Light and set its warmth.

Press **Super**, type `night`, pick an entry, hit **Enter**. The list stays short: the warmth presets are only offered while the screen is
really warm (GNOME's `NightLightActive`), otherwise only *Turn on/off* and one more entry are shown:

- **Turn Night Light on/off** (the entry shows the current state, schedule and temperature)
- **Warm now** switches to a manual schedule that starts immediately and ends at the configured end time (default 6:00), so you see the effect during the day
- **Low / Medium / High** set the warmth (3200 / 2700 / 2200 K) and switch Night Light on
- **Use sunset to sunrise** appears after *Warm now* (or any custom schedule) and switches back to the automatic schedule

Note: with the automatic schedule the screen only turns warm after sunset, so toggling during the day
has no visible effect until then. Use *Warm now* for an immediate effect.

## Requirements

GNOME with `gsettings` (schema `org.gnome.settings-daemon.plugins.color`). Not available on COSMIC.
