"""Known-good default keyboard shortcuts for popular Windows DAWs.

Each preset pre-fills the settings form; the buyer can still edit any
field afterward, so a preset is a convenience, not a lock. Only DAWs
with a verified, sourced default keymap belong here - a wrong preset
is worse than no preset for a buyer who won't know how to debug it.

Sourcing notes (checked against official manuals/keyboard shortcut
references, not general impression):
- Most DAWs below use ONE toggle key for Play/Stop by default (Ableton,
  Pro Tools, Reaper, Cakewalk, FL Studio all toggle on Space). That's
  reflected here by key_play and key_stop being identical - tapping
  either sends the same keystroke, which works for the normal
  record -> stop -> play-back flow but will toggle the wrong direction
  if pressed out of sequence (e.g. Stop tapped while already stopped
  starts playback instead).
- Studio One is the exception: it has genuinely separate, non-toggle
  Play/Stop defaults.
- Fender Studio Pro ships a CUSTOMIZED keymap that differs from vanilla
  PreSonus Studio One (confirmed by hands-on hardware testing) - kept
  as a separate preset rather than assumed identical.
- key_beginning ("go to start of project") is only filled in where
  hands-on verified - Reaper's default is W. Left empty elsewhere
  rather than guessed; an empty key_beginning hides the button.
"""

PRESETS = {
    "fender_studio_pro": {
        "label": "Fender Studio Pro",
        "window_title_hint": "studio",
        "key_record": ["ctrl", "r"],
        "key_play": ["space"],
        "key_stop": ["num0"],
        "key_beginning": [],
    },
    "studio_one": {
        "label": "PreSonus Studio One",
        "window_title_hint": "studio one",
        "key_record": ["multiply"],
        "key_play": ["enter"],
        "key_stop": ["num0"],
        "key_beginning": [],
    },
    "ableton_live": {
        "label": "Ableton Live",
        "window_title_hint": "ableton",
        "key_record": ["f9"],
        "key_play": ["space"],
        "key_stop": ["space"],
        "key_beginning": [],
    },
    "pro_tools": {
        "label": "Pro Tools",
        "window_title_hint": "pro tools",
        "key_record": ["ctrl", "space"],
        "key_play": ["space"],
        "key_stop": ["space"],
        "key_beginning": [],
    },
    "reaper": {
        "label": "Reaper",
        "window_title_hint": "reaper",
        "key_record": ["ctrl", "r"],
        "key_play": ["space"],
        "key_stop": ["space"],
        "key_beginning": ["w"],
    },
    "cakewalk": {
        "label": "Cakewalk by BandLab",
        "window_title_hint": "cakewalk",
        "key_record": ["r"],
        "key_play": ["space"],
        "key_stop": ["space"],
        "key_beginning": [],
    },
    "fl_studio": {
        "label": "FL Studio",
        "window_title_hint": "fl studio",
        "key_record": ["r"],
        "key_play": ["space"],
        "key_stop": ["space"],
        "key_beginning": [],
    },
}
