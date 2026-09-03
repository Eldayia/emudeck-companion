import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";

const source = await readFile(new URL("../src/saveStateFiles.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ESNext },
}).outputText;
const { stateFilePage, stateFileSize } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);
let passed = 0;
function test(name, run) { run(); passed++; console.log(`OK ${name}`); }
const state = (number) => ({ path: `/states/Game.state${number}`, slot: number, modified_at: 100 + number, size: 1024 });

test("Pagination exposes all files, newest first, in groups of five", () => {
  const states = Array.from({ length: 12 }, (_, i) => state(i));
  assert.deepEqual(stateFilePage(states, 0).items.map((x) => x.slot), [11, 10, 9, 8, 7]);
  assert.deepEqual(stateFilePage(states, 2).items.map((x) => x.slot), [1, 0]);
  assert.equal(stateFilePage(states, 2).pages, 3);
  assert.equal(stateFilePage(states, 2).total, 12);
});
test("Page index is clamped after files disappear and on invalid input", () => {
  assert.equal(stateFilePage([state(1)], 4).page, 0);
  for (const page of [-1, NaN, Infinity]) assert.equal(stateFilePage([state(1)], page).page, 0);
  assert.deepEqual(stateFilePage([], 5), { items: [], page: 0, pages: 1, total: 0 });
});
test("Empty or invalid input does not invent empty slots", () => {
  for (const input of [null, {}, [null, 3, {}, { path: "" }, { path: 1 }]]) assert.equal(stateFilePage(input, 0).total, 0);
});
test("Unknown metadata stays unknown and slot zero remains valid", () => {
  const files = stateFilePage([{ path: "/file", slot: -1, modified_at: NaN, size: -1 }, state(0)], 0).items;
  assert.equal(files[0].slot, 0);
  assert.deepEqual(files[1], { path: "/file", name: "file", slot: null, modifiedAt: null, size: null });
  for (const bad of [true, "1", Infinity, 1.5]) {
    const file = stateFilePage([{ path: "/x", slot: bad, size: bad }], 0).items[0];
    assert.equal(file.slot, null); assert.equal(file.size, null);
  }
});
test("Duplicate paths keep the newest observation without merging distinct files in a slot", () => {
  const result = stateFilePage([state(1), { ...state(1), modified_at: 200 }, { ...state(1), path: "/other/Game.state1" }], 0);
  assert.equal(result.total, 2); assert.equal(result.items[0].modifiedAt, 200);
});
test("Filenames retain accents and markup as text; full paths remain only identifiers", () => {
  const file = stateFilePage([{ ...state(1), path: 'C:\\states\\Été <game>.state1' }], 0).items[0];
  assert.equal(file.name, 'Été <game>.state1');
});
test("Sorting is deterministic and never mutates the backend snapshot", () => {
  const states = Object.freeze([Object.freeze(state(1)), Object.freeze(state(3))]);
  const result = stateFilePage(states, 0); result.items[0].slot = 99;
  assert.equal(states[1].slot, 3); assert.equal(states[0].slot, 1);
});
test("Binary size units and invalid dates are explicit", () => {
  assert.equal(stateFileSize(0), "0 B"); assert.equal(stateFileSize(1024), "1.0 KiB");
  assert.equal(stateFileSize(1048576), "1.0 MiB"); assert.equal(stateFileSize(1073741824), "1.0 GiB");
  assert.equal(stateFileSize(null), "Size unknown");
  for (const date of [-1, Infinity, 8640000000001, "100", true]) assert.equal(stateFilePage([{ ...state(0), modified_at: date }], 0).items[0].modifiedAt, null);
});
console.log(`${passed} savestate file tests passed`);
