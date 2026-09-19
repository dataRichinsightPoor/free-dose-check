# Free-Dose Check
## First-release specification: v0.1.0

Status: ready for implementation planning; software not yet implemented.  
Release class: research-use, model-based assay-design aid.  
Proposed repository: `free-dose-check`; Python module: `free_dose_check`.  
Prepared: September 19, 2026.

**Product promise:** Before running a cell-binding titration, determine whether finite binding capacity could materially reduce free ligand, and identify cell-number or volume changes that meet a declared depletion tolerance under explicit assumptions.

The release solves one problem: deciding whether the approximation “free ligand concentration equals added ligand concentration” is acceptable for a proposed equilibrium binding experiment. It does not decide whether the experiment as a whole is valid.

## Problem statement

An assay scientist chooses a concentration series, cell number, and volume, but the relevant binding-site concentration may be comparable with the ligand concentration. Receptor binding then consumes enough ligand that the free concentration differs from the added concentration; under a single-site equilibrium model, the concentration producing half occupancy also shifts with binding-site concentration ([Hulme and Trevethick, 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC3000649/)).

This is particularly relevant to designing cell-binding measurements, where changing cell number and assay volume changes total binding-site concentration ([Hunter and Cochran, 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC6067677/)). The decision this tool supports is whether to proceed with the planned density, change cells or volume, obtain a better binding-capacity estimate, or use a different analysis/model.

