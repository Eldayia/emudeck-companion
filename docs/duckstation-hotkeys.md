# DuckStation hotkey configuration (0.13.0)

The plugin reads DuckStation's global `[Hotkeys]` section without modifying any
emulator settings. This first implementation targets standard EmuDeck installs:

- AppImage/native: `$HOME/.local/share/duckstation/settings.ini`, respecting the
  running process's absolute `XDG_DATA_HOME` when available.
- Legacy Flatpak: `~/.var/app/org.duckstation.DuckStation/config/duckstation/settings.ini`,
  respecting the running process's absolute `XDG_CONFIG_HOME` when available.

The process environment is used only to locate settings; it is not exported in
diagnostics. The file is size-limited and parsed again only after its path, size
or modification time changes. Refreshing the same emulator session updates the
resolved shortcuts without resetting the plugin's selected slot.

## Resolution rules

- A supported keyboard binding replaces the bundled action's keys. Repeated INI
  entries are alternatives; the first complete supported keyboard chord wins.
- Letters, digits, F1–F12, common navigation keys and Ctrl/Alt/Shift combinations
  are supported. Mixed keyboard/controller chords are never partially injected.
- In an existing config, missing, empty, unsupported or controller-only bindings
  disable the corresponding action instead of sending an assumed default.
- If the file is absent, diagnostics report `fallback` and bundled shortcuts
  remain available, except fast-forward. An unreadable, malformed or oversized
  file reports `unavailable` and disables configuration-dependent actions.
- Fast-forward requires a keyboard binding for `ToggleFastForward`. `FastForward`
  (hold, usually Tab) is not treated as a toggle.
- Quit retains the plugin's native Alt+F4 shortcut; it is not mapped to DuckStation's
  PowerOff hotkey.

Diagnostics show the path, resolution status and reasons for disabled actions.
The Hotkeys panel identifies bindings read from DuckStation global settings.

## Scope and remaining limitations

This reads global settings **on disk**, not DuckStation's live input state.
Unsaved changes, game-specific input profiles, portable mode and custom settings
locations are not resolved. The plugin's slot/toggle indicators remain estimates;
actions made outside the plugin are not tracked. Other emulators still use their
existing profiles. No emulator configuration changes are required by this feature.

## Steam Deck check

1. Update the plugin, then launch a game in DuckStation using your normal EmuDeck setup.
2. In Diagnostics, check that the hotkey status is `configured` and the path points
   to your global settings file.
3. Compare the Hotkeys panel with DuckStation's global keyboard shortcuts. Try
   pause/resume and a screenshot first; use a spare slot to test save/load.
4. If an action is absent, check its disabled reason in Diagnostics. Fast-forward
   being absent is expected if only a hold or controller binding is configured.
5. Send the exported diagnostics if a supported global keyboard shortcut differs.
   There is no need to send the complete settings file (it can contain account data).

Automated coverage includes parsing, repeated bindings, unsupported chords,
fallbacks, cache invalidation, AppImage/Flatpak selection and same-PID refresh.
Actual Steam input injection still needs the hardware check above.

## Upstream references

- [EmuDeck DuckStation installation and migration paths](https://github.com/dragoonDorise/EmuDeck/blob/main/functions/EmuScripts/emuDeckDuckStation.sh)
- [DuckStation hotkey names and hold/toggle behavior](https://github.com/stenzek/duckstation/blob/master/src/core/hotkeys.cpp)
- [DuckStation input binding resolution](https://github.com/stenzek/duckstation/blob/master/src/util/input_manager.cpp)
- [DuckStation repeated INI entries](https://github.com/stenzek/duckstation/blob/master/src/util/ini_settings_interface.cpp)
