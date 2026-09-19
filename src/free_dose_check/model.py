"""Scaled, cancellation-resistant finite-bath 1:1 equilibrium.

Public concentration units are nM. No experimental validity is inferred.
"""
import math

AVOGADRO = 6.02214076e23
DOMAIN = (1e-12, 1e12)
DECISION_RTOL = 1e-10


class NumericalError(ValueError):
    """A calculation is outside the verified domain or violates invariants."""


def within(value, tolerance):
    return value <= tolerance * (1 + DECISION_RTOL)


def site_concentration(cells, sites, volume_uL):
    try:
        result = (cells / volume_uL) * sites * (1e15 / AVOGADRO)
    except (OverflowError, ZeroDivisionError) as exc:
        raise NumericalError("Site concentration cannot be represented.") from exc
    if not math.isfinite(result) or not DOMAIN[0] <= result <= DOMAIN[1]:
        raise NumericalError("Total sites must be within 1e-12 to 1e12 nM (verified numerical domain).")
    return result


def equilibrium(receptor_nM, ligand_nM, kd_nM):
    for name, value, zero in [
        ("Total sites", receptor_nM, False),
        ("Total ligand", ligand_nM, True),
        ("Kd", kd_nM, False),
    ]:
        if not math.isfinite(value) or not (
            (zero and value == 0) or DOMAIN[0] <= value <= DOMAIN[1]
        ):
            raise NumericalError(f"{name} is outside the verified 1e-12 to 1e12 nM domain.")
    if ligand_nM == 0:
        return dict(bound_nM=0.0, free_nM=0.0, occupancy=0.0,
                    naive_occupancy=0.0, occupancy_error_pp=0.0, depletion=None)
    scale = max(receptor_nM, ligand_nM, kd_nM)
    r, l, k = (x / scale for x in (receptor_nM, ligand_nM, kd_nM))
    # Subtract BEFORE scaling: independently rounded r and l can destroy
    # the small difference of nearly equal original concentrations.
    difference = (receptor_nM - ligand_nM) / scale
    disc = math.sqrt(difference**2 + k*k + 2*k*(r + l))
    bound = (2*r*l / (r + l + k + disc)) * scale
    # fsum matters when R and L nearly cancel but K is very small.
    a = math.fsum((kd_nM, receptor_nM, -ligand_nM)) / scale
    root = math.hypot(a, 2 * math.sqrt(k) * math.sqrt(l))
    free = ((2*k*l / (root + a)) if a >= 0 else (root - a)/2) * scale
    occupancy = bound / receptor_nM
    depletion = bound / ligand_nM
    naive = l / (k + l)
    if not (
        0 <= bound <= min(receptor_nM, ligand_nM) * (1 + 1e-13)
        and 0 < free <= ligand_nM * (1 + 1e-13)
        and math.isclose(bound + free, ligand_nM, rel_tol=1e-12)
        and 0 <= occupancy <= 1 + 1e-13
        and naive - occupancy >= -1e-13
    ):
        raise NumericalError("Physical bounds or ligand mass balance failed.")
    # Suppress only floating-point-scale negative occupancy error, not states.
    error = max(0.0, 100 * (naive - occupancy))
    return dict(bound_nM=bound, free_nM=free, occupancy=occupancy,
                naive_occupancy=naive, occupancy_error_pp=error, depletion=depletion)
