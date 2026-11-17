# audio-switch

A [pop-launcher](https://github.com/pop-os/launcher) plugin to switch the audio output
from the Super-key launcher on Pop!_OS.

Press **Super**, type `audio`, pick a device, hit **Enter**. `audio` lists outputs and microphones together;
running streams move to the new device too. Type `audio usb` to filter by device name.

Shortcuts: `out` (or `sound`) shows only outputs, `mic` (or `input`) only microphones.

## Requirements

`python3` and `pactl` (PulseAudio or PipeWire with pulse compatibility).
