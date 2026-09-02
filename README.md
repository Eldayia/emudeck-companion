# EmuDeck Companion

EmuDeck Companion is a Decky Loader plugin that exposes context-aware controls
for the emulator currently launched by EmuDeck, ES-DE, or Steam ROM Manager.
It does not replace EmuDeck and does not require EmuDecky.

## Current status

Version 0.4 includes:

- automatic process and ROM detection through `/proc`;
- data-driven profiles for Cemu, DuckStation, PCSX2, Dolphin, RetroArch,
  PPSSPP, melonDS, Azahar, and Flycast;
- contextual QAM sections (unsupported actions are hidden);
- save/load, slots, pause, fast-forward, display, disc, menu, screenshot, and
  graceful quit actions where the profile supports them;
- EmuDeck/ES-DE discovery and diagnostics;
- internal, `/run/media`, and home-mounted EmuDeck storage discovery;
- cached ES-DE `gamelist.xml` metadata and scraped cover lookup;
- `.m3u` multidisc discovery with disc actions hidden for single-disc games;
- active-ROM savestate discovery with slot and modification time where filenames
  can be matched safely;
- 250 ms protection against accidental double actions;
- controller-friendly Decky controls with no pointer-only interaction.

Hotkeys are delivered through Steam's controller-keyboard API after the QAM is
closed, so no extra input package or root access is required. `ydotool`, Wayland
`wtype`, and targeted X11 `xdotool` remain available as backend fallbacks. The
bundled hotkeys are baseline defaults and must be validated against the
actual EmuDeck/emulator configuration before a store release. Steam Deck Gaming
Mode hardware tests are still required.

RetroArch's native menu is intentionally not exposed: a clean EmuDeck profile
disables its keyboard menu binding and Decky cannot safely inject the configured
gamepad chord into the active controller. Supported RetroArch operations remain
available directly as controller-friendly QAM actions.

PPSSPP and melonDS shortcuts mirror EmuDeck's shipped emulator configuration.
PPSSPP's Quick Menu remains available because its native interface supports
controller navigation. melonDS exposes direct slots 1–8, its toggle fast-forward
binding, pause, screen swap, lid, fullscreen, and graceful quit controls.

Azahar exposes EmuDeck's native newest/oldest savestate actions, speed, pause,
screen layout, rotation, fullscreen, screenshot, and quit shortcuts. Flycast
exposes its Quick Menu everywhere; save/load and fast-forward are limited to
Dreamcast ROMs because those keys have different arcade meanings on clean
Naomi and Atomiswave configurations.

## Development

Requirements: Node.js 16.14+, pnpm 9, and Python 3.10+.

```sh
pnpm install
pnpm run typecheck
pnpm run build
python -m unittest discover -s tests -v
```

For Decky developer installation, build the frontend and copy the plugin folder
to `~/homebrew/plugins/EmuDeck-Companion`. Decky loads `main.py`; the built
frontend must be present as `dist/index.js`.

The prebuilt `dist/index.js` is committed so a Steam Deck checkout can be
updated without installing Node.js or pnpm:

```sh
git pull --ff-only origin main
sudo systemctl restart plugin_loader
```

Settings use Decky's current `DECKY_PLUGIN_SETTINGS_DIR`. No system files or
EmuDeck configuration are modified.

## Architecture

- `src/`: Decky React/TypeScript QAM interface and RPC bindings.
- `companion_session.py`: active session lifecycle.
- `companion_process_detection.py`: emulator process matching.
- `companion_game_detection.py`: ROM extraction and display name fallback.
- `companion_esde.py`: cached gamelist metadata and scraped-media lookup.
- `companion_multidisc.py`: M3U playlist discovery.
- `companion_savestates.py`: conservative per-ROM savestate inventory.
- `companion_action_engine.py`: capability checks, debounce, and action dispatch.
- `companion_input_backends.py`: virtual input abstraction.
- `defaults/emulators/`: independently versioned emulator profiles, copied to
  `emulators/` by the Decky release builder.
- `tests/`: platform-independent backend tests.

## Safety

The plugin never displays an action absent from the active profile. Normal quit
uses the emulator's graceful shortcut. The MVP intentionally does not expose
force-kill, savestate deletion, remote profile updates, or any root installer.
