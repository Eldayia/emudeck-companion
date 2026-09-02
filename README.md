# EmuDeck Companion

EmuDeck Companion is a Decky Loader plugin that exposes context-aware controls
for the emulator currently launched by EmuDeck, ES-DE, or Steam ROM Manager.
It does not replace EmuDeck and does not require EmuDecky.

## Current status

Version 0.2 includes:

- automatic process and ROM detection through `/proc`;
- data-driven profiles for Cemu, DuckStation, PCSX2, Dolphin, and RetroArch;
- contextual QAM sections (unsupported actions are hidden);
- save/load, slots, pause, fast-forward, display, disc, menu, screenshot, and
  graceful quit actions where the profile supports them;
- EmuDeck/ES-DE discovery and diagnostics;
- internal, `/run/media`, and home-mounted EmuDeck storage discovery;
- cached ES-DE `gamelist.xml` metadata and scraped cover lookup;
- `.m3u` multidisc discovery with disc actions hidden for single-disc games;
- 250 ms protection against accidental double actions;
- controller-friendly Decky controls with no pointer-only interaction.

Hotkeys are delivered through Steam's controller-keyboard API after the QAM is
closed, so no extra input package or root access is required. `ydotool`, Wayland
`wtype`, and targeted X11 `xdotool` remain available as backend fallbacks. The
bundled hotkeys are baseline defaults and must be validated against the
actual EmuDeck/emulator configuration before a store release. Steam Deck Gaming
Mode hardware tests are still required.

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

Settings use Decky's current `DECKY_PLUGIN_SETTINGS_DIR`. No system files or
EmuDeck configuration are modified.

## Architecture

- `src/`: Decky React/TypeScript QAM interface and RPC bindings.
- `companion_session.py`: active session lifecycle.
- `companion_process_detection.py`: emulator process matching.
- `companion_game_detection.py`: ROM extraction and display name fallback.
- `companion_esde.py`: cached gamelist metadata and scraped-media lookup.
- `companion_multidisc.py`: M3U playlist discovery.
- `companion_action_engine.py`: capability checks, debounce, and action dispatch.
- `companion_input_backends.py`: virtual input abstraction.
- `defaults/emulators/`: independently versioned emulator profiles, copied to
  `emulators/` by the Decky release builder.
- `tests/`: platform-independent backend tests.

## Safety

The plugin never displays an action absent from the active profile. Normal quit
uses the emulator's graceful shortcut. The MVP intentionally does not expose
force-kill, savestate deletion, remote profile updates, or any root installer.
