import copy
import csv
import io
import json
import random
import subprocess
import sys
import pytest
from free_dose_check import analyze, dumps, to_csv, ValidationError
from free_dose_check.model import equilibrium, site_concentration


def test_full_reference(config):
    report = analyze(config)
    assert report["depletion_assessment"] == "exceeds_tolerance"
    assert report["model_applicability"] == "supported_under_declared_assumptions"
    assert report["doses"][0]["depletion"] is None
    assert report["doses"][0]["assessment"] == "not_applicable"
    assert report["doses"][2]["occupancy_error_pp"]["low"] == pytest.approx(18.051307526826527)
    assert report["model_implied_half_occupancy_nM"]["low"] == pytest.approx(.18302695335869235)
    assert report["half_occupancy_fold_over_kd"]["low"] == pytest.approx(1.8302695335869235)
    rec = report["recommendations"]
    assert rec["minimum_volume_uL"] == pytest.approx(1371.0873031710657)
    assert rec["maximum_cells"] == pytest.approx(7293.481587111113)
    assert rec["volume_option"]["volume_uL"] == 1371.088
    assert rec["cell_option"]["cell_count"] == 7293
    assert rec["volume_option"]["forward_verified"]
    assert rec["cell_option"]["forward_verified"]
    assert rec["status"] == "no_one_variable_solution_within_supplied_constraints"


def test_bounds_enclose_interior(config):
    config["sites_per_cell"] = {"low": 10000, "high": 200000}
    config["kd_nM"] = {"low": .05, "high": .2}
    report = analyze(config)
    assert report["bounded_inputs"]
    assert report["doses"][1]["assessment"] == "crosses_tolerance"
    rng = random.Random(33)
    for _ in range(1000):
        sites, kd = rng.uniform(10000,200000), rng.uniform(.05,.2)
        for row in report["doses"][1:]:
            s = equilibrium(site_concentration(100000,sites,100),row["ligand_total_nM"],kd)
            for metric in s:
                assert row[metric]["low"] - 1e-12 <= s[metric] <= row[metric]["high"] + 1e-12
    assert report["recommendations"]["minimum_volume_uL"] == pytest.approx(5066.051391377836)
    assert report["recommendations"]["cell_option"]["cell_count"] == 1973
    # Exported bounds have no implicit midpoint.
    assert "nominal" not in dumps(report)


def test_overall_crossing_and_within(config):
    config["sites_per_cell"] = {"low": 1000, "high": 100000}
    assert analyze(config)["depletion_assessment"] == "crosses_tolerance"
    config["cell_count"] = 1000
    report = analyze(config)
    assert report["depletion_assessment"] == "within_tolerance"
    assert report["recommendations"]["volume_option"]["volume_uL"] == config["volume_uL"]
    assert report["recommendations"]["cell_option"]["cell_count"] == config["cell_count"]


def test_assumption_gate_all_exports(config):
    config["assumptions"]["equilibrium"]["status"] = "uncertain"
    assert analyze(config)["model_applicability"] == "assumption_check_required"
    config["assumptions"]["closed_system"]["status"] = "unsupported"
    report = analyze(config)
    assert report["model_applicability"] == "unsupported_model"
    assert report["recommendations"]["volume_option"] is None
    assert report["recommendations"]["cell_option"] is None
    rows = list(csv.DictReader(io.StringIO(to_csv(report))))
    assert all(x["model_applicability"] == "unsupported_model" for x in rows)
    meta = json.loads(rows[0]["metadata_json"])
    assert meta["recommendations"]["status"] == "suppressed"
    assert meta["inputs"]["assumptions"]["closed_system"]["status"] == "unsupported"


def test_affinity_and_valency_gate(config):
    config["provenance"]["kd_nM"]["basis"] = "possibly_depleted"
    assert analyze(config)["model_applicability"] == "assumption_check_required"
    config["provenance"]["kd_nM"]["basis"] = "functional"
    with pytest.raises(ValidationError, match="Functional"):
        analyze(config)
    config["provenance"]["kd_nM"]["basis"] = "independent"
    config["ligand_format"] = "bivalent"
    assert analyze(config)["recommendations"]["status"] == "suppressed"
    config["ligand_format"] = "effective_1to1"
    assert analyze(config)["model_applicability"] == "assumption_check_required"
    config["effective_1to1_justification"] = "Declared hypothetical justification"
    assert analyze(config)["model_applicability"] == "supported_under_declared_assumptions"


