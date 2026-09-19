# Quickstart

Free-Dose Check 0.1.0 is a browser and Python tool with the same scientific core. It calculates conditional equilibrium binding states, not functional potency or assay validity.

## Browser

Choose a synthetic case and explicitly select “Load & run,” or enter your own incubation inputs and evidence notes. The form begins with empty experimental inputs; only the editable 10% planning tolerance is initialized.

For uncertainty, enable “Use bounds” for accessible sites and/or affinity. Enter genuine lower and upper bounds rather than a standard deviation. Each output is independently bounded, with no invented nominal estimate.

Declare the ligand format and all four assumptions. An unsupported declaration keeps illustrative outputs but suppresses recommendations. Uncertain declarations produce a conditional warning, not a reassuring model verdict.

Optionally enter maximum volume and minimum cells. To compare another condition, enable the comparison and provide both alternative cell count and volume; all other inputs and constraints remain unchanged.

Run the check. The table contains every dose, including zero controls; the plots omit zero from their log axis. Download JSON for a full-precision canonical report or CSV for rows with embedded metadata. The alternative condition has its own complete JSON export.

Changing inputs marks existing results stale and disables exports until rerun. Results are not automatically recalculated from partial edits.

## CLI

Requires Python 3.10 or later.

```sh
python -m pip install .
free-dose-check analyze examples/constrained.json --json report.json --csv doses.csv
```

Without `--json`, the full report is printed to standard output. Invalid inputs produce a structured error on standard error and exit code 2. Successful analysis returns 0; a depletion warning or unsupported model is a scientific result, not a program execution failure.

## Input contract

See `examples/constrained.json` for a complete, directly executable JSON input. The following fields are accepted:

| Field | Meaning |
|---|---|
| `cell_count` | Positive whole count in incubation, at most \(2^{53}-1\) |
| `volume_uL` | Positive final incubation volume |
| `sites_per_cell` | Positive accessible-site number or `{low, high}` |
| `kd_nM` | Positive equilibrium dissociation constant or `{low, high}` |
| `ligand_total_nM` | Distinct nonnegative dose list; at least one positive; at most 1,000 entries |
| `depletion_tolerance` | Fraction strictly between 0 and 1; default 0.1 |
| `max_volume_uL`, `min_cells` | Optional positive operating constraints |
| `provenance` | Sites and affinity: `kind`, nonempty `note`; affinity also `basis` |
| `assumptions` | `equilibrium`, `independent_sites`, `closed_system`, `well_mixed`: status and optional note |
| `ligand_format` | `monovalent`, `effective_1to1`, `bivalent`, or `unspecified` |
| `effective_1to1_justification` | Assay-specific note for an effective 1:1 format |
| `label` | Optional condition identifier retained in exports |

Unknown keys are rejected to catch misspellings. Functional affinity basis is rejected. Positive affinity, ligand, and resulting site concentrations outside the verified \(10^{-12}\) to \(10^{12}\) nM input domain are rejected.

## Output contract

`schema_version`, `model_version`, and `equations_version` are explicit. Inputs are normalized, dose order is sorted, scalar numeric inputs become equal low/high bounds, and provenance is preserved.

`model_applicability`, `depletion_assessment`, and `design_feasibility` are separate. Every concentration-wise metric is `{low, high}`, except undefined zero-dose depletion which is `null`. There is no volatile timestamp or probabilistic interpretation.

The canonical report is reproducible with `analyze(report["inputs"])`. Python `dumps` uses sorted keys, full standard floating-point precision, and rejects nonfinite output. CSV repeats compact report metadata per dose so a detached row still carries assumptions, inputs, version, limits, and recommendations. It is larger than a bare table by design.

## Offline and privacy

The CLI runs offline after installation and has no runtime dependencies beyond Python. The browser requires runtime assets from jsDelivr, optional fonts from Google Fonts, and the static hosting files; it does not send experimental values to those providers or an analysis service.

No account, database, telemetry, local/session storage, or service worker is used. Reloading the page clears unsaved inputs. Download a report if the conditions need to be retained.
