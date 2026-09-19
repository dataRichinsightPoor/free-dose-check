# Free-Dose Check

A small, inspectable design aid for a specific question: under a finite-bath, single-site equilibrium model, can free ligand reasonably be approximated by added ligand across a planned titration? It computes depletion and exact one-variable cell-count or volume limits, rather than declaring an assay “valid.”

Version 0.1.0. Research use only. Biological validation is not yet established.

## Run

Requires Python 3.10 or later. The installed package has no third-party runtime dependencies.

```sh
python -m pip install .
free-dose-check analyze examples/constrained.json --json report.json --csv doses.csv
```

Or from Python:

```python
import json
from free_dose_check import analyze
report = analyze(json.load(open("examples/constrained.json")))
```

The browser executes the same package in pinned Pyodide 0.27.7. It does not reimplement the solver in JavaScript. Experimental values are not transmitted, stored in browser storage, or sent to an analysis server. Loading the interface and runtime requires network access; hosting/CDN providers receive ordinary asset requests.

## What this release does

- Computes free and bound ligand, occupancy, depletion, and the error in naive occupancy at each concentration.
- Propagates user-supplied affinity and accessible-site bounds without invented midpoint estimates or confidence intervals.
- Separates model applicability, depletion assessment, and operating-constraint feasibility.
- Forward-checks rounded cell-count and volume recommendations.
- Exports full-precision deterministic JSON and CSV with embedded context.
- Compares one alternative count/volume condition against the same model and assumptions.

## Scientific boundary

Only equilibrium, effectively monovalent 1:1 binding with independent sites in a well-mixed, conserved system is represented. Internalization, avidity, multiple affinity classes, nonspecific sinks, wash-induced dissociation, functional potency, and assay qualification are outside scope. Functional EC50/IC50 is rejected as an affinity input.

The established finite-bath equations and the influence of depletion on binding interpretation are described by [Hulme and Trevethick (2010)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3000649/). The cell-binding context is discussed by [Hunter and Cochran (2016)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6067677/). Related depletion-aware kinetic work already exists; this project does not claim a new binding theory ([Kamprath et al., 2023](https://www.nature.com/articles/s41598-023-37015-1)).

## Reproduce verification and build

```sh
python -m pip install -e '.[test]'
python -m pytest
python tools/build_web.py
python -m build
```

Serve `web/` with any static HTTP server. The browser downloads a Python package ZIP assembled from `src/`; run the build script after any core change. No application backend is required. A pinned runtime CDN is needed for the browser; the Python CLI works offline.

The included static server is `python tools/serve.py --port 3000`. In a separate terminal, optional browser verification uses `npm ci`, `npx playwright install chromium`, then `npm run test:browser`. Afterward, run `python tools/check_browser_parity.py /tmp/free-dose-qa` to compare exported reports with native Python. The Node dependency is test-only, not part of the application runtime.

See `docs/model.md`, `docs/assumptions.md`, `docs/validation.md`, and `docs/quickstart.md`. The release specification is in `docs/specification.md`. Synthetic examples are not experimental validation.

## License

License selection is pending the author's approval before public release. No third-party scientific dataset is bundled. Runtime and test dependencies retain their own licenses.
