import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";

// Compile the pure frontend selector in memory, without a DOM or Steam runtime.
const source = await readFile(new URL("../src/actionLayout.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ESNext },
}).outputText;
const { quickActions, hasSlotControls } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);
let passed = 0;
function test(name, run) {
  run();
  passed++;
  console.log(`OK ${name}`);
}
function session(capabilities) {
  return { capabilities, actions: Object.fromEntries(capabilities.map((key) => [key, { label: key }])) };
}

test("RetroArch defaults prioritize save/load/pause/menu", () => {
  const value = session(["quit", "screenshot", "menu_up", "fast_forward", "pause", "load_state", "save_state", "emulator_menu"]);
  assert.deepEqual(quickActions(value, []), ["save_state", "load_state", "pause", "emulator_menu"]);
});
test("Cemu never receives nonexistent savestate controls", () => {
  assert.deepEqual(quickActions(session(["quit", "fullscreen", "swap_screen", "pause"]), []),
    ["pause", "swap_screen", "fullscreen", "quit"]);
});
test("User favorites retain order and do not get automatic filler", () => {
  const value = session(["save_state", "load_state", "pause", "emulator_menu"]);
  assert.deepEqual(quickActions(value, ["emulator_menu", "save_state"]), ["emulator_menu", "save_state"]);
});
test("Duplicate and stale favorites are removed before the four-action limit", () => {
  const value = session(["pause", "screenshot", "menu_up", "menu_down", "quit"]);
  assert.deepEqual(quickActions(value, ["missing", "quit", "quit", "menu_down", "menu_up", "pause", "screenshot"]),
    ["quit", "menu_down", "menu_up", "pause"]);
});
test("Hidden or unavailable actions cannot return via favorites or defaults", () => {
  const value = session(["load_state", "pause"]);
  value.actions.save_state = { label: "hidden" };
  value.capabilities.push("undefined_action");
  assert.deepEqual(quickActions(value, ["save_state", "undefined_action"]), ["load_state", "pause"]);
});
test("Profiles without common actions retain their own capability order", () => {
  assert.deepEqual(quickActions(session(["special_b", "special_a"]), []), ["special_b", "special_a"]);
  assert.deepEqual(quickActions(session([]), []), []);
});
test("Slot controls require both visible capabilities and definitions", () => {
  const value = session(["slot_previous", "slot_next"]);
  assert.equal(hasSlotControls(value), true);
  value.capabilities = ["slot_previous"];
  assert.equal(hasSlotControls(value), false);
  value.capabilities.push("slot_next");
  delete value.actions.slot_next;
  assert.equal(hasSlotControls(value), false);
});
test("Selection does not mutate session or stored favorites", () => {
  const value = session(["load_state", "save_state", "pause"]);
  const favorites = ["pause", "pause", "save_state"];
  const original = JSON.stringify({ value, favorites });
  quickActions(value, favorites);
  hasSlotControls(value);
  assert.equal(JSON.stringify({ value, favorites }), original);
});
console.log(`${passed} frontend tests passed`);
