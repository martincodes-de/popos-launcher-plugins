# night-light

A [pop-launcher](https://github.com/pop-os/launcher) plugin to make the screen warm and back to normal
(GNOME Night Light).

The default is GNOME's **sunset-to-sunrise schedule**. This plugin only adds a temporary override.

Press **Super**, type `night`, hit **Enter**:

- **Warm on** (shown while the screen is normal): warm right now until the next sunrise (from GNOME's
  location, fallback 6:00). A one-shot systemd timer then restores the sunset schedule.
- **Warm off** (shown while the screen is warm): back to normal colours and the sunset schedule.
  If it is night, it only skips tonight (GNOME's "disabled until tomorrow").
- **Low / Medium / High** (shown while the screen is warm): warmth 3200 / 2700 / 2200 K.

"Warm" means GNOME's real state (`NightLightActive`), not just the on/off setting.

## Requirements

GNOME with `gsettings`, `gdbus` and `systemd --user`. Not available on COSMIC.
If the session ends before the restore timer fires, the schedule stays manual until you pick **Warm off**.
