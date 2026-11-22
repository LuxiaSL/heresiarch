// Headless conformance check for the serverless build.
//
// Mirrors boot.js step-for-step against the staged dist/ — vendored
// pyodide runtime, loadPackage from the local index, wheel + data via
// unpackArchive, the same bootstrap.py — then drives hx_handle through
// new run → zone → full combat → loot, i.e. the JSON contract the
// phone client actually speaks. IDBFS doesn't exist in Node, so
// /persist is plain MEMFS here; everything else is identical.
//
//   uv run python wasm/build.py
//   npm install pyodide@<PYODIDE_VERSION from build.py>   (any dir)
//   node wasm/verify_node.mjs
//
// Exit 0 = the browser build's engine path is good.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { createRequire } from "node:module";

const here = path.dirname(fileURLToPath(import.meta.url));
const dist = path.join(here, "dist");
const require = createRequire(
  process.env.PYODIDE_NODE_MODULES
    ? path.join(process.env.PYODIDE_NODE_MODULES, "/")
    : import.meta.url,
);
const { loadPyodide } = await import(
  require.resolve("pyodide/pyodide.mjs")
);

const t0 = Date.now();
const mark = (label) =>
  console.log(`[${((Date.now() - t0) / 1000).toFixed(1)}s] ${label}`);

// -- boot.js, transliterated --------------------------------------------
const py = await loadPyodide({
  packageBaseUrl: path.join(dist, "pyodide") + path.sep,
  lockFileURL: path.join(dist, "pyodide", "pyodide-lock.json"),
});
mark(`pyodide booted (python ${py.runPython("import sys; sys.version.split()[0]")})`);

await py.loadPackage(["pydantic", "pyyaml"]);
mark("pydantic + pyyaml from vendored index");

const whl = readFileSync(path.join(dist, "heresiarch.whl"));
const site = py.runPython("import site; site.getsitepackages()[0]");
py.unpackArchive(whl.buffer.slice(whl.byteOffset, whl.byteOffset + whl.byteLength), "zip", { extractDir: site });

const dz = readFileSync(path.join(dist, "data.zip"));
py.unpackArchive(dz.buffer.slice(dz.byteOffset, dz.byteOffset + dz.byteLength), "zip", { extractDir: "/data" });

py.FS.mkdir("/persist"); // MEMFS stand-in for the browser's IDBFS mount

const bootstrap = readFileSync(path.join(dist, "bootstrap.py"), "utf-8");
py.runPython(bootstrap);
const handle = py.globals.get("hx_handle");
mark("engine bootstrapped via bootstrap.py");

// -- drive the client's JSON contract ------------------------------------
const call = (p, body) => JSON.parse(handle(p, body ? JSON.stringify(body) : ""));
const act = (tool, args) => {
  const payload = call("/api/action", { tool, args: args || {} });
  if (payload.error) throw new Error(`${tool}: ${payload.error}`);
  return payload;
};

let p = call("/api/state");
if (p.phase !== "SETUP") throw new Error(`expected SETUP, got ${p.phase}`);

p = act("new_run", { name: "WasmSpike", job_id: "einherjar", seed: 42 });
p = act("enter_zone", { zone_id: p.zone_select.zones[0].id });
if (!p.dungeon) throw new Error("dungeon mode: expected a floor payload");

// -- dungeon floor: per-turn latency, then explore until contact --------
const timeIt = (fn, n) => {
  const t = performance.now();
  for (let i = 0; i < n; i++) fn();
  return (performance.now() - t) / n;
};
// wait_turn can trigger an ambush, so time on a copy-safe read first
const readMs = timeIt(() => call("/api/state"), 20);
mark(`state read: ${readMs.toFixed(1)} ms/call`);

const frontier = (d) => {
  let best = null;
  for (let y = 0; y < d.height; y++) for (let x = 0; x < d.width; x++) {
    if (!".>".includes(d.tiles[y][x])) continue;
    const near = [[1,0],[-1,0],[0,1],[0,-1]].some(([dx, dy]) => (d.tiles[y + dy] || "")[x + dx] === " ");
    const dist = Math.abs(x - d.player_x) + Math.abs(y - d.player_y);
    if (near && dist && (!best || dist < best[0])) best = [dist, x, y];
  }
  return best;
};
let turns = 0, turnMs = 0, travels = 0;
while (p.phase === "IN_ZONE" && travels < 200) {
  const d = p.dungeon;
  const foes = d.entities.filter((e) => e.kind !== "ITEM");
  const before = d.turn;
  const t = performance.now();
  if (foes.length) p = act("travel", { x: foes[0].x, y: foes[0].y });
  else {
    const f = frontier(d);
    if (!f) throw new Error("explored everything without meeting a pack");
    p = act("travel", { x: f[1], y: f[2] });
  }
  const dt = performance.now() - t;
  const after = p.dungeon ? p.dungeon.turn : before + 1;
  turns += Math.max(1, after - before); turnMs += dt; travels += 1;
}
const perTurn = turnMs / Math.max(1, turns);
mark(`floor: ${travels} travels, ${turns} turns, ${perTurn.toFixed(1)} ms/turn incl. payload → ${p.phase}`);
if (p.phase !== "COMBAT") throw new Error(`expected contact → COMBAT, got ${p.phase}`);

let rounds = 0;
let events = 0;
while (p.phase === "COMBAT" && rounds < 60) {
  const decisions = {};
  for (const pl of p.combat.players) {
    if (!pl.is_alive) continue;
    const ready = pl.abilities.filter((a) => a.cooldown_remaining === 0);
    const ab = ready.find((a) => a.category === "OFFENSIVE") || ready[0];
    const d = { mode: "normal", action: ab.id };
    if (ab.target === "SINGLE_ENEMY") {
      d.target = p.combat.enemies.find((e) => e.is_alive).id;
    }
    decisions[pl.id] = d;
  }
  p = act("submit_decisions", { decisions });
  rounds += 1;
  events += (p.events || []).length;
}
mark(`combat: ${rounds} rounds, ${events} events → ${p.phase}`);

if (p.phase === "POST_COMBAT") {
  p = act("pick_loot", { item_ids: [] });
  mark(`loot picked → ${p.phase}`);
}

if (rounds < 1 || events < 1 || p.phase === "COMBAT") {
  console.error("VERIFICATION FAILED");
  process.exit(1);
}
console.log("SERVERLESS BUILD VERIFIED");
