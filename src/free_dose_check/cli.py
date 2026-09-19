import argparse
import json
import sys
from pathlib import Path
from .report import analyze, dumps, to_csv
from .schema import ValidationError
from .model import NumericalError


def main(argv=None):
    parser = argparse.ArgumentParser(description="Free-Dose Check: research-use finite-bath binding design.")
    parser.add_argument("--version", action="version", version="0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("analyze", help="Analyze a JSON configuration.")
    run.add_argument("config")
    run.add_argument("--json", dest="json_path")
    run.add_argument("--csv", dest="csv_path")
    args = parser.parse_args(argv)
    try:
        report = analyze(json.loads(Path(args.config).read_text()))
        if args.json_path:
            Path(args.json_path).write_text(dumps(report))
        else:
            print(dumps(report), end="")
        if args.csv_path:
            Path(args.csv_path).write_text(to_csv(report))
    except (ValidationError, NumericalError, ValueError, OSError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, allow_nan=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
