"""Build web runtime bundle, synthetic configs, and downloadable repository snapshot."""
import copy
import json
import shutil
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
web = ROOT / "web"
web.mkdir(exist_ok=True)
with ZipFile(web / "free_dose_check.zip", "w", ZIP_DEFLATED) as archive:
    for path in sorted((ROOT / "src/free_dose_check").glob("*.py")):
        archive.write(path, "free_dose_check/" + path.name)

base = json.loads((ROOT / "examples/constrained.json").read_text())
examples = {"constrained": base}
low = copy.deepcopy(base)
low.update(label="Synthetic: low depletion", cell_count=1000, min_cells=500)
examples["low"] = low
bounded = copy.deepcopy(base)
bounded.update(label="Synthetic: bounds cross tolerance",
               sites_per_cell={"low": 1000, "high": 100000},
               kd_nM={"low": .05, "high": .2})
examples["bounded"] = bounded
unsupported = copy.deepcopy(base)
unsupported.update(label="Synthetic: unsupported internalizing bivalent ligand", ligand_format="bivalent")
unsupported["assumptions"]["closed_system"] = {"status": "unsupported", "note": "Illustrative internalization during incubation."}
unsupported["assumptions"]["independent_sites"] = {"status": "unsupported", "note": "Bivalent binding with potential crosslinking."}
examples["unsupported"] = unsupported
for key, config in examples.items():
    (ROOT / "examples" / f"{key}.json").write_text(json.dumps(config, indent=2) + "\n")
(web / "examples.json").write_text(json.dumps(examples, indent=2) + "\n")
downloads = web / "downloads"
downloads.mkdir(exist_ok=True)
for path in (ROOT / "docs").glob("*.md"):
    shutil.copy2(path, downloads / path.name)
with ZipFile(downloads / "free-dose-check-v0.1.0.zip", "w", ZIP_DEFLATED) as archive:
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if not path.is_file() or any(
            part in {".git", ".pytest_cache", "__pycache__", "downloads", "build", "dist", "node_modules"}
            or part.endswith(".egg-info") for part in relative.parts
        ) or path.suffix == ".pyc" or path.name == "free_dose_check.zip":
            continue
        archive.write(path, "free-dose-check/" + str(relative))
print("Built Python runtime ZIP, examples, documentation, and source snapshot.")
