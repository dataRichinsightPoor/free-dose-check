# Free-Dose Check v0.1.0: implementation receipt

This first-release implementation was prepared September 19, 2026. It includes a runnable browser application and downloadable repository snapshot. The author approved public GitHub publication as `dataRichinsightPoor/free-dose-check` and the MIT license on the same date.

## Implemented

- **Shared scientific core:** Standard-library Python finite-bath 1:1 equilibrium solver, conservative design limits, strict inputs, explicit applicability gates, bounded inputs, and deterministic reports.
- **Interfaces:** Python API, installed CLI, and a static browser application executing the same source in Pyodide 0.27.7.
- **Decisions:** Per-dose and overall depletion assessment, independent volume/cell alternatives, constraints, forward verification after rounding, and optional alternative-condition comparison.
- **Evidence handling:** Required provenance notes, functional-affinity rejection, circular-affinity warning, unsupported/uncertain assumption behavior, and complete metadata in JSON/CSV.
- **Usability:** Four explicitly synthetic examples, two plots, per-dose table, light/dark themes, mobile layout, stale-result handling, and source/documentation downloads.
- **Reproducibility:** Equations, assumptions, validation plan, quickstart, release spec, automated tests, browser QA script, parity checker, build script, and proposed GitHub CI configuration.

## Verification performed

The native Python suite contains 47 passing test cases at this snapshot. Within those cases are 3,140 high-precision oracle comparisons of positive free/bound concentrations, 1,000 parameter pairs checked for bounded enclosure at four positive doses, and 500 forward-checked design scenarios.

Browser/native parity was checked for four synthetic scenarios, a baseline JSON download, an alternative-condition JSON download, and all CSV rows plus embedded metadata. Numerical equality is required within \(10^{-12}\) relative tolerance, without an absolute-error exemption; nonnumeric contract fields must match.

Browser checks include input blankness on startup, supported/uncertain/unsupported gates, functional-input rejection, duplicate/all-zero input rejection, editing and stale-export disabling, comparison, downloads, light/dark layouts, and mobile viewport overflow checks. The runtime was also exercised inside an opaque-origin sandbox iframe.

Local tools used: Python 3.14.3, pytest 9.1.1, mpmath 1.4.1, and Playwright 1.59.0. These verification results describe the initial local implementation. For remote CI results, consult the repository's GitHub Actions runs rather than treating this local receipt as evidence of completed remote CI.

## Public-release boundary

Biological validation remains not established. Synthetic correctness does not show that accessible-site counts, affinity, equilibrium, or absence of sinks are true in a real assay, or that a suggested condition supplies enough signal.

Original project code and documentation use the MIT license; third-party dependencies retain their own terms. The repository and app must not be presented as a biologically validated assay or as a novel binding theory; the contribution is the constrained, inspectable decision workflow.
