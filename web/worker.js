/* All experimental values stay in this dedicated local worker. */
let py;
async function boot() {
  importScripts("https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js");
  py = await loadPyodide({indexURL:"https://cdn.jsdelivr.net/pyodide/v0.27.7/full/"});
  const response = await fetch(PACKAGE_URL);
  if (!response.ok) throw new Error("Python package could not be loaded.");
  py.unpackArchive(await response.arrayBuffer(), "zip");
  py.runPython("import json\nfrom free_dose_check import analyze, dumps, to_csv");
  postMessage({type:"ready"});
}
self.onmessage = async event => {
  const {type, id, config, report, alternative} = event.data;
  try {
    if (type === "analyze") {
      py.globals.set("_config_json", JSON.stringify(config));
      const result = JSON.parse(py.runPython("dumps(analyze(json.loads(_config_json)))"));
      let alt = null;
      if (alternative) {
        py.globals.set("_config_json", JSON.stringify(alternative));
        alt = JSON.parse(py.runPython("dumps(analyze(json.loads(_config_json)))"));
      }
      py.runPython("del _config_json");
      postMessage({type:"result", id, report:result, alternative:alt});
    } else if (type === "csv") {
      py.globals.set("_report_json", JSON.stringify(report));
      const csv = py.runPython("to_csv(json.loads(_report_json))");
      py.runPython("del _report_json");
      postMessage({type:"csv", id, csv});
    }
  } catch (error) {
    postMessage({type:"error", id, message:String(error.message).split("\n").filter(Boolean).pop()});
  }
};
boot().catch(error => postMessage({type:"boot_error",message:String(error.message)}));
