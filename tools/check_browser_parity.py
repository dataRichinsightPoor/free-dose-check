"""Compare generated browser QA outputs against native Python, including CSV metadata.

Usage: python tools/check_browser_parity.py /path/to/browser-qa
"""
import csv
import json
import math
import sys
from pathlib import Path
from free_dose_check import analyze


def compare(actual, expected, path="root"):
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys(), path
        for key in expected:
            compare(actual[key], expected[key], path + "." + key)
    elif isinstance(expected, list):
        assert len(actual) == len(expected), path
        for i, (a, e) in enumerate(zip(actual, expected)):
            compare(a, e, path + "." + str(i))
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=0), (path, actual, expected)
    else:
        assert actual == expected, (path, actual, expected)


if __name__ == "__main__":
    folder = Path(sys.argv[1])
    files = list(folder.glob("*-browser.json")) + list(folder.glob("*-export.json"))
    assert files, "No browser reports found."
    for path in files:
        report = json.loads(path.read_text())
        compare(report, analyze(report["inputs"]))
        print(f"PASS native/browser parity: {path.name}")
    with (folder / "browser-export.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 5
    metadata = json.loads(rows[0]["metadata_json"])
    baseline = analyze(metadata["inputs"])
    compare(metadata, {k:v for k,v in baseline.items() if k != "doses"})
    for row, dose in zip(rows, baseline["doses"]):
        assert row["assessment"] == dose["assessment"]
        for metric in ("free_nM","bound_nM","depletion","occupancy","naive_occupancy","occupancy_error_pp"):
            for bound in ("low","high"):
                v = row[f"{metric}_{bound}"]
                assert v == "" if dose[metric] is None else math.isclose(float(v),dose[metric][bound],rel_tol=1e-12,abs_tol=0)
    print("PASS CSV values and complete embedded metadata.")
