# RetroArch keyboard hotkey configuration (0.16.0)

For EmuDeck setups with keyboard bindings set to `nul`, see
[native commands and explicit activation](retroarch-native-commands.md). A verified
native endpoint takes priority over the keyboard path described below, including
menu control. Only the explicit setup button writes `network_cmd_enable`; the
keyboard resolver itself remains read-only.

RetroArch and FinalBurn Neo running in RetroArch now resolve keyboard shortcuts
from configuration files. All reads are local and read-only: Companion does not
change EmuDeck settings, controller bindings or emulator files.

## Configuration selection

- Flatpak: `~/.var/app/org.libretro.RetroArch/config/retroarch/retroarch.cfg`,
  respecting the running process's absolute `XDG_CONFIG_HOME`.
- Native: `$XDG_CONFIG_HOME/retroarch/retroarch.cfg`, then
  `~/.config/retroarch/retroarch.cfg`, `~/.retroarch.cfg`, then the process's
  `/etc/retroarch.cfg` when accessible through `/proc`.
- Explicit `-c` / `--config` takes precedence. Relative command-line paths are
  resolved against the emulator's working directory, not Decky's.
- `#include` is expanded at its position. The first assignment wins within a
  file/include chain. `--appendconfig` files override the base in order; `|`
  separates multiple files. The last occurrence of the CLI option is used.
- For supported standard cores, automatic overrides are then merged in order:
  core, ROM directory, game. A later file overrides earlier settings without
  discarding unrelated bindings. `auto_overrides_enable = "false"` disables this.

Parsing is cached by file path, modification time and size. Included files are
checked independently. Reads are limited to eight files per resolution and one
MiB per file, with cycle detection. Only relevant hotkey settings and include
paths are retained; account tokens and unrelated configuration are not exported.

## Automatic overrides

The initial supported core binaries are `mupen64plus_next_libretro`,
`snes9x_libretro` and `fbneo_libretro`. Their standard internal names are
`Mupen64Plus-Next`, `Snes9x` and `FinalBurn Neo`. Renamed/custom binaries and FBNeo
subset builds are not covered. Names are matched exactly, not guessed from
directory contents or display labels.

Given `rgui_config_directory = "/path/config"`, the selected paths are:

1. `/path/config/<core>/<core>.cfg`
2. `/path/config/<core>/<ROM-parent-directory>.cfg`
3. `/path/config/<core>/<ROM-basename-without-extension>.cfg`

The directory comes from the global/CLI settings, and stays fixed while loading
these layers. Explicit `default` or empty values use the main config's parent.
Relative paths use the emulator's working directory; `~/` uses its home.
If the directory setting is absent, Companion does not guess the build-specific
runtime default. Application-relative `:/` paths are not supported yet.

Diagnostics includes an override status (`applied`, `none`, `disabled`,
`not_resolved` or `unavailable`), the core/directory and each selected layer.
`not_resolved` retains the preceding global/CLI behavior and explains the missing
coverage; it does not mean the running emulator has no overrides. A selected but
unreadable/malformed override blocks mapped actions instead of silently ignoring
it. The existing aggregate file-count and include-cycle limits still apply.

## Shortcut behavior

- A configured supported key replaces the bundled action's shortcut.
- A keyboard `input_enable_hotkey` is prepended to the action key. `nul` means
  no keyboard enabler; a controller-only enabler is not injected as a keyboard key.
- When device merging is enabled without a usable keyboard enabler, actions are
  disabled conservatively: a controller enabler may be required.
- An action explicitly set to `nul`, an empty value or an unsupported key is
  disabled, never replaced with an assumed default. Right-side modifiers,
  punctuation and keypad keys are not yet supported.
- Missing action settings retain bundled defaults and identify them as such in
  Hotkeys. Disc selection requires explicit keyboard bindings.
- A missing default configuration reports `fallback`. A missing explicit config,
  unreadable file, malformed relevant setting, missing include or exceeded limit
  reports `unavailable` and disables mapped actions, including Quit.
- Rewind is hidden: RetroArch requires a held key, which Companion's brief key
  injection does not implement. Fast-forward uses the toggle binding, not hold.
- The RetroArch menu remains hidden because opening it from the virtual keyboard
  did not provide usable controller navigation in our prior Steam Deck tests.

## Scope

This resolves global, explicitly supplied configuration and supported automatic
overrides **on disk**, not the live emulator state. The core and ROM are derived
from launch arguments. Switching core/content inside RetroArch, manually loading
or unloading overrides, archived member paths (`archive#member`), unsaved changes,
Game Focus, controller autoconfiguration and core-specific feature restrictions
are not resolved. `configured` means the files were read,
not that every shortcut was validated against the running core. Slot and toggle
indicators remain estimates, not synchronized emulator state.

## Steam Deck validation

1. Update and start a RetroArch game through your usual launcher.
2. Check Diagnostics: hotkey status, selected path, additional files and disabled
   reasons. For a supported core, check the override status and listed layers.
   `none` is normal if no matching override files exist. The Hotkeys panel
   distinguishes disk bindings from defaults.
3. With your existing configuration, test pause/resume, screenshot, then save/load
   on a spare slot. No configuration changes are needed for this check.
4. If a shortcut is missing or incorrect, export diagnostics and mention the
   action and core used. Do not send the entire emulator configuration, which may
   contain account information.

## References

- [RetroArch CLI and config paths](https://docs.libretro.com/guides/cli-intro/)
- [RetroArch sample configuration and hold/toggle semantics](https://github.com/libretro/RetroArch/blob/master/retroarch.cfg)
- [Configuration precedence](https://github.com/libretro/RetroArch/blob/master/libretro-common/file/config_file.c)
- [Keyboard names](https://github.com/libretro/RetroArch/blob/master/input/input_keymaps.c)
- [Hotkey device gating](https://github.com/libretro/RetroArch/blob/master/input/input_driver.c)
- [Override hierarchy and names](https://docs.libretro.com/guides/overrides/)
- [Override selection implementation](https://github.com/libretro/RetroArch/blob/master/configuration.c)
- [Override directory fallback](https://github.com/libretro/RetroArch/blob/master/file_path_special.c)
- [Mupen64Plus-Next internal name](https://github.com/libretro/mupen64plus-libretro-nx/blob/develop/libretro/libretro.c)
- [Snes9x internal name](https://github.com/snes9xgit/snes9x/blob/master/libretro/libretro.cpp)
- [FBNeo standard core metadata](https://github.com/libretro/libretro-core-info/blob/master/fbneo_libretro.info)
