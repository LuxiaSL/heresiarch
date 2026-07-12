/* Heresiarch engine-in-wasm bootstrap.
 *
 * Injected before the game client's inline script by build.py. Defines
 * window.HX_LOCAL_DISPATCH synchronously — the client's transport()
 * seam sees it and never touches fetch("/api/...") — then boots
 * Pyodide in the background. The client's first api("/api/state")
 * simply awaits the boot promise, so the stock "loading…" screen
 * covers wasm startup.
 *
 * Persistence: /persist is an IDBFS mount (IndexedDB), holding
 * agent_notes.json and agent_saves/ — game saves survive reloads.
 */
(function () {
  "use strict";

  function status(msg) {
    var el = document.querySelector("#app .sub");
    if (el) el.textContent = msg;
  }

  function loadScript(src) {
    return new Promise(function (ok, err) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = ok;
      s.onerror = function () { err(new Error("failed to load " + src)); };
      document.head.appendChild(s);
    });
  }

  function fetchBuffer(url) {
    return fetch(url).then(function (res) {
      if (!res.ok) throw new Error(url + " → HTTP " + res.status);
      return res.arrayBuffer();
    });
  }

  var py = null;
  var handle = null;
  var persistTimer = null;

  var boot = (async function () {
    status("waking wasm python…");
    await loadScript("./pyodide/pyodide.js");
    py = await loadPyodide({ indexURL: "./pyodide/" });

    status("loading pydantic + pyyaml…");
    await py.loadPackage(["pydantic", "pyyaml"]);

    status("installing the engine…");
    var whl = await fetchBuffer("./heresiarch.whl");
    var site = py.runPython("import site; site.getsitepackages()[0]");
    py.unpackArchive(whl, "zip", { extractDir: site });

    status("loading game data…");
    var dz = await fetchBuffer("./data.zip");
    py.unpackArchive(dz, "zip", { extractDir: "/data" });

    // Saves + notes survive reloads via IndexedDB
    py.FS.mkdir("/persist");
    py.FS.mount(py.FS.filesystems.IDBFS, {}, "/persist");
    await new Promise(function (ok, err) {
      py.FS.syncfs(true, function (e) { e ? err(e) : ok(); });
    });

    status("summoning the heresiarch…");
    var bootstrap = await (await fetch("./bootstrap.py")).text();
    py.runPython(bootstrap);
    handle = py.globals.get("hx_handle");
  })();

  boot.catch(function (e) {
    console.error(e);
    status("boot failed: " + e.message);
  });

  var syncBusy = false;
  var syncAgain = false;
  function flushPersist() {
    if (persistTimer) { clearTimeout(persistTimer); persistTimer = null; }
    if (!py) return;
    if (syncBusy) { syncAgain = true; return; } // serialize; rerun after
    syncBusy = true;
    py.FS.syncfs(false, function (e) {
      syncBusy = false;
      if (e) console.error("persist sync failed:", e);
      if (syncAgain) { syncAgain = false; flushPersist(); }
    });
  }

  function schedulePersist() {
    // Debounced IndexedDB flush; the visibility hooks below close the
    // window where swiping the app away could lose the last action
    if (persistTimer) return;
    persistTimer = setTimeout(flushPersist, 500);
  }

  // Mobile browsers kill background PWAs without warning — flush the
  // moment we stop being visible
  window.addEventListener("pagehide", flushPersist);
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") flushPersist();
  });

  window.HX_LOCAL_DISPATCH = async function (path, body) {
    await boot;
    var out = handle(path, body ? JSON.stringify(body) : "");
    // Imports are rare and explicit — make them durable right now;
    // everything else rides the debounce
    if (path === "/api/import_save") flushPersist();
    else schedulePersist();
    return JSON.parse(out);
  };
})();
