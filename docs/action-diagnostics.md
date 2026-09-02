# Action diagnostics (0.19.0)

Diagnostics now shows the installed package version and the five most recent
action attempts. **Copy Diagnostics** and **Export Diagnostics** include up to
30 attempts, newest first, including attempts from earlier detected games during
the same plugin run. Use **Refresh Diagnostics** to update this view without
recreating the session; **Refresh Detection** still performs the full rescan.

Each entry includes its request ID, request timestamp, emulator, game title, PID,
and (since 0.20.0) the session ID observed by the backend,
action, dispatch method, status and a bounded message. The history is held only
in memory, capped at 30 entries and reset when the plugin restarts. It is not a
permanent play history and is not sent anywhere. An exported JSON file remains
on disk until removed or replaced by another export. Review diagnostics before
sharing: the complete report includes game names, ROM/config paths and system
information. The journal itself does not add ROM paths or emulator config data.

## Status meanings

- `pending` / **Waiting for keyboard**: the backend prepared a shortcut; the
  frontend has not yet reported the complete key press/release operation.
- `sent` / **Sent (unconfirmed)**: native dispatch succeeded, or the frontend
  reported that Steam keyboard API calls completed without throwing. This does
  not prove that the emulator acted on the input or saved a file.
- `failed` / **Failed**: the action was rejected, backend dispatch failed, or a
  keyboard press/release raised an error. Some input may already have been sent.
- `unknown` / **Delivery unknown**: no frontend report arrived within 15 seconds.
  This is not proof of failure. The status expires on the next history read/write.
- `completed` / **Local selection updated**: an operation that only changes
  Companion's local selection, not an emulator command.

Keyboard delivery is correlated by request ID. Old, expired, duplicate and
non-keyboard reports are ignored. A delayed report for an earlier action cannot
overwrite the latest action summary. Reporting never executes or retries an
action. If the reporting RPC fails after a shortcut was sent, the frontend keeps
that separate from an input error; history eventually says delivery unknown.

Keyboard shortcuts close the QAM and wait 200 ms. Since 0.20.0, the frontend then
rechecks the session before sending keys; a changed or unreadable session fails
without sending the chord. The chord is held for 100 ms and released in reverse
order. On a press or release error,
the frontend attempts release for every attempted key and reports the error.
The key mappings, emulator bindings and RetroArch UDP command transport are
unchanged. Slot and toggle indicators remain estimates, not synchronized state.

## Validation

Automated tests cover the bounded journal, pending/sent/failed/unknown states,
duplicate and stale reports, local/native actions, old-game correlation, export
integration and frontend press/release failure cleanup. Frontend tests simulate
the keyboard API; they do not replace Steam Deck testing.

On the Deck, check that Plugin version is 0.19.0. Trigger one previously working
RetroArch action, then open Diagnostics: it should show `retroarch_udp` and Sent
(unconfirmed). For another emulator that uses keyboard shortcuts, test a harmless
action such as pause twice and check `steam_input`. Refresh Diagnostics and export
the report if an action fails. No need to deliberately break a working setup.
