import { SteamClient } from "@decky/ui/dist/globals/steam-client";
import { EHIDKeyboardKey } from "@decky/ui/dist/globals/steam-client/Input";

declare const SteamClient: SteamClient;

const keys: Record<string, EHIDKeyboardKey> = {
  a: EHIDKeyboardKey.A,
  d: EHIDKeyboardKey.D,
  f: EHIDKeyboardKey.F,
  p: EHIDKeyboardKey.P,
  r: EHIDKeyboardKey.R,
  enter: EHIDKeyboardKey.Return,
  esc: EHIDKeyboardKey.Escape,
  tab: EHIDKeyboardKey.Tab,
  space: EHIDKeyboardKey.Space,
  insert: EHIDKeyboardKey.Insert,
  home: EHIDKeyboardKey.Home,
  pageup: EHIDKeyboardKey.PageUp,
  end: EHIDKeyboardKey.End,
  f1: EHIDKeyboardKey.F1,
  f2: EHIDKeyboardKey.F2,
  f3: EHIDKeyboardKey.F3,
  f4: EHIDKeyboardKey.F4,
  f5: EHIDKeyboardKey.F5,
  f6: EHIDKeyboardKey.F6,
  f7: EHIDKeyboardKey.F7,
  f8: EHIDKeyboardKey.F8,
  f9: EHIDKeyboardKey.F9,
  f10: EHIDKeyboardKey.F10,
  f11: EHIDKeyboardKey.F11,
  f12: EHIDKeyboardKey.F12,
  leftalt: EHIDKeyboardKey.LAlt,
  leftshift: EHIDKeyboardKey.LShift,
  leftctrl: EHIDKeyboardKey.LControl,
};

export function pressHotkeys(names: string[]): void {
  const mapped = names.map((name) => {
    const key = keys[name.toLowerCase()];
    if (key === undefined) throw new Error(`Unsupported Steam Input key: ${name}`);
    return key;
  });

  mapped.forEach((key) => SteamClient.Input.ControllerKeyboardSetKeyState(key, true));
  window.setTimeout(() => {
    [...mapped].reverse().forEach((key) =>
      SteamClient.Input.ControllerKeyboardSetKeyState(key, false),
    );
  }, 100);
}
