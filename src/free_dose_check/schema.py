"""Strict JSON contract and explicit applicability gate."""
import math
from .model import DOMAIN

ASSUMPTIONS = {
    "equilibrium": "Equilibrium has been reached during incubation.",
    "independent_sites": "One ligand occupies one independent site; no avidity or crosslinking.",
    "closed_system": "No relevant ligand sink, internalization, degradation, or site turnover.",
    "well_mixed": "The incubation is well mixed with one accessible affinity class.",
}


class ValidationError(ValueError):
    pass


def number(x, name, positive=True, integer=False):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValidationError(f"{name}: enter a finite number.")
    try:
        valid = math.isfinite(x)
    except OverflowError:
        valid = False
    if not valid or (x <= 0 if positive else x < 0):
        raise ValidationError(f"{name}: enter a finite {'positive' if positive else 'nonnegative'} number.")
    if integer and (x != int(x) or x > 2**53 - 1):
        raise ValidationError(f"{name}: enter a whole number no greater than 2^53 - 1.")
    return int(x) if integer else float(x)


def bounds(x, name):
    if isinstance(x, dict):
        if set(x) != {"low", "high"}:
            raise ValidationError(f"{name}: bounds require only low and high.")
        low, high = number(x["low"], name), number(x["high"], name)
        if low > high:
            raise ValidationError(f"{name}: low cannot exceed high.")
    else:
        low = high = number(x, name)
    return {"low": low, "high": high}


def text(x, name, required=False):
    if not isinstance(x, str) or (required and not x.strip()):
        raise ValidationError(f"{name}: provide a {'nonempty ' if required else ''}text note.")
    if len(x) > 4000:
        raise ValidationError(f"{name}: maximum 4,000 characters.")
    return x.strip()


def validate(config):
    if not isinstance(config, dict):
        raise ValidationError("Configuration must be a JSON object.")
    required = {"cell_count", "volume_uL", "sites_per_cell", "kd_nM",
                "ligand_total_nM", "provenance", "assumptions"}
    allowed = required | {"depletion_tolerance", "max_volume_uL", "min_cells",
                          "label", "ligand_format", "effective_1to1_justification"}
    missing, unknown = required - config.keys(), config.keys() - allowed
    if missing:
        raise ValidationError("Missing fields: " + ", ".join(sorted(missing)))
    if unknown:
        raise ValidationError("Unknown fields: " + ", ".join(sorted(unknown)))
    c = {
        "label": text(config.get("label", ""), "label"),
        "cell_count": number(config["cell_count"], "cell_count", integer=True),
        "volume_uL": number(config["volume_uL"], "volume_uL"),
        "sites_per_cell": bounds(config["sites_per_cell"], "sites_per_cell"),
        "kd_nM": bounds(config["kd_nM"], "kd_nM"),
        "depletion_tolerance": number(config.get("depletion_tolerance", .1), "depletion_tolerance"),
    }
    if c["depletion_tolerance"] >= 1:
        raise ValidationError("depletion_tolerance must be strictly between 0 and 1.")
    if not DOMAIN[0] <= c["kd_nM"]["low"] <= c["kd_nM"]["high"] <= DOMAIN[1]:
        raise ValidationError("Kd must be within the verified 1e-12 to 1e12 nM domain.")
    doses = config["ligand_total_nM"]
    if not isinstance(doses, list) or not 1 <= len(doses) <= 1000:
        raise ValidationError("ligand_total_nM: provide 1 to 1,000 concentrations.")
    doses = [number(x, "ligand_total_nM", positive=False) for x in doses]
    if len(set(doses)) != len(doses):
        raise ValidationError("Dose concentrations must be distinct.")
    if not any(doses):
        raise ValidationError("Provide at least one positive ligand concentration.")
    if any(x and not DOMAIN[0] <= x <= DOMAIN[1] for x in doses):
        raise ValidationError("Positive doses must be within the verified 1e-12 to 1e12 nM domain.")
    c["ligand_total_nM"] = sorted(doses)
    for key, integer in (("max_volume_uL", False), ("min_cells", True)):
        c[key] = None if config.get(key) is None else number(config[key], key, integer=integer)
    c["assumptions"] = {}
    assumptions = config["assumptions"]
    if not isinstance(assumptions, dict) or set(assumptions) != set(ASSUMPTIONS):
        raise ValidationError("assumptions must contain: " + ", ".join(ASSUMPTIONS))
    for key, value in assumptions.items():
        if not isinstance(value, dict) or set(value) - {"status", "note"}:
            raise ValidationError(f"{key}: provide status and optional note.")
        if value.get("status") not in {"supported", "uncertain", "unsupported"}:
            raise ValidationError(f"{key}: status must be supported, uncertain, or unsupported.")
        c["assumptions"][key] = {"status": value["status"], "note": text(value.get("note", ""), key)}
    prov = config["provenance"]
    if not isinstance(prov, dict) or set(prov) != {"sites_per_cell", "kd_nM"}:
        raise ValidationError("provenance must describe sites_per_cell and kd_nM.")
    c["provenance"] = {}
    for key, value in prov.items():
        if not isinstance(value, dict) or set(value) - {"kind", "note", "basis"}:
            raise ValidationError(f"provenance.{key}: provide kind, note, and optional affinity basis.")
        if value.get("kind") not in {"measured", "literature", "assumed"}:
            raise ValidationError(f"provenance.{key}: kind must be measured, literature, or assumed.")
        c["provenance"][key] = {
            "kind": value["kind"], "note": text(value.get("note"), f"provenance.{key}.note", True)}
    basis = prov["kd_nM"].get("basis", "not_established")
    if basis not in {"independent", "possibly_depleted", "functional", "not_established"}:
        raise ValidationError("Affinity basis must be independent, possibly_depleted, functional, or not_established.")
    if basis == "functional":
        raise ValidationError("Functional EC50/IC50 cannot be used as Kd. Supply an affinity or an explicit assumed sensitivity range.")
    c["provenance"]["kd_nM"]["basis"] = basis
    c["ligand_format"] = config.get("ligand_format", "unspecified")
    if c["ligand_format"] not in {"monovalent", "effective_1to1", "bivalent", "unspecified"}:
        raise ValidationError("Unknown ligand_format.")
    c["effective_1to1_justification"] = text(config.get("effective_1to1_justification", ""), "effective_1to1_justification")
    return c


def applicability(c):
    warnings = []
    states = [v["status"] for v in c["assumptions"].values()]
    unsupported = "unsupported" in states or c["ligand_format"] == "bivalent"
    uncertain = "uncertain" in states or c["ligand_format"] == "unspecified"
    if c["ligand_format"] == "bivalent":
        warnings.append("Bivalent binding is outside this 1:1 model. No actionable recommendations.")
    if c["ligand_format"] == "effective_1to1" and not c["effective_1to1_justification"]:
        uncertain = True
        warnings.append("Effective 1:1 behavior needs an assay-specific justification.")
    basis = c["provenance"]["kd_nM"]["basis"]
    if basis != "independent":
        uncertain = True
        warnings.append(
            "Affinity may be circular if estimated from a depleted assay. Obtain independent support or declare a sensitivity range."
            if basis == "possibly_depleted" else
            "Independent support for affinity is not established; treat results as conditional.")
    for key, v in c["assumptions"].items():
        if v["status"] != "supported":
            warnings.append(f"{key}: {v['status']}. {v['note']}".strip())
    status = "unsupported_model" if unsupported else "assumption_check_required" if uncertain else "supported_under_declared_assumptions"
    return status, warnings
