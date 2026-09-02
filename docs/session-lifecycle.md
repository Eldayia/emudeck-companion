# Session lifecycle (0.20.0)

Companion gives each detected session a unique ID. Normal polling preserves it
only while the PID, process start ticks, selected emulator profile and complete
launch arguments remain the same. Process start ticks distinguish a restarted
emulator from an older process whose PID has been reused. The process reader
checks these ticks before and after reading its command line.

A new session reloads ROM metadata, documents, savestate inventory and disc
information, and resets local slot/toggle estimates and action debounce state.
An observed exit followed by a relaunch also creates a new session. Normal
polling preserves local selections. **Refresh Detection** explicitly recreates
the session; **Refresh Diagnostics** does not force recreation.

## Stale action protection

The frontend sends its session ID with each action. The backend refreshes
detection and rejects requests for an old or missing session ID before dispatch.
For keyboard shortcuts, the frontend checks again after closing the QAM and
waiting 200 ms. If the session changed or cannot be read, no keys are sent.
Failures appear in the bounded action history; there is no automatic retry.

Update the frontend bundle and backend together, then restart Decky. An old
frontend without session IDs is deliberately rejected. If you see a session
changed/missing error after updating, reopen Companion and refresh detection.

This reduces stale-input mistakes but is not an atomic process-targeted input
guarantee: the emulator or focused window can change after the final check.
Steam keyboard dispatch still depends on focus, and UDP delivery still does
not prove execution. Session IDs and start ticks are visible in Diagnostics.

## Limits and optional ES-DE scripts

Changing a game or core inside an already-running emulator without changing its
launch arguments is not detected by this mechanism. Runtime slot/toggle state
is not synchronized with the emulator. Do not treat local indicators as proof
that an action occurred.

Version 0.20.0 does not install or require ES-DE custom scripts. Optional ES-DE
launch/exit hooks are a planned integration, not an available feature yet. The
project may use them even when users must explicitly enable custom scripts in
ES-DE. When implemented, the setup documentation must explain that activation,
the exact installed files and events, preservation/backup of existing scripts,
and how to disable and uninstall the integration. It must remain opt-in and
must not silently overwrite existing user scripts. Hooks will only help with
launches managed by ES-DE; they will not observe every in-emulator game change.

## Validation

Automated tests cover stable polling, PID reuse, profile/core/ROM argument
changes, exits, explicit refresh, state resets, malformed process snapshots,
per-session debounce, stale backend requests and frontend keyboard rechecks.
These tests do not replace Gaming Mode hardware validation.

On the Steam Deck:

1. Open a game and note its Session ID in Diagnostics. Refresh Diagnostics:
   the ID should stay stable while the process and launch arguments do.
2. Test an already-working action such as RetroArch Save, Load or Menu.
3. Quit the emulator normally, then launch another game. Confirm the title and
   session ID change, and that old game details/local toggles do not persist.
4. Relaunch the same game and confirm a fresh session ID. Export Diagnostics
   if an action is rejected unexpectedly; do not repeatedly retry a save/load
   whose execution is uncertain.
