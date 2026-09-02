import type { EmulatorSession } from "./types";

const quickPriority = [
  "save_state", "load_state", "pause", "emulator_menu", "fast_forward",
  "swap_screen", "screen_layout", "fullscreen", "quit",
];

export function quickActions(session: EmulatorSession, favorites: string[]): string[] {
  // capabilities already excludes actions hidden by the user's per-game settings.
  const supported = (action: string) => session.capabilities.includes(action) && Boolean(session.actions[action]);
  const selected = [...new Set(favorites)].filter(supported).slice(0, 4);
  if (selected.length) return selected;
  return [...new Set([...quickPriority, ...session.capabilities])].filter(supported).slice(0, 4);
}

export function hasSlotControls(session: EmulatorSession): boolean {
  return ["slot_previous", "slot_next"].every((action) =>
    session.capabilities.includes(action) && Boolean(session.actions[action]),
  );
}
