import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";

const source = await readFile(new URL("../src/actionDelivery.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ESNext },
}).outputText;
const { deliverKeyboard, pressChord } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);
let passed = 0;
async function test(name, run) { await run(); passed++; console.log(`OK ${name}`); }

await test("Report waits until the complete press/release operation finishes", async () => {
  const calls = [];
  const result = await deliverKeyboard(async () => { await Promise.resolve(); calls.push("press"); }, async (ok) => {
    calls.push(`report:${ok}`); return { ok: true };
  });
  assert.deepEqual(calls, ["press", "report:true"]);
  assert.equal(result.ok, true);
});
await test("Synchronous and asynchronous failures are reported as failures", async () => {
  for (const press of [() => { throw new Error("down failed"); }, async () => { throw new Error("up failed"); }]) {
    let delivery;
    const result = await deliverKeyboard(press, async (ok, error) => { delivery = { ok, error }; return { ok: true }; });
    assert.equal(result.ok, false);
    assert.equal(delivery.ok, false);
    assert.match(delivery.error, /failed/);
  }
});
await test("Report transport errors never resend keys or imply input failure", async () => {
  let presses = 0;
  const result = await deliverKeyboard(() => { presses++; }, async () => { throw new Error("RPC unavailable"); });
  assert.equal(presses, 1);
  assert.equal(result.ok, true);
  assert.match(result.reportError, /RPC unavailable/);
});
await test("Rejected reports remain separate from successful input delivery", async () => {
  const result = await deliverKeyboard(() => {}, async () => ({ ok: false }));
  assert.equal(result.ok, true);
  assert.match(result.reportError, /not accepted/);
});
await test("Key chords release in reverse order after the hold interval", async () => {
  const calls = [];
  await pressChord(["ctrl", "f2"], (key, down) => calls.push([key, down]), async () => { calls.push("wait"); });
  assert.deepEqual(calls, [["ctrl", true], ["f2", true], "wait", ["f2", false], ["ctrl", false]]);
});
await test("A failed key down releases every attempted key without retrying", async () => {
  const calls = [];
  await assert.rejects(pressChord(["ctrl", "f2", "extra"], (key, down) => {
    calls.push([key, down]); if (key === "f2" && down) throw new Error("down failed");
  }, async () => { throw new Error("should not wait"); }), /down failed/);
  assert.deepEqual(calls, [["ctrl", true], ["f2", true], ["f2", false], ["ctrl", false]]);
});
await test("A failed release still releases the other keys and surfaces the error", async () => {
  const calls = [];
  await assert.rejects(pressChord(["ctrl", "f2"], (key, down) => {
    calls.push([key, down]); if (key === "f2" && !down) throw new Error("release failed");
  }, async () => {}), /release failed/);
  assert.deepEqual(calls, [["ctrl", true], ["f2", true], ["f2", false], ["ctrl", false]]);
});
await test("Failed wait still releases the chord", async () => {
  const calls = [];
  await assert.rejects(pressChord(["f2"], (key, down) => calls.push([key, down]), async () => {
    throw new Error("timer failed");
  }), /timer failed/);
  assert.deepEqual(calls, [["f2", true], ["f2", false]]);
});
console.log(`${passed} action delivery tests passed`);
