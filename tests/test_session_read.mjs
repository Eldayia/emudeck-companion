import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";

const source = await readFile(new URL("../src/sessionRead.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ESNext },
}).outputText;
const { createSessionRead } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);
let passed = 0;
async function test(name, run) { await run(); passed++; console.log(`OK ${name}`); }
function deferred() { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }

await test("Successful and empty session reads release the gate", async () => {
  const read = createSessionRead();
  assert.deepEqual(await read(async () => ({ session_id: "abc" })), { session_id: "abc" });
  assert.equal(await read(async () => null), null);
});
await test("Decky zero-argument RPC receives no promise fulfillment argument", async () => {
  const read = createSessionRead();
  for (const route of ["get_current_session", "refresh_detection"]) {
    const rpc = async (...args) => {
      assert.deepEqual(args, [], `${route} must not receive undefined/null as an extra argument`);
      return null;
    };
    assert.equal(await read(rpc), null);
  }
});
await test("Synchronous and asynchronous errors surface and release the gate", async () => {
  const read = createSessionRead();
  await assert.rejects(read(() => { throw Error("sync"); }), /sync/);
  await assert.rejects(read(async () => { throw Error("async"); }), /async/);
  assert.equal(await read(async () => null), null);
});
await test("Pending reads do not start overlapping poll or refresh requests", async () => {
  const read = createSessionRead(); const pending = deferred(); let calls = 0;
  const first = read(() => { calls++; return pending.promise; });
  for (let i = 0; i < 10; i++) assert.equal(read(() => { calls++; return Promise.resolve(null); }), null);
  pending.resolve("ok"); assert.equal(await first, "ok"); assert.equal(calls, 1);
});
await test("Timeout is visible but does not reopen the gate or apply a late result", async () => {
  const read = createSessionRead(5); const pending = deferred(); let applied = false;
  const first = read(() => pending.promise);
  first.then(() => { applied = true; }, () => {});
  await assert.rejects(first, /did not respond/);
  assert.equal(read(async () => "duplicate"), null);
  pending.resolve("stale"); await Promise.resolve(); await Promise.resolve();
  assert.equal(applied, false);
  assert.equal(await read(async () => "new"), "new");
});
await test("Late rejection after timeout is handled and permits recovery", async () => {
  const read = createSessionRead(5); const pending = deferred();
  await assert.rejects(read(() => pending.promise), /did not respond/);
  pending.reject(Error("late failure")); await Promise.resolve(); await Promise.resolve();
  assert.equal(await read(async () => "recovered"), "recovered");
});
console.log(`${passed} session read tests passed`);
