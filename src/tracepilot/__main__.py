import argparse
import json
import sys
from pathlib import Path
from tracepilot.core import load_report, compare_reports
from tracepilot.report import render_report
from tracepilot.history import DEFAULT_DB, save_run, list_runs
def main():
    parser = argparse.ArgumentParser(
        prog="TracePilot",
        description="Compare JUnit reports and maintain local history."
    )
    parser.add_argument("baseline", nargs="?")
    parser.add_argument("current", nargs="?")
    parser.add_argument("--out", default="tracepilot-report.html")
    parser.add_argument("--json-out")
    parser.add_argument("--fail-on", choices=("none", "new", "any"), default="none")
    parser.add_argument("--history-db", default=DEFAULT_DB)
    parser.add_argument("--show-history", action="store_true")
    parser.add_argument("--history-limit", type=int, default=20)
    parser.add_argument("--no-save-history", action="store_true")
    args = parser.parse_intermixed_args()
    if args.show_history:
        try:
            runs = list_runs(args.history_db, args.history_limit)
            if not runs:
                print("No saved comparison runs yet.")
            else:
                print(f"\nTracePilot history: {len(runs)} run(s)")
                print("=" * 85)
                for run in runs:
                    s = run["summary"]
                    print(
                        f"#{run['id']} | {run['created_at']} | {run['current']} | "
                        f"new: {s.get('new_failures', 0)} | "
                        f"persistent: {s.get('persistent_failures', 0)} | "
                        f"resolved: {s.get('resolved_failures', 0)}"
                    )
            return 0
        except Exception as exc:
            print(f"History error: {exc}", file=sys.stderr)
            return 2
    if not args.baseline or not args.current:
        parser.error("Provide baseline and current XML reports, or use --show-history.")
    try:
        result = compare_reports(
            load_report(args.baseline),
            load_report(args.current)
        )
        html_path = render_report(result, args.out)
        if args.json_out:
            json_path = Path(args.json_out)
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(
                json.dumps(result, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        run_id = None
        if not args.no_save_history:
            run_id = save_run(result, args.history_db)
    except Exception as exc:
        print(f"TracePilot input/report error: {exc}", file=sys.stderr)
        return 2
    s = result["summary"]
    print("\nTracePilot comparison")
    print("=" * 38)
    print(f"Baseline:          {result['baseline']} ({result['baseline_total']} tests)")
    print(f"Current:           {result['current']} ({result['current_total']} tests)")
    print(f"New failures:      {s['new_failures']}")
    print(f"Persistent:        {s['persistent_failures']}")
    print(f"Resolved:          {s['resolved_failures']}")
    print(f"New tests:         {s['new_tests']}")
    print(f"Removed tests:     {s['removed_tests']}")
    print(f"Failure groups:    {s['failure_groups']}")
    print(f"HTML report:       {Path(html_path).resolve()}")
    if args.json_out:
        print(f"JSON results:      {Path(args.json_out).resolve()}")
    if run_id is not None:
        print(f"Saved history run: #{run_id}")
    failed = (
        args.fail_on == "new" and s["new_failures"] > 0
    ) or (
        args.fail_on == "any" and (
            s["new_failures"] > 0 or s["persistent_failures"] > 0
        )
    )
    if failed:
        print(f"CI GATE: FAILED (--fail-on {args.fail_on})", file=sys.stderr)
        return 1
    print(f"CI GATE: PASSED (--fail-on {args.fail_on})")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())