@pytest.mark.parametrize("key,value", [
    ("cell_count", 0), ("cell_count", 1.3), ("cell_count", True),
    ("cell_count", 2**54), ("volume_uL", float("inf")), ("kd_nM", float("nan")),
    ("kd_nM", 0), ("kd_nM", 1e-14), ("sites_per_cell", {"low": 4, "high": 2}),
    ("sites_per_cell", {"low": 4}), ("ligand_total_nM", [0]), ("ligand_total_nM", []),
    ("ligand_total_nM", [1,1]), ("ligand_total_nM", [-1,1]), ("ligand_total_nM", [1e13]),
    ("depletion_tolerance", 0), ("depletion_tolerance", 1), ("min_cells", 1.5),
    ("provenance", {}), ("assumptions", {}), ("cell_cout", 100),
])
def test_invalid(config, key, value):
    config[key] = value
    with pytest.raises(ValidationError):
        analyze(config)


def test_constraint_fixed_variable_and_missing(config):
    config["max_volume_uL"] = 50
    # Even the cell-only option violates fixed volume's supplied constraint.
    assert not analyze(config)["recommendations"]["cell_option"]["feasible_with_supplied_constraints"]
    config.pop("max_volume_uL")
    config.pop("min_cells")
    rec = analyze(config)["recommendations"]
    assert rec["status"] == "operational_feasibility_not_assessed"
    assert rec["volume_option"]["feasible_with_supplied_constraints"] is None


def test_random_recommendation_forward_checks(config):
    rng = random.Random(73)
    config.pop("max_volume_uL")
    config.pop("min_cells")
    for _ in range(500):
        config["cell_count"] = rng.randint(1000,1000000)
        config["sites_per_cell"] = 10**rng.uniform(3,6)
        config["kd_nM"] = 10**rng.uniform(-2,1)
        config["volume_uL"] = rng.uniform(50,200)
        config["depletion_tolerance"] = rng.uniform(.01,.3)
        rec = analyze(config)["recommendations"]
        assert rec["volume_option"]["forward_verified"]
        assert rec["volume_option"]["worst_depletion"] <= config["depletion_tolerance"]*(1+1e-10)
        if rec["cell_option"]["cell_count"] > 0:
            assert rec["cell_option"]["forward_verified"]


def test_deterministic_roundtrip_and_cli(config, tmp_path):
    expected = analyze(config)
    assert dumps(expected) == dumps(analyze(expected["inputs"]))
    path, result, csvpath = tmp_path/"config.json", tmp_path/"report.json", tmp_path/"doses.csv"
    path.write_text(json.dumps(config))
    proc = subprocess.run([sys.executable, "-m", "free_dose_check", "analyze", str(path),
                           "--json", str(result), "--csv", str(csvpath)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(result.read_text()) == expected
    assert len(list(csv.DictReader(io.StringIO(csvpath.read_text())))) == 5
    path.write_text('{"wrong":true}')
    proc = subprocess.run([sys.executable, "-m", "free_dose_check", "analyze", str(path)], capture_output=True, text=True)
    assert proc.returncode == 2
    assert json.loads(proc.stderr)["error"] == "ValidationError"


def test_unsupported_roundtrip_independent_of_input_key_order(config):
    config["assumptions"]["closed_system"]["status"] = "unsupported"
    config["assumptions"]["independent_sites"]["status"] = "unsupported"
    expected = analyze(config)
    reparsed = json.loads(dumps(expected))
    assert dumps(expected) == dumps(analyze(reparsed["inputs"]))


def test_unrepresentably_small_design_capacity(config):
    config["depletion_tolerance"] = 1e-320
    report = analyze(config)
    assert report["recommendations"]["status"] == "numerical_domain_limit"
    assert report["recommendations"]["volume_option"] is None
