import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";

const source = await readFile(new URL("../src/gameDetails.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ESNext },
}).outputText;
const { gameDetails, releaseDate } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);
let passed = 0;
function test(name, run) { run(); passed++; console.log(`OK ${name}`); }

test("Only present descriptive metadata is displayed", () => {
  assert.deepEqual(gameDetails({ genre: " RPG ", developer: "Square", publisher: "Publisher", players: "1-2",
    releasedate: "19970131T000000", rating: "0.85", name: "Game", image: "/private/path.png" }).rows, [
    ["Genre", "RPG"], ["Developer", "Square"], ["Publisher", "Publisher"], ["Players", "1-2"],
    ["Release date", "1997-01-31"], ["ES-DE rating", "85%"],
  ]);
});
test("Missing and ES-DE sentinel values do not fabricate information", () => {
  assert.deepEqual(gameDetails({ genre: "unknown", developer: " UNKNOWN ", publisher: 12,
    players: null, rating: "0", releasedate: "19700101T000000", desc: " " }),
    { rows: [], descriptionPages: [], descriptionTruncated: false });
});
test("Dates are validated without timezone conversion", () => {
  assert.equal(releaseDate("20000229T235959"), "2000-02-29");
  assert.equal(releaseDate("1998-07-14"), "1998-07-14");
  assert.equal(releaseDate("19980714"), "1998-07-14");
  for (const invalid of ["19000229T000000", "20010431", "20001301", "20000001", "20000100",
    "20000101T240000", "20000101T006000", "20000101T000060", "00000101", "garbage", "1998", null, 1998]) {
    assert.equal(releaseDate(invalid), null, String(invalid));
  }
});
test("Ratings are bounded decimal fractions, not arbitrary numeric strings", () => {
  assert.deepEqual(gameDetails({ rating: ".5" }).rows, [["ES-DE rating", "50%"]]);
  assert.deepEqual(gameDetails({ rating: "1" }).rows, [["ES-DE rating", "100%"]]);
  for (const invalid of ["", "0", "-0.5", "1.1", "85", "NaN", "Infinity", "0x1", "1e-1", 0.5]) {
    assert.deepEqual(gameDetails({ rating: invalid }).rows, [], String(invalid));
  }
});
test("Long descriptions are paginated without losing words", () => {
  const desc = Array.from({ length: 300 }, (_, i) => `word${i}`).join(" ");
  const details = gameDetails({ desc });
  assert.ok(details.descriptionPages.length > 1);
  assert.ok(details.descriptionPages.every((page) => page.length > 0 && page.length <= 400));
  assert.equal(details.descriptionPages.join(" "), desc);
  assert.equal(details.descriptionTruncated, false);
});
test("Single words and surrogate pairs do not break pagination", () => {
  for (const desc of ["x".repeat(1100), "x".repeat(399) + "🎮" + "y".repeat(402)]) {
    const pages = gameDetails({ desc }).descriptionPages;
    assert.equal(pages.join(""), desc);
    assert.ok(pages.every((page) => !/[\uD800-\uDBFF]$/.test(page) && !/^[\uDC00-\uDFFF]/.test(page)));
  }
});
test("Oversized descriptions and fields have explicit rendering limits", () => {
  const details = gameDetails({ desc: "x".repeat(13000), genre: "y".repeat(1000) });
  assert.equal(details.descriptionTruncated, true);
  assert.equal(details.descriptionPages.join("").length, 12000);
  assert.equal(details.rows[0][1].length, 158);
  assert.equal(gameDetails({ genre: "x".repeat(156) + "🎮".repeat(10) }).rows[0][1], "x".repeat(156) + "…");
  const emoji = gameDetails({ desc: "x".repeat(11999) + "🎮" });
  assert.equal(emoji.descriptionPages.join("").length, 11999);
});
test("Markup is retained as plain text, not interpreted or stripped", () => {
  const desc = '<script>alert("test")</script> A & B';
  const metadata = { desc, developer: "<b>Studio</b>" };
  const snapshot = JSON.stringify(metadata);
  assert.deepEqual(gameDetails(metadata).descriptionPages, [desc]);
  assert.equal(JSON.stringify(metadata), snapshot);
});
console.log(`${passed} game details tests passed`);