The problem and its mathematics are not new. Published work already uses depletion-aware kinetic models to estimate affinity and accessible binding-site number on cells and tissue ([Kamprath and colleagues, 2023](https://www.nature.com/articles/s41598-023-37015-1)). The proposed contribution is a small, transparent pre-experiment check with explicit input uncertainty, practical constraints, and testable recommendations, not a novel binding model.

Frequency of use and time saved are not yet measured. No adoption, efficiency, or experimental-success claim should be made before evaluation.

## Goals

- **Expose the approximation:** For every positive input concentration, return free ligand, bound ligand, occupancy, depletion, and the occupancy error introduced by treating added ligand as free.
- **Support a practical decision:** Return analytically derived cell-number and volume limits for a selected depletion tolerance, checked against user-supplied constraints.
- **Preserve uncertainty:** Accept bounded uncertainty in accessible binding sites and affinity without turning those bounds into confidence intervals or invented probability distributions.
- **Prevent overinterpretation:** Distinguish model assumptions, numerical verification, and biological validation in every report.
- **Make the result reproducible:** Export the exact inputs, units, assumptions, model version, equations version, and outputs used for each recommendation.

## Non-goals

- **Affinity fitting or correction:** No fitting raw fluorescence, estimating an unknown \(K_d\), or correcting an observed functional EC50/IC50.
- **Multivalent or heterogeneous-affinity binding:** No bivalent IgG avidity, receptor crosslinking, cooperative binding, competing ligands, or multiple affinity classes.
- **Dynamic biology:** No internalization, receptor synthesis, trafficking, growth, time-to-equilibrium prediction, or kinetic fitting.
- **Additional ligand sinks:** No adsorption, nonspecific binding, degradation, serum binding, or ligand loss to equipment.
- **Assay qualification:** No regulatory suitability claim, clinical prediction, automatic cell-line selection, or guarantee that a mathematically feasible design supplies adequate signal.

For the first release, Fab fragments, nanobodies, peptides, or other ligands with a defensible effective 1:1 interaction are the clearest intended use. Intact IgG must not be accepted as 1:1 merely because it has one antigen specificity; a user must supply a defensible assay-specific justification or receive an unsupported-model result.

## User stories

- **Assay developer:** As an assay developer, I want to compare two cell counts at the same volume and concentration series so that I can choose a condition with acceptably small modeled depletion.
- **Scientist with uncertain capacity:** As a scientist with an approximate accessible-site count, I want a bounded result so that I know whether uncertainty changes the recommendation.
- **Scientist with plate constraints:** As a scientist limited by maximum volume and minimum cell count, I want infeasible changes identified so that I do not receive an unusable “solution.”
- **Reviewer or collaborator:** As a reviewer, I want equations, assumptions, and machine-readable inputs so that I can independently reproduce the conclusion.
- **User outside model scope:** As a user studying an internalizing bivalent antibody, I want the tool to explain why its standard calculation is not applicable rather than return a misleading assurance.

## Requirements

### Release boundary and priorities

P0 is a verified calculation core, a minimal browser form, a CLI, reproducible exports, and the scientific documentation. There is no account system, database, server-side computation, raw-data upload, curve fitting, or AI component.

- **P0, must ship:** Single-condition analysis; optional comparison with one alternative condition; scalar or bounded \(K_d\) and accessible-site inputs; concentration-wise outputs; constraint-aware one-variable design recommendations; assumption gate; JSON/CSV export; tests and worked examples.
- **P1, first follow-up:** Import existing JSON configurations through the browser; user-defined combinations of volume and cell number; optional HTML report export. These must not delay v0.1.0.
- **P2, consider after observed demand:** Instrument-specific input templates and accessibility-calibration tutorials. These require validated conventions rather than arbitrary conversions.
- **Won’t ship in this release:** All non-goals above, probabilistic uncertainty inference, automated receptor-count estimation, and recommendations inferred from uploaded fluorescence data.

### Scientific contract

Assume a closed, well-mixed incubation at equilibrium with one class of accessible independent binding sites and one ligand molecule per occupied site. Ligand and sites are conserved; no relevant nonspecific sink, ligand instability, or receptor turnover is represented.

The state being calculated is the state during binding incubation, before any separation or wash. The tool does not model ligand dissociation during flow-cytometry preparation or other downstream processing.

The assumption gate uses `supported`, `uncertain`, or `unsupported` for each assumption, with an optional note. Any explicit violation gives `unsupported_model` and suppresses actionable recommendations; an uncertain assumption allows an illustrative calculation labeled `assumption_check_required`, not a green overall result.

Users may export such illustrative results, but exports must preserve the warning. The software cannot independently establish equilibrium from incubation duration because this release does not accept kinetic rate constants.

### Inputs and provenance

Use explicit field names and display units; never infer units from magnitude.

- **`cell_count`:** Positive whole-number cells in the binding incubation, not cells subsequently acquired by the instrument. Treat this as fixed in v0.1; cell-count uncertainty can be explored through separate scenarios.
- **`volume_uL`:** Positive final incubation volume in microliters. Exclude wash volume.
- **`sites_per_cell`:** Positive accessible binding sites per cell, either a scalar or `{low, high}`. Permit noninteger values because this may be a population average.
- **`kd_nM`:** Positive equilibrium dissociation constant, either a scalar or `{low, high}`. Require \(K_d>0\), not an association constant.
- **`ligand_total_nM`:** One or more distinct nonnegative finite concentrations, including at least one positive value. A zero-dose control is allowed.
- **`depletion_tolerance`:** A fraction strictly between zero and one. Default 0.10, visibly labeled an editable planning convention rather than a universal acceptance criterion.
- **`max_volume_uL`:** Optional user-specified maximum usable incubation volume.
- **`min_cells`:** Optional user-specified minimum usable cell count.
- **`provenance`:** For sites and affinity, record `measured`, `literature`, or `assumed`, plus a short source/condition note. Synthetic examples use `assumed` and an explicit synthetic label.

Accessible binding capacity is not automatically identical to total expression or raw fluorescence; ligand-dependent accessibility and valency affect the interpretation of measured sites ([Hunter and Cochran, 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC6067677/); [Kamprath and colleagues, 2023](https://www.nature.com/articles/s41598-023-37015-1)). No automatic conversion from MFI, transcript abundance, or arbitrary antibody-binding units is permitted.

Do not accept a functional IC50/EC50 as \(K_d\). If the only affinity estimate came from a potentially depleted cell-binding assay, the report must flag circularity and recommend an independently supported value or a declared sensitivity range.

Intervals are user-specified bounds, not statistical confidence intervals. Missing values must prompt an explicit assumption rather than silently populate a generic receptor count or affinity.

### Governing equations

Let \(N\) be cells, \(r\) accessible sites per cell, \(V\) volume in liters, and \(N_A=6.02214076\times10^{23}\ \mathrm{mol^{-1}}\). Total accessible-site concentration in molar units is

\[
R_T=\frac{Nr}{N_A V}.
\]

Convert consistently to nM for the public interface. With the stated units, the implementation can use

\[
R_{T,\mathrm{nM}}=\frac{Nr\,10^{15}}{N_A V_{\mathrm{\mu L}}}.
\]

For total ligand \(L_T\), free ligand \(L_f\), and bound complex \(B\), the equilibrium and conservation equations are

\[
K_d=\frac{(R_T-B)(L_T-B)}{B}, \qquad L_f=L_T-B.
\]

The physically admissible bound concentration is

\[
B=\frac{R_T+L_T+K_d-
\sqrt{(R_T+L_T+K_d)^2-4R_TL_T}}{2}.
\]

These are the established single-site equilibrium equations with ligand conservation, not a new model ([Hulme and Trevethick, 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC3000649/)).

Report

\[
\delta=\frac{B}{L_T},\qquad
\theta=\frac{B}{R_T},\qquad
\theta_{\mathrm{naive}}=\frac{L_T}{K_d+L_T}.
\]

Depletion \(\delta\) is the fraction of added ligand bound, not the fraction of sites occupied. Display occupancy error as \(100(\theta_{\mathrm{naive}}-\theta)\) percentage points; do not conflate percentage-point occupancy error with percent ligand depletion.

At zero ligand, return \(B=L_f=\theta=\theta_{\mathrm{naive}}=0\), with depletion and its dose-level assessment set to `null`/`not_applicable`. Never render a zero-dose depletion value of 0% as evidence that the design passes.

The model’s total ligand concentration at half occupancy is

\[
L_{T,50}=K_d+\frac{R_T}{2}.
\]

This relationship is established for the binding model ([Hulme and Trevethick, 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC3000649/)). Label it “model-implied half-occupancy concentration,” not a fitted EC50, measured \(K_d\), or functional potency.

### Numerically stable implementation

Do not use the subtractive quadratic expression as the only implementation. Use a scaled, rationalized evaluation for \(B\):

\[
D=\sqrt{(R_T-L_T)^2+K_d^2+2K_d(R_T+L_T)},\qquad
B=\frac{2R_TL_T}{R_T+L_T+K_d+D}.
\]

To preserve very small free concentrations, independently evaluate the nonnegative root of

\[
L_f^2+(K_d+R_T-L_T)L_f-K_dL_T=0.
\]

Writing \(a=K_d+R_T-L_T\), use the rationalized expression for \(a\geq0\) and the direct noncancelling expression for \(a<0\):

\[
L_f=
\begin{cases}
\dfrac{2K_dL_T}{\sqrt{a^2+4K_dL_T}+a}, & a\geq0,\\[6pt]
\dfrac{\sqrt{a^2+4K_dL_T}-a}{2}, & a<0.
\end{cases}
\]

Scale concentrations before multiplication to prevent overflow. Check physical bounds and mass balance after evaluation; return `numerical_error` if tolerances are violated rather than silently clipping a materially impossible result.

The numerical acceptance suite must cover nonzero \(R_T,L_T,K_d\) from \(10^{-12}\) to \(10^{12}\) nM, including extreme ratios. Inputs outside that verified numerical domain may be rejected with an explicit range message; this range is a software verification boundary, not a claim of experimental plausibility.

### Uncertainty and decision rules

For bounded inputs, evaluate the four combinations of \(r_{\mathrm{low/high}}\) and \(K_{d,\mathrm{low/high}}\). Compute a separate min/max for each output; do not assume that the same corner minimizes both depletion and occupancy.

Under this model, depletion increases with site concentration and decreases with \(K_d\). Thus the worst case for depletion is \(r_{\mathrm{high}},K_{d,\mathrm{low}}\), and the best case is \(r_{\mathrm{low}},K_{d,\mathrm{high}}\). The corners give marginal ranges over the specified rectangular input domain, not a joint confidence region.

For tolerance \(\epsilon\), assign a dose-level status:

- **`within_tolerance`:** Maximum modeled depletion is at or below \(\epsilon\).
- **`exceeds_tolerance`:** Minimum modeled depletion is above \(\epsilon\).
- **`crosses_tolerance`:** The specified input bounds include both outcomes.
- **`not_applicable`:** Zero-dose control only.

Use unrounded values with a documented numerical comparison tolerance; display rounding must not decide status. If any positive dose exceeds tolerance, the overall depletion assessment is `exceeds_tolerance`; otherwise any crossing gives `crosses_tolerance`; otherwise it is `within_tolerance`.

Keep `model_applicability`, `depletion_assessment`, and `design_feasibility` as separate fields. A depletion result within tolerance is not an overall “assay passed” result.

Evaluate every positive input concentration. Do not silently drop low doses to make a design pass; a changed concentration series is a new analysis with its own inputs.

### Design recommendations

Derive recommendations from the exact model rather than a blanket “ligand must exceed receptor by tenfold” rule. At the boundary \(\delta=\epsilon\), substituting \(B=\epsilon L_T\) into mass action gives

\[
R_{\mathrm{cap}}(L_T,K_d,\epsilon)
=\epsilon L_T+\frac{\epsilon K_d}{1-\epsilon}.
\]

Therefore, for all positive doses, use the smallest \(R_{\mathrm{cap}}\), occurring at the smallest positive \(L_T\). For bounded inputs, use \(K_{d,\mathrm{low}}\) and \(r_{\mathrm{high}}\) for recommendations that are conservative over the stated bounds.

With \(R_{\mathrm{cap}}\) in molar units, calculate:

\[
V_{\min}=\frac{Nr}{N_A R_{\mathrm{cap}}},\qquad
N_{\max}=\frac{N_A V R_{\mathrm{cap}}}{r}.
\]

Offer two independent options: increase volume holding cell count and each ligand concentration fixed, or reduce cell count holding volume and each ligand concentration fixed. Increasing volume at fixed concentration requires proportionally more ligand molecules; prominently show that reagent-use multiplier.

Round the cell recommendation down to a whole number. Show the mathematical minimum volume and an upward-rounded display recommendation, then re-evaluate the rounded recommendation through the core.

Check volume against `max_volume_uL` and cells against `min_cells`. If neither one-variable option meets the supplied limits, return “No one-variable solution within supplied constraints,” not “No solution exists”; combined changes are outside v0.1.

If constraints are absent, label options “mathematically sufficient; operational feasibility not assessed.” Reducing cell number is not a guarantee of sufficient detection signal, and increasing ligand concentration is not automatically offered because it changes the intended binding experiment.

### Outputs and user experience

The browser is one page with an assumption gate, input form, and result panel. Provide one synthetic worked example, but do not populate a real analysis with its values without an explicit “Load example” action.

The result panel contains:

- **Decision statement:** Model applicability and whether the free-equals-added approximation meets the selected tolerance over the supplied dose range.
- **Concentration-wise results:** Added, free, and bound ligand; occupancy; naive occupancy; occupancy error; depletion; and status, as values or bounded ranges.
- **Two figures:** Depletion versus added concentration with the selected tolerance; exact occupancy versus the naive occupancy curve. Zero-dose controls appear separately from the logarithmic concentration axis.
- **Design alternatives:** Current condition, required volume at fixed cells, and maximum cells at fixed volume, with constraint checks and reagent-use consequence.
- **Assumptions and provenance:** Visible, not hidden in a tooltip or downloadable appendix.

Default wording: “Modeled depletion exceeds your 10% planning tolerance at some tested concentrations. This is a warning about the free-concentration approximation, not a verdict on assay validity.”

JSON is the canonical export and includes `schema_version`, `model_version`, normalized inputs, provenance, assumptions, concentration-wise results, statuses, constraints, and recommendations. CSV is a derived human-readable export; its accompanying metadata must retain the assumptions and model version. Store full numerical precision in JSON, with deterministic serialization and no volatile timestamp in reference fixtures.

### Implementation shape

Use a pure-Python standard-library numerical core with no required scientific-computing dependencies. Provide `analyze(config) -> report` and a thin CLI:

```text
free-dose-check analyze config.json --json report.json --csv doses.csv
```

Keep assumptions and input validation in a shared application layer so the CLI cannot bypass the browser’s scientific warnings. Use a static browser frontend with pinned Pyodide to execute the same Python implementation, avoiding a second independently maintained binding solver.

Implementation dependencies are sequential: schema and units precede the numerical core; the verified core precedes uncertainty bounds and design limits; those precede report generation; the CLI and browser depend on that shared report layer. The examples, model documentation, and test oracles can be prepared alongside the core, but a browser mockup is not a substitute for passing the numerical gates.

The browser must not transmit experimental inputs, save them remotely, or load them into analytics. Static asset requests may occur; computation and export stay client-side. Public example data must be synthetic or appropriately licensed.

Suggested repository structure:

```text
src/free_dose_check/
  model.py
  design.py
  schema.py
  report.py
  cli.py
tests/
  test_model.py
  test_design.py
  test_bounds.py
  test_contract.py
  fixtures/
examples/
docs/
  model.md
  assumptions.md
  validation.md
  quickstart.md
web/
CITATION.cff
LICENSE
README.md
```

Use an MIT license for original code, subject to author approval, and identify third-party licenses separately. Every public interface should display “Research-use model; biological validation status: not yet established” until evidence justifies a narrower updated claim.

### Worked synthetic acceptance case

Use 100,000 cells, 100,000 accessible sites per cell, 100 µL, \(K_d=0.1\) nM, and total ligand concentrations 0, 0.01, 0.1, 1, and 10 nM. These are deliberately synthetic values, not a specific cell line or therapeutic.

The exact site concentration is approximately 0.166053907 nM. At 0.1 nM added ligand, the calculation should return:

- Free ligand: approximately 0.0469479480 nM.
- Bound ligand: approximately 0.0530520520 nM.
- Depletion: approximately 53.0520520%.
- Occupancy: approximately 31.9486925%.
- Naive occupancy: 50%.
- Occupancy error: approximately 18.0513075 percentage points.

The model-implied half-occupancy concentration is approximately 0.183026953 nM, or 1.83026953 times \(K_d\). Do not present that ratio as the result of fitting a 4PL curve.

Across all four positive doses, a 10% depletion tolerance implies a minimum volume of approximately 1,371.0873 µL at fixed cell count, or at most 7,293 cells at 100 µL. With limits of 200 µL maximum and 20,000 cells minimum, neither one-variable change is feasible.

This example should end in an informative limitation, not force a “recommended” plate configuration. Its point is that a computation can reveal that the desired approximation conflicts with the stated design constraints.

### Acceptance tests

- **Reference calculation:** Given the synthetic case above, when analyzed, then outputs match full-precision committed fixtures within `rtol=1e-9` and `atol=1e-12 nM` for concentrations.
- **Independent oracle:** Given log-spaced and extreme-ratio parameter cases, when compared with a high-precision test-only root solver, then every strictly positive concentration has relative error at most \(10^{-9}\), including tiny free concentrations; do not use the reference-case absolute tolerance to excuse rounding a positive state to zero. Test dependencies may use arbitrary precision even though runtime dependencies do not.
- **Physical identities:** Given supported parameters, then \(0\leq B\leq\min(R_T,L_T)\), \(0\leq L_f\leq L_T\), and fractions lie in \([0,1]\); conservation and equilibrium hold to scale-aware tolerance.
- **Midpoint identity:** Given \(L_T=K_d+R_T/2\), then computed occupancy is 0.5 within tolerance.
- **Dilute-site limit:** Given decreasing \(R_T\) at fixed \(L_T,K_d\), then free ligand approaches added ligand and exact occupancy approaches naive occupancy.
- **Density invariance:** Given cells and volume scaled by the same positive factor, then concentration-based binding outputs remain unchanged.
- **Direction checks:** Given increased sites or decreased \(K_d\), then depletion does not decrease; given increased volume at fixed cells and added concentration, depletion does not increase.
- **Zero-dose control:** Given zero alongside positive doses, then zero contributes no depletion status and does not distort the overall assessment.
- **Input rejection:** Given negative, missing, nonfinite, reversed-bound, duplicate-dose, or all-zero-dose inputs, then return an explicit input error without a normal report.
- **Bound handling:** Given a parameter rectangle crossing tolerance, then return `crosses_tolerance`, no fabricated central estimate, and conservative design limits from the stated worst case.
- **Analytic recommendation:** Given a model-derived design limit, then forward calculation at the boundary meets the selected tolerance; the downward-rounded cell recommendation must also meet it.
- **Constraint failure:** Given the synthetic case with 200 µL maximum and 20,000 cells minimum, then report no feasible one-variable option, while leaving combined-change feasibility unspecified.
- **Scope refusal:** Given a declared violation such as meaningful bivalent avidity or ongoing internalization, then return `unsupported_model` and no actionable design recommendation.
- **Assumption uncertainty:** Given any unconfirmed assumption, then preserve `assumption_check_required` through browser, CLI, JSON, and CSV metadata.
- **Frontend parity:** Given identical inputs, browser and CLI outputs match because they use the same core; all synthetic fixtures must run through both paths.
- **Round-trip provenance:** Given an exported JSON report, then the normalized inputs and model version suffice to regenerate its numerical results exactly within the pinned environment.

## Success metrics and validation

### Release gates

All P0 acceptance tests must pass in CI before v0.1.0 is tagged. All user-facing results must preserve units, applicability warnings, and input provenance; no unresolved numerical or decision-status discrepancy may be waived as a cosmetic issue.

Ship three examples: a low-depletion design, the constrained high-depletion case, and a bounded-input case that crosses tolerance. Include a deliberately unsupported bivalent/internalizing case to demonstrate refusal behavior.

The browser must support input, analysis, and export without login or submission of data. Verify this manually and through a browser smoke test before publishing the viewer.

### User usefulness

Before promoting v0.1 beyond an initial research release, target five volunteer assay scientists completing three fixed decision tasks: identify an affected dose range, choose a feasible change, and recognize an unsupported-model case. Target at least four of five completing each correctly; this is a proposed usability gate, not an observed result.

Measure baseline performance with the same information and a short written equation sheet, then compare errors and completion time. Report results descriptively; five users cannot establish broad effectiveness or a reliable time-saving claim.

### Scientific validation ladder

- **Verified computation:** Exact identities and independent numerical oracles establish that the equations were implemented correctly. This is required for v0.1.0.
- **Published-example reproduction:** Attempt a compatible equilibrium example using traceable concentrations and capacity estimates. Confirm that the necessary raw observations, conditions, and reuse rights actually exist before naming it a benchmark; none is secured by this specification.
- **Held-out perturbation:** With a suitable monovalent ligand and cell system, specify the predictions before observing a new density or volume condition. Compare the finite-bath prediction with the constant-free-ligand baseline using independently supported affinity/capacity inputs.
- **Prospective test:** If a collaborator runs new experiments, prerecord the conditions, prediction intervals or bounded envelopes, scoring rule, assay repeatability, and failure criteria. Publish failures as well as successes.

The user’s essay argues for decision-relevant testing against simple baselines and for distinguishing methods performance from biological progress ([“Fifteen Hard Problems, One Easy Benchmark”](https://ermelindadamko.substack.com/p/fifteen-hard-problems-one-easy-benchmark)). Here, the consequential test is whether a predicted change in binding behavior under a new cell-number or volume condition is supported, not whether the software can recover the equations that generated its synthetic data.

Do not tune a fresh affinity for each held-out condition. Prespecify whether the measured endpoint is occupancy, calibrated bound ligand, or an independently justified proportional signal; a fluorescence change without a suitable observation model is not automatically a test of occupancy.

The initial release may ship as a numerically verified planning tool without experimental validation. Its README and reports must say so; claims of improved experimental decisions require subsequent evidence.

## Open questions and implementation decisions

- **Author, nonblocking:** Confirm the repository name and code license. Defaults are `free-dose-check` and MIT, with no publication or repository creation authorized by this specification.
- **Scientific owner, blocking for biological validation only:** Identify a public benchmark or collaborator with an effective 1:1 system, independently supported inputs, and a density/volume perturbation. No employer-derived or unpublished proprietary data should be used.
- **Scientific owner, nonblocking for implementation:** Choose any assay-specific depletion tolerance. v0.1 retains an editable 10% default, not a universal validity threshold.
- **Implementation owner, blocking before release:** Document and test practical frontend loading behavior and the verified numerical range. Pin runtime and browser dependencies.

No broader modeling choices are left open for v0.1: it is equilibrium-only, one-site, no fitting, two one-variable design alternatives, bounded rather than probabilistic uncertainty, and explicit refusal outside scope.

## Definition of done

A new user can enter an explicit assay design, see whether the free-equals-added approximation meets their chosen tolerance under the stated model, inspect a feasible alternative or an honest constraint failure, and export a fully reproducible record. They should leave knowing what to change or what still needs measurement, not believing that the tool has validated the assay.
