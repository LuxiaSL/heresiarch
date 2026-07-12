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

  function schedulePersist() {
    // Debounced IndexedDB flush; losing the last 500ms on tab-kill is fine
    if (persistTimer) return;
    persistTimer = setTimeout(function () {
      persistTimer = null;
      if (py) py.FS.syncfs(false, function () {});
    }, 500);
  }

  window.HX_LOCAL_DISPATCH = async function (path, body) {
    await boot;
    var out = handle(path, body ? JSON.stringify(body) : "");
    schedulePersist();
    return JSON.parse(out);
  };
})();
