# Compact actions (0.17.0)

Enable **Show Settings → Compact actions** to shorten the QAM action list.
The setting is off by default, including when upgrading from an older version.
It is stored in Companion's own settings and never changes emulator bindings.

The compact panel shows up to four actions:

- Usable favorites first, in saved order. Game favorites take precedence over
  emulator favorites as in the full view. No automatic filler is added to a
  nonempty list of usable favorites.
- If no usable favorites remain, common actions are chosen from the current
  session: save, load, pause, menu, fast-forward, display controls, then quit.
  Other supported actions fill any remaining places.
- Actions hidden for this game or unavailable in the current backend remain
  excluded. Stale favorites cannot enable them.
- When save/load is visible and both slot controls are supported, the slot
  indicator and previous/next buttons remain directly accessible. RetroArch's
  native slot value stays explicitly labeled as an estimate.

**Show All Actions** reveals the existing full sections, including RetroArch
menu navigation, disc controls and recent savestates. **Show Quick Actions**
returns to the compact panel. The toggle remains above the full sections so it
does not require scrolling to the bottom to collapse them. Expansion resets for
a new detected session or when changing the compact setting. Documents, hotkey
reference, settings and diagnostics remain accessible in either view.

## Validation

`pnpm test` runs backend tests and frontend selection tests; `pnpm test:frontend`
runs only the latter. TypeScript checks and the frontend bundle build are also
required. The selection tests run without Steam/Decky and do not prove gamepad
focus behavior on a Steam Deck.

On the Deck: enable Compact actions, check the default selection, set two
favorites, and verify their order. Expand/collapse with the controller, try the
RetroArch menu from the full view, then hide one action for the current game and
verify it disappears in both views. Relaunch the plugin to check persistence.
