# RetroArch native commands (0.16.0)

Companion can use RetroArch's UDP command interface instead of simulated keyboard
input. This supports EmuDeck configurations with keyboard bindings set to `nul`
without changing those bindings or creating a virtual controller. No ES-DE custom
scripts are needed; the usual EmuDeck/Steam launcher can still be used.

## Enable explicitly

1. Close RetroArch completely (not just its menu or game content).
2. Open Companion → **Show Settings** → **RetroArch Native Commands**.
3. Read the security warning, choose **Enable Native Commands…**, then confirm.
4. Relaunch a RetroArch game normally. Open Diagnostics and refresh: native commands
   should show `ready`, the verified RetroArch version, and the localhost port.

Setup supports the standard Flatpak config at
`~/.var/app/org.libretro.RetroArch/config/retroarch/retroarch.cfg`. It changes only
`network_cmd_enable`, keeping keyboard/controller binds and the configured port.
If no port is configured, RetroArch's default is 55355. The setting is written
before includes so the first assignment takes precedence. A command-line appended
configuration can still override it; check Diagnostics if activation has no effect.
Custom/native configs are not automatically edited by this setup button.

A byte-for-byte backup is written before each change to Decky's plugin settings
directory, under `retroarch-backups/`, with Linux file permissions `0600`. The UI
and plugin log report its exact path. Backups may contain private emulator account
settings: do not upload them. The new config is atomically replaced, preserving its
owner and permission bits. A detected concurrent edit or failed backup aborts setup.
Normal startup/detection never edits emulator configuration.

To disable, close RetroArch, use **Disable Native Commands…**, confirm, and relaunch.
This sets the flag to false; it does not restore the entire old config or remove
backups. A full manual restore is possible from the reported backup, with RetroArch
closed, but would also discard configuration changes made since that backup.

## Network security

RetroArch's UDP command interface is unauthenticated and may listen on all network
interfaces, including the LAN. Enabling it is not a localhost-only server setting.
Other reachable hosts could send commands. Use a trusted network and disable it
when it is no longer needed. Companion does not change firewall rules.

Companion itself only sends to `127.0.0.1`. Before probing or dispatching, it checks
Linux `/proc` for one IPv4 UDP listener on the selected port, owned by the detected
RetroArch PID in the same network namespace. Shared ports, ownership ambiguity,
inaccessible process information, invalid ports and changed sockets fail closed.
This verifies the destination; it does not protect the receiver from other clients.

## Actions and limits

- Save/load state, previous/next slot, pause/resume, fast-forward toggle,
  screenshot, fullscreen, and quit use native commands.
- Open/close menu and direction/confirm/back buttons are available in Companion.
  These send menu commands rather than selecting a new input device. Physical
  controller navigation still depends on the emulator/Steam Input configuration.
- Multi-disc playlists also offer tray open/close and previous/next disc. Open
  the tray, change disc, then close the tray. Core support is still required.
- Rewind remains unavailable: its hold behavior is not implemented. This release
  does not advertise a one-frame rewind command as continuous rewind.
- Companion requires a live `VERSION` reply identifying RetroArch 1.19+ and a valid
  `GET_STATUS` reply. Version and status are rechecked before each action. Read-only
  discovery is cached briefly, but socket ownership is checked each time.
- Native control is independent of the known-core keyboard override resolver.
  It can work with other RetroArch cores; each core, achievements mode and runtime
  setting can still limit individual actions.
- State/button commands have no execution acknowledgement. The notification says
  **command sent, execution not confirmed**. A successful send is not proof of a
  saved file or a changed state. No mutating command is retried, and no keyboard
  fallback is sent after an uncertain native action.
- Slot/disc indicators are estimates; initial state and changes outside Companion
  are not synchronized. Confirm the actual save slot in RetroArch's OSD. Native
  pause/fast-forward buttons do not display an assumed ON state.
- If no live native interface validates, the existing read-only keyboard resolver
  remains in effect. Explicit `nul` bindings stay disabled, not replaced with
  invented keyboard defaults.

## Steam Deck test checklist

User-reported validation on 2026-09-02, version 0.16.0: **Save State**, **Load State**
and **opening the RetroArch menu** work. Menu navigation, pause/resume, slot changes,
fast-forward, screenshots and disc controls are not yet confirmed by that report.
The report does not establish compatibility with every core or controller.

Automated tests cover parsing, endpoint ownership, protocol validation, loopback
transport against a fake server, single-send/no-retry dispatch, UI typechecking,
settings integration, config preservation and backup/error paths. They do not
replace validation against the real Steam Deck and RetroArch build.

After activation, first check `ready` in Diagnostics, then try pause/resume and a
screenshot. Check the menu and navigation. Finally test save/load on a spare slot
after verifying its actual number in RetroArch. Test fast-forward and playlist
disc changes separately. Confirm your existing controller shortcuts still work.
If an action does nothing, export diagnostics and report the core, action, and
whether the emulator was in gameplay or its menu. Do not send the full config.

## References

- [Libretro Network Control Interface](https://docs.libretro.com/development/retroarch/network-control-interface/)
- [RetroArch 1.19.1 command definitions](https://github.com/libretro/RetroArch/blob/v1.19.1/command.h)
- [RetroArch network command implementation](https://github.com/libretro/RetroArch/blob/master/command.c)
