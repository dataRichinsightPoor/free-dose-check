# Applicability and evidence

Version 0.1.0 is a research-use mathematical model, not a validated assay qualification system. Software verification does not establish biological applicability.

## Required declarations

Each assumption is `supported`, `uncertain`, or `unsupported`, with an optional explanatory note. Supported means declared by the scientist; the tool does not independently verify it.

- **Equilibrium:** The incubation has reached the equilibrium represented by the model. Incubation duration alone is insufficient to demonstrate this; kinetic rates are not accepted by this release.
- **Independent sites:** One ligand per accessible independent site, with no relevant multivalent avidity, crosslinking, or cooperativity.
- **Closed system:** No relevant internalization, site turnover, degradation, nonspecific binding, or equipment adsorption.
- **Well mixed:** Homogeneous access with one represented affinity class, without transport limitation or inaccessible compartments.

Cell-binding assay interpretation depends on the measurement conditions and the binding format; accessible ligand-binding capacity should not be inferred automatically from arbitrary fluorescence or total expression ([Hunter and Cochran, 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC6067677/)).

## Gate behavior

Any unsupported assumption or a declared bivalent format yields `unsupported_model`. The output remains available as an explicitly illustrative mathematical calculation, but both design alternatives are suppressed in browser, JSON, and CSV.

An uncertain assumption, unspecified ligand format, unjustified “effective 1:1” format, or affinity without independent support yields `assumption_check_required`. Conditional alternatives may be shown, but they are not an assurance about the assay.

The apparently supported status is named `supported_under_declared_assumptions`, rather than “validated.” The depletion and design-feasibility statuses remain separate.

## Provenance

Both accessible sites and affinity require a provenance kind (`measured`, `literature`, or `assumed`) and a nonempty source/condition note. There are no automatic receptor counts or affinity defaults. The 10% depletion tolerance is a visible, editable planning convention.

Affinity basis is `independent`, `possibly_depleted`, `not_established`, or `functional`. A potentially depleted assay can produce circular input assumptions, so the output asks for independent support or a declared sensitivity range. A functional EC50/IC50 is rejected as an affinity.

Synthetic cases are explicitly labeled and use assumed inputs. Their “supported” declarations stipulate a simulated model; they do not represent experimental evidence. A condition label remains in every export to preserve this distinction.

## Deliberate exclusions

The tool does not model internalization, kinetics, receptor synthesis, multiple affinity classes, ligand competition, nonspecific sinks, wash-induced dissociation, avidity, or functional potency. A small fractional depletion does not establish adequate detection signal, specificity, equilibrium, or assay precision.

Published depletion-aware kinetic approaches address related but different inference tasks; this tool is not a substitute for them ([Kamprath et al., 2023](https://www.nature.com/articles/s41598-023-37015-1)).
