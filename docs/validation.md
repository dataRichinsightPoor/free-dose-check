# Verification and validation status

Free-Dose Check v0.1.0 has a numerical and software verification suite. Biological validation, user adoption, decision improvement, time saved, and assay-success benefits have not been established.

## Automated numerical checks

The test suite uses an independent 100-decimal-digit `mpmath` evaluation of the subtractive quadratic as an oracle. Production uses scaled double-precision, rationalized roots; the oracle deliberately uses a different numerical evaluation.

- **Oracle cases:** 125 logarithmic-grid combinations, 3,000 seeded log-random combinations, and 15 nearly equal total-ligand/site cases. Positive concentrations span \(10^{-12}\) to \(10^{12}\) nM.
- **Accuracy criterion:** Relative error at most \(10^{-9}\) for both positive free and bound concentration. There is no absolute-error exemption for very small free concentration.
- **Reference fixture:** 100,000 cells, 100,000 sites/cell, 100 µL, \(K_d=0.1\) nM, and doses 0, 0.01, 0.1, 1, and 10 nM.
- **Invariants:** Ligand conservation, valid states, zero-dose handling, half occupancy, low-receptor limit, count-volume scaling, and monotonic directions.
- **Bounds:** 1,000 seeded interior parameter pairs evaluated at all four positive reference doses to check marginal-corner enclosure.
- **Recommendations:** 500 seeded scenarios verify the forward model after rounding each design option.

The high-precision oracle is numerical verification of the equations, not independent experimental validation of their biological premises.

## Software-contract checks

The tests cover malformed values, finite domains, duplicate/all-zero doses, affinity/valency gates, missing evidence, bounds crossing, scalar/bounded output, constraint failures, suppressed recommendations, metadata-preserving CSV, deterministic JSON round-trip, and CLI output parity.

The browser uses the same Python files bundled from `src/free_dose_check`, running in Pyodide 0.27.7. The interface adds no second binding solver. Browser QA checks actual execution, example outcomes, comparison, input errors, export content, stale-result handling, theme, and narrow-screen layout.

Test and browser-QA counts in the implementation receipt describe the run performed for that snapshot, rather than a guarantee about subsequent modifications. Run `python -m pytest` after changing code and rebuild browser assets before checking parity.

## Prospective biological evaluation needed

A useful next validation study would predeclare conditions rather than merely show a clean fitted curve. This proposal is not completed validation.

Use a defensible monovalent binding system with independently supported affinity, accessible-site capacity, incubation equilibrium, and absence of meaningful sinks. Select several conditions spanning predicted low/high depletion and one declared boundary-crossing uncertainty case. Where feasible, independently measure unbound ligand rather than deriving every endpoint from the same occupancy fit.

Hold concentrations fixed while changing cell count or volume as recommended. Predeclare tolerances on measured free concentration and the decision criterion, blind the held-out conditions during model setup, and compare against both the naive free-equals-added assumption and the simple “no change” baseline. Record failures, signal loss, practicality, and assay-specific scope violations.

The decision-relevant question is whether the tool correctly warns when the approximation is inadequate and proposes a practically usable change, not whether an optimizer can produce a favorable fit. No portfolio claim should convert synthetic accuracy into demonstrated experimental value.
