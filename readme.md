# MOTHER 3 to MIDI (WIP)

Converts MOTHER 3 MIDI rips into files conforming to the Roland General Standard (GS).

You need Python.

## Usage
0. Make sure you have installed Python and the [Mido](https://pypi.org/project/mido/) module
1. ~~Obtain the [MOTHER 3 Ultimate Music Rip](https://forum.starmen.net/forum/Games/Mother3/MOTHER-3-Ultimate-Music-Rip) (down as of 9/29/25)~~
2. ~~Unpack it and move the `OSV` folder next to `fixosv.py`~~
3. Execute the script and watch the debug waterfall
4. Enjoy the music!

This script was originally created to target Microsoft GS Wavetable Synth, due to the game soundbank's shared usage of the Roland SC-55 (technically 88Pro.)

## Available CLI options:
- `--defer-drums`: Enables drum channel allocation
  - Channel doesn't toggle drum mode, but messages are instead redirected to one of the allocated drum channels, while in drum mode
- `--instant-cut`: Enables an MSGS-specific hack for cutting notes off instantly 
- `--skip-replace`: Skips instrument replacements 
- `--skip-tweaks`: Skips instrument tweaks


## Tested target synths:
- Microsoft GS Wavetable Synth
  - `--defer-drums` must be used, otherwise notes will cut out when switching to drum mode
  - `--instant-cut` can be used if you want
- SpessaSynth
  - `--defer-drums` is not needed, since this synth seamlessly toggles to/from drum mode
  - `--instant-cut` doesn't work well with this, but you can achieve a similar effect by enabling Black MIDI Mode (`B` key or toggle it in `Config > Black MIDI mode`)

Most instruments have already been replaced, but some don't have the best fit, and some chords are missing.