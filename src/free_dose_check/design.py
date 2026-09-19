"""Exact one-variable design limits, rounded and forward checked."""
import math
from .model import AVOGADRO, DOMAIN, NumericalError, site_concentration, equilibrium, within


def recommendations(c, applicability_status):
    if applicability_status == "unsupported_model":
        return {"status": "suppressed", "message": "No actionable recommendations: model unsupported.",
                "volume_option": None, "cell_option": None}
    eps = c["depletion_tolerance"]
    dose = min(x for x in c["ligand_total_nM"] if x > 0)
    kd = c["kd_nM"]["low"]
    sites = c["sites_per_cell"]["high"]
    cap = eps*dose + eps*kd/(1-eps)
    if cap < DOMAIN[0]:
        return {"status": "numerical_domain_limit",
                "message": "The required site capacity is below the verified numerical domain; no actionable option is returned.",
                "volume_option": None, "cell_option": None}
    volume_min = c["cell_count"] * (sites / AVOGADRO) * 1e15 / cap
    cells_max = (AVOGADRO / 1e15) * (c["volume_uL"] / sites) * cap
    if not all(math.isfinite(x) for x in (cap, volume_min, cells_max)):
        return {"status": "numerical_domain_limit", "message": "Design limits cannot be represented.",
                "volume_option": None, "cell_option": None}
    # Display resolution is 0.001 uL; ceil never recommends a too-small volume.
    volume_rounded = (math.ceil(volume_min * 1000) / 1000 if volume_min < 1e12
                      else math.nextafter(volume_min, math.inf))
    if not math.isfinite(volume_rounded):
        return {"status": "numerical_domain_limit", "message": "A sufficient rounded volume cannot be represented.",
                "volume_option": None, "cell_option": None}
    volume = max(c["volume_uL"], volume_rounded)
    cells = min(c["cell_count"], math.floor(cells_max))

    def check(n, v):
        if n < 1:
            return False, None, "Fewer than one cell would be required."
        try:
            r = site_concentration(n, sites, v)
            delta = max(equilibrium(r, x, kd)["depletion"] for x in c["ligand_total_nM"] if x > 0)
            return within(delta, eps), delta, None
        except NumericalError as exc:
            return False, None, str(exc)

    vv, vd, ve = check(c["cell_count"], volume)
    cv, cd, ce = check(cells, c["volume_uL"])
    # Both supplied operating constraints apply to each option, including fixed variables.
    def constraints(n, v):
        failures = []
        if c["max_volume_uL"] is not None and v > c["max_volume_uL"]:
            failures.append("maximum volume exceeded")
        if c["min_cells"] is not None and n < c["min_cells"]:
            failures.append("minimum cell count not met")
        return failures

    vf, cf = constraints(c["cell_count"], volume), constraints(cells, c["volume_uL"])
    any_constraints = c["max_volume_uL"] is not None or c["min_cells"] is not None
    def option(verified, delta, error, failures, **kwargs):
        return dict(**kwargs, forward_verified=verified, worst_depletion=delta,
                    feasible_with_supplied_constraints=bool(verified and not failures) if any_constraints else None,
                    constraint_failures=failures, error=error)
    status = ("no_one_variable_solution_within_supplied_constraints" if any_constraints and not (
        (vv and not vf) or (cv and not cf)) else "one_variable_option_available" if any_constraints and (
        vv or cv) else "operational_feasibility_not_assessed" if vv or cv else "numerical_domain_limit")
    return {
        "status": status, "conditional": applicability_status != "supported_under_declared_assumptions",
        "limiting_dose_nM": dose, "site_cap_nM": cap,
        "minimum_volume_uL": volume_min, "maximum_cells": cells_max,
        "volume_option": option(vv, vd, ve, vf, volume_uL=volume,
                                cell_count=c["cell_count"], reagent_multiplier=volume/c["volume_uL"]),
        "cell_option": option(cv, cd, ce, cf, cell_count=cells, volume_uL=c["volume_uL"]),
        "message": {
            "no_one_variable_solution_within_supplied_constraints": "No one-variable solution within supplied constraints. Combined changes were not analyzed.",
            "one_variable_option_available": "A mathematically sufficient option meets supplied constraints; detection signal is not established.",
            "operational_feasibility_not_assessed": "Mathematically sufficient; operational feasibility not assessed.",
            "numerical_domain_limit": "No forward-verified option within the verified numerical domain.",
        }[status],
    }
