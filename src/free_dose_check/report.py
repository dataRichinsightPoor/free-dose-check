"""Deterministic report, marginal bounds, and traceable exports."""
import csv
import io
import itertools
import json
from .model import equilibrium, site_concentration, within, DECISION_RTOL
from .schema import validate, applicability
from .design import recommendations

VERSION = "0.1.0"
METRICS = ("free_nM", "bound_nM", "occupancy", "naive_occupancy", "occupancy_error_pp", "depletion")


def envelope(values):
    if values[0] is None:
        return None
    return {"low": min(values), "high": max(values)}


def analyze(config):
    c = validate(config)
    app, warnings = applicability(c)
    corners = list(itertools.product(sorted(set(c["sites_per_cell"].values())),
                                      sorted(set(c["kd_nM"].values()))))
    r_values = [site_concentration(c["cell_count"], r, c["volume_uL"]) for r, k in corners]
    rows = []
    for dose in c["ligand_total_nM"]:
        states = [equilibrium(r, dose, corner[1]) for r, corner in zip(r_values, corners)]
        row = {"ligand_total_nM": dose, **{
            key: envelope([state[key] for state in states]) for key in METRICS}}
        delta = row["depletion"]
        row["assessment"] = ("not_applicable" if delta is None else
            "within_tolerance" if within(delta["high"], c["depletion_tolerance"]) else
            "exceeds_tolerance" if not within(delta["low"], c["depletion_tolerance"]) else "crosses_tolerance")
        rows.append(row)
    statuses = {r["assessment"] for r in rows}
    status = next(x for x in ("exceeds_tolerance", "crosses_tolerance", "within_tolerance") if x in statuses)
    design = recommendations(c, app)
    warnings += [
        "Research-use model. Biological validation has not yet been established.",
        "Low modeled depletion is not an assay-validity verdict or a functional potency correction.",
        "User-specified bounds are marginal ranges, not confidence intervals or joint trajectories.",
        "Calculation describes incubation before wash or separation.",
    ]
    if app == "unsupported_model":
        warnings.insert(0, "Illustrative mathematical output only: declared biology is outside this model.")
    return {
        "schema_version": "1.0", "model_version": VERSION, "equations_version": "finite-bath-1to1-v1",
        "inputs": c, "units": {"concentrations": "nM", "volume": "uL", "occupancy_error": "percentage_points"},
        "model_applicability": app, "depletion_assessment": status, "design_feasibility": design["status"],
        "decision_relative_tolerance": DECISION_RTOL, "biological_validation": "not_established",
        "bounded_inputs": any(v["low"] != v["high"] for v in (c["sites_per_cell"], c["kd_nM"])),
        "site_concentration_nM": envelope(r_values),
        "model_implied_half_occupancy_nM": envelope([k + r/2 for r, (_, k) in zip(r_values, corners)]),
        "half_occupancy_fold_over_kd": envelope([1 + r/(2*k) for r, (_, k) in zip(r_values, corners)]),
        "doses": rows, "recommendations": design, "warnings": warnings,
    }


def dumps(report):
    return json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"


def to_csv(report):
    """CSV repeats metadata so every exported row retains model context."""
    stream = io.StringIO(newline="")
    fields = ["ligand_total_nM"] + [f"{x}_{side}" for x in METRICS for side in ("low", "high")] + [
        "assessment", "model_applicability", "model_version", "biological_validation", "metadata_json"]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    metadata = {k: v for k, v in report.items() if k != "doses"}
    for dose in report["doses"]:
        row = {"ligand_total_nM": dose["ligand_total_nM"], "assessment": dose["assessment"],
               "model_applicability": report["model_applicability"], "model_version": VERSION,
               "biological_validation": "not_established",
               "metadata_json": json.dumps(metadata, sort_keys=True, separators=(",", ":"), allow_nan=False)}
        for metric in METRICS:
            for side in ("low", "high"):
                row[f"{metric}_{side}"] = None if dose[metric] is None else dose[metric][side]
        writer.writerow(row)
    return stream.getvalue()
