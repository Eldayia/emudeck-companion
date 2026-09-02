import { SteamClient } from "@decky/ui/dist/globals/steam-client";
import { EHIDKeyboardKey } from "@decky/ui/dist/globals/steam-client/Input";
import { pressChord } from "./actionDelivery";

declare const SteamClient: SteamClient;

const keys: Record<string, EHIDKeyboardKey> = {
  "1": EHIDKeyboardKey.Key_1,
  "2": EHIDKeyboardKey.Key_2,
  "3": EHIDKeyboardKey.Key_3,
  "4": EHIDKeyboardKey.Key_4,
  "5": EHIDKeyboardKey.Key_5,
  "6": EHIDKeyboardKey.Key_6,
  "7": EHIDKeyboardKey.Key_7,
  "8": EHIDKeyboardKey.Key_8,
  "9": EHIDKeyboardKey.Key_9,
  "0": EHIDKeyboardKey.Key_0,
  a: EHIDKeyboardKey.A,
  b: EHIDKeyboardKey.B,
  c: EHIDKeyboardKey.C,
  e: EHIDKeyboardKey.E,
  g: EHIDKeyboardKey.G,
  h: EHIDKeyboardKey.H,
  i: EHIDKeyboardKey.I,
  j: EHIDKeyboardKey.J,
  k: EHIDKeyboardKey.K,
  l: EHIDKeyboardKey.L,
  m: EHIDKeyboardKey.M,
  n: EHIDKeyboardKey.N,
  o: EHIDKeyboardKey.O,
  q: EHIDKeyboardKey.Q,
  t: EHIDKeyboardKey.T,
  u: EHIDKeyboardKey.U,
  v: EHIDKeyboardKey.V,
  w: EHIDKeyboardKey.W,
  x: EHIDKeyboardKey.X,
  y: EHIDKeyboardKey.Y,
  z: EHIDKeyboardKey.Z,
  s: EHIDKeyboardKey.S,
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
  pagedown: EHIDKeyboardKey.PageDown,
  delete: EHIDKeyboardKey.Delete,
  backspace: EHIDKeyboardKey.Backspace,
  up: EHIDKeyboardKey.UpArrow,
  down: EHIDKeyboardKey.DownArrow,
  left: EHIDKeyboardKey.LeftArrow,
  right: EHIDKeyboardKey.RightArrow,
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

export async function pressHotkeys(names: string[]): Promise<void> {
  const mapped = names.map((name) => {
    const key = keys[name.toLowerCase()];
    if (key === undefined) throw new Error(`Unsupported Steam Input key: ${name}`);
    return key;
  });

  await pressChord(mapped,
    (key, pressed) => SteamClient.Input.ControllerKeyboardSetKeyState(key, pressed),
    () => new Promise<void>((resolve) => window.setTimeout(resolve, 100)),
  );
}
