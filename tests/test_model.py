import itertools
import math
import random
import mpmath as mp
import pytest
from free_dose_check.model import equilibrium, site_concentration, NumericalError


@pytest.mark.parametrize("dose,bound,free", [
    (.01, .006152388766771189, .003847611233228811),
    (.1, .05305205199682758, .046947948003172424),
    (1, .1486002644147373, .8513997355852627),
    (10, .16438260738936422, 9.835617392610637),
])
def test_reference(dose, bound, free):
    r = site_concentration(100000, 100000, 100)
    assert r == pytest.approx(.16605390671738468, rel=1e-14)
    state = equilibrium(r, dose, .1)
    assert state["bound_nM"] == pytest.approx(bound, rel=1e-9, abs=1e-12)
    assert state["free_nM"] == pytest.approx(free, rel=1e-9, abs=1e-12)


def test_independent_high_precision_oracle():
    mp.mp.dps = 100
    rng = random.Random(991)
    grid = list(itertools.product([1e-12, 1e-6, 1, 1e6, 1e12], repeat=3))
    random_cases = [tuple(10**rng.uniform(-12, 12) for _ in range(3)) for _ in range(3000)]
    near_equal = [(r, r*(1+d), 1e-12) for r in [1, 1e6, 1e11]
                  for d in [-1e-10, -1e-14, 0, 1e-14, 1e-10]]
    for r, l, k in grid + random_cases + near_equal:
        s = equilibrium(r, l, k)
        R, L, K = map(mp.mpf, (r, l, k))
        # Independent high-precision subtractive quadratic, not production algorithm.
        B = (R+L+K-mp.sqrt((R+L+K)**2-4*R*L))/2
        F = L-B
        for actual, expected in [(s["bound_nM"], B), (s["free_nM"], F)]:
            relative_error = abs(mp.mpf(actual)-expected)/expected
            assert relative_error <= mp.mpf("1e-9"), (r, l, k, actual, str(expected), str(relative_error))
        assert math.isclose(s["bound_nM"] + s["free_nM"], l, rel_tol=1e-12)
        actual_b, actual_f = mp.mpf(s["bound_nM"]), mp.mpf(s["free_nM"])
        scaled_residual = abs((R-actual_b)*actual_f-K*actual_b)/(R*actual_f+K*actual_b)
        assert scaled_residual <= mp.mpf("1e-12"), (r,l,k,str(scaled_residual))
        # Residual evaluated at high precision avoids subtractive roundoff in nearly full occupancy.
        assert abs((R-B)*F-K*B) / max(K*B, mp.mpf("1e-100")) < mp.mpf("1e-50")


@pytest.mark.parametrize("r,k", [(1e-12,1e-12), (1,1), (100,.0001), (.01,100)])
def test_half_occupancy(r, k):
    assert equilibrium(r, k+r/2, k)["occupancy"] == pytest.approx(.5, rel=1e-12)


def test_zero():
    assert equilibrium(1, 0, 1) == dict(bound_nM=0, free_nM=0, occupancy=0,
                                      naive_occupancy=0, occupancy_error_pp=0, depletion=None)


def test_invariance_dilute_and_monotonicity():
    r = site_concentration(10000, 100000, 50)
    assert r == site_concentration(20000, 100000, 100)
    dilute = equilibrium(1e-12, 1, 1)
    assert dilute["occupancy"] == pytest.approx(.5, rel=1e-10)
    base = equilibrium(1, 1, 1)
    assert equilibrium(2,1,1)["depletion"] > base["depletion"]
    assert equilibrium(1,1,2)["depletion"] < base["depletion"]
    assert equilibrium(1,2,1)["depletion"] < base["depletion"]
    assert equilibrium(1,2,1)["occupancy"] > base["occupancy"]


@pytest.mark.parametrize("r,l,k", [(0,1,1), (1,-1,1), (1,1,0), (1,1,float("nan")), (1e13,1,1)])
def test_domain(r,l,k):
    with pytest.raises(NumericalError):
        equilibrium(r,l,k)
