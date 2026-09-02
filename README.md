# EmuDeck Companion

EmuDeck Companion is a Decky Loader plugin that exposes context-aware controls
for the emulator currently launched by EmuDeck, ES-DE, or Steam ROM Manager.
It does not replace EmuDeck and does not require EmuDecky.

## Current status

Version 0.10.0 includes:

- automatic process and ROM detection through `/proc`;
- data-driven profiles for Cemu, DuckStation, PCSX2, Dolphin, RetroArch,
  PPSSPP, melonDS, Azahar, Flycast, MAME, FinalBurn Neo, RPCS3, Ryujinx,
  and xemu;
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
- persistent per-emulator favorites (up to four actions), display preferences,
  configurable detection interval, and optional success notifications.
- ES-DE manual discovery plus local per-game PDF, text, Markdown, and HTML
  documents served through a tokenized localhost URL and opened in Steam's
  controller-accessible browser.

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

MAME exposes only keyboard actions preserved by a clean EmuDeck configuration:
its controller-navigable menu, screenshot, fullscreen, and graceful exit.
Savestate, pause, and fast-forward buttons are intentionally hidden because
EmuDeck maps those MAME functions exclusively to controller chords. FinalBurn
Neo is detected from RetroArch's active core and keeps the proven RetroArch
action set while displaying the correct emulator and arcade platform.

RPCS3 exposes its native four savestate slots, pause, boost mode, fullscreen,
and screenshot shortcuts. For extracted disc games, Companion derives the game
name from the directory above `PS3_GAME` instead of displaying `EBOOT`.
Ryujinx follows EmuDeck's shipped F-key configuration for pause, UI/fullscreen,
screenshot, docked mode, mute, and stop. xemu sessions and Xbox ROMs are detected,
but action buttons stay hidden because a clean EmuDeck setup does not provide
reliable xemu keyboard shortcuts.

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
sudo systemctl stop plugin_loader
cd ~/homebrew/plugins/EmuDeck-Companion
git pull --ff-only origin main
sudo systemctl start plugin_loader
```

Stopping Decky before pulling prevents its development hot reload from racing
with a service restart while plugin files are changing.

Settings use Decky's current `DECKY_PLUGIN_SETTINGS_DIR`. No system files or
EmuDeck configuration are modified. Favorites and UI preferences are validated
before being written atomically to the plugin's `settings.json`.

## Architecture

- `src/`: Decky React/TypeScript QAM interface and RPC bindings.
- `companion_session.py`: active session lifecycle.
- `companion_process_detection.py`: emulator process matching.
- `companion_game_detection.py`: ROM extraction and display name fallback.
- `companion_esde.py`: cached gamelist metadata and scraped-media lookup.
- `companion_documents.py`: bounded per-game manual and document discovery.
- `companion_document_server.py`: localhost-only, tokenized document delivery.
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
