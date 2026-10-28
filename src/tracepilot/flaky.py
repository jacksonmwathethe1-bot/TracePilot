import argparse
import html
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
def load_outcomes(report_path):
    """Return test identity -> outcome for a single JUnit XML report."""
    path = Path(report_path)
    if not path.is_file():
        raise FileNotFoundError(f"JUnit report not found: {path}")
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        raise ValueError(f"Could not read JUnit XML '{path}': {exc}") from exc
    outcomes = {}
    for case in root.iter():
        if case.tag.split("}")[-1] != "testcase":
            continue
        name = case.attrib.get("name", "").strip()
        if not name:
            continue
        classname = case.attrib.get("classname", "").strip()
        identity = f"{classname}::{name}" if classname else name
        children = {child.tag.split("}")[-1] for child in case}
        if "failure" in children or "error" in children:
            outcome = "fail"
        elif "skipped" in children:
            outcome = "skipped"
        else:
            outcome = "pass"
        # If duplicate identities occur in one report, failure takes priority.
        previous = outcomes.get(identity)
        if previous is None or outcome == "fail":
            outcomes[identity] = outcome
        elif previous == "skipped" and outcome == "pass":
            outcomes[identity] = outcome
    if not outcomes:
        raise ValueError(f"No testcase elements found in JUnit report: {path}")
    return outcomes
def analyze_reports(report_paths):
    """Analyze the same test identities across multiple JUnit reports."""
    if len(report_paths) < 2:
        raise ValueError("Provide at least two JUnit XML reports.")
    counts = defaultdict(lambda: {
        "passes": 0, "failures": 0, "skipped": 0, "reports": 0
    })
    for report_path in report_paths:
        outcomes = load_outcomes(report_path)
        for identity, outcome in outcomes.items():
            item = counts[identity]
            item["reports"] += 1
            if outcome == "pass":
                item["passes"] += 1
            elif outcome == "fail":
                item["failures"] += 1
            else:
                item["skipped"] += 1
    results = []
    for identity, item in sorted(counts.items()):
        passes = item["passes"]
        failures = item["failures"]
        executed = passes + failures
        if passes and failures:
            status = "FLAKY"
        elif failures:
            status = "CONSISTENTLY FAILING"
        elif passes:
            status = "PASSING"
        else:
            status = "SKIPPED ONLY"
        results.append({
            "test": identity,
            **item,
            "executed": executed,
            "failure_rate": round(failures / executed * 100, 1)
            if executed else None,
            "status": status,
        })
    return {
        "reports_analyzed": len(report_paths),
        "tests_found": len(results),
        "flaky": sum(r["status"] == "FLAKY" for r in results),
        "consistently_failing": sum(
            r["status"] == "CONSISTENTLY FAILING" for r in results
        ),
        "passing": sum(r["status"] == "PASSING" for r in results),
        "skipped_only": sum(r["status"] == "SKIPPED ONLY" for r in results),
        "results": results,
        "report_paths": [str(Path(p)) for p in report_paths],
    }
def render_flaky_report(analysis, output_path):
    rows = []
    for item in analysis["results"]:
        rate = (
            f'{item["failure_rate"]:.1f}%'
            if item["failure_rate"] is not None else "N/A"
        )
        rows.append(
            "<tr>"
            f'<td>{html.escape(item["test"])}</td>'
            f'<td>{html.escape(item["status"])}</td>'
            f'<td>{item["passes"]}</td>'
            f'<td>{item["failures"]}</td>'
            f'<td>{item["skipped"]}</td>'
            f'<td>{rate}</td>'
            f'<td>{item["reports"]}</td>'
            "</tr>"
        )
    table_rows = "\n".join(rows) or (
        '<tr><td colspan="7">No tests found.</td></tr>'
    )
    report_names = "".join(
        f"<li>{html.escape(p)}</li>" for p in analysis["report_paths"]
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TracePilot — Flaky Test Analysis</title>
<style>
:root {{ color-scheme: dark; --bg:#10101a; --panel:#191927;
--line:#303047; --text:#f3f2ff; --muted:#aaa8c2; --accent:#a78bfa; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; padding:32px; background:var(--bg); color:var(--text);
font:15px/1.5 "Segoe UI",sans-serif; }}
main {{ max-width:1200px; margin:auto; }}
h1 {{ margin-bottom:4px; }} p, .muted {{ color:var(--muted); }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
gap:12px; margin:24px 0; }}
.card {{ background:var(--panel); border:1px solid var(--line);
border-radius:12px; padding:18px; }}
.number {{ font-size:30px; font-weight:700; color:var(--accent); }}
.card small {{ color:var(--muted); }}
input {{ width:100%; padding:12px; border-radius:8px;
border:1px solid var(--line); background:var(--panel); color:var(--text);
margin:8px 0 16px; }}
.table-wrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:10px; }}
table {{ width:100%; border-collapse:collapse; min-width:760px; }}
th,td {{ padding:12px; border-bottom:1px solid var(--line);
text-align:left; overflow-wrap:anywhere; }}
th {{ background:var(--panel); color:var(--muted); }}
tr:last-child td {{ border-bottom:0; }}
.status {{ font-weight:700; color:var(--accent); }}
details {{ margin-top:24px; background:var(--panel); padding:16px; border-radius:10px; }}
li {{ overflow-wrap:anywhere; margin:6px 0; }}
footer {{ margin-top:28px; color:var(--muted); font-size:13px; }}
</style>
</head>
<body><main>
<h1>TracePilot <span style="color:var(--accent)">/</span> Flaky Test Analysis</h1>
<p>Repeated JUnit outcomes, analyzed locally.</p>
<div class="cards">
<div class="card"><small>Reports analyzed</small><div class="number">{analysis["reports_analyzed"]}</div></div>
<div class="card"><small>Tests identified</small><div class="number">{analysis["tests_found"]}</div></div>
<div class="card"><small>Flaky tests</small><div class="number">{analysis["flaky"]}</div></div>
<div class="card"><small>Consistently failing</small><div class="number">{analysis["consistently_failing"]}</div></div>
<div class="card"><small>Passing</small><div class="number">{analysis["passing"]}</div></div>
</div>
<label for="search">Search test names or status</label>
<input id="search" type="search" placeholder="Search tests...">
<div class="table-wrap"><table id="results">
<thead><tr><th>Test</th><th>Status</th><th>Passes</th><th>Failures</th>
<th>Skipped</th><th>Failure rate</th><th>Reports seen</th></tr></thead>
<tbody>{table_rows}</tbody>
</table></div>
<details><summary>Input reports</summary><ul>{report_names}</ul></details>
<footer>Flaky means at least one pass and one failure were observed for the same test identity.
Skipped outcomes are excluded from the failure-rate calculation. Missing tests are not assumed to have passed.</footer>
</main>
<script>
document.getElementById('search').addEventListener('input', function() {{
 const q = this.value.toLowerCase();
 document.querySelectorAll('#results tbody tr').forEach(row => {{
  row.hidden = !row.textContent.toLowerCase().includes(q);
 }});
}});
</script>
</body></html>"""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding="utf-8")
    return destination
def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="TracePilot flaky",
        description="Detect inconsistent outcomes across JUnit XML reports."
    )
    parser.add_argument("reports", nargs="+", help="JUnit XML reports, in run order")
    parser.add_argument("--out", default="tracepilot-flaky-report.html")
    args = parser.parse_args(argv)
    try:
        analysis = analyze_reports(args.reports)
        output = render_flaky_report(analysis, args.out)
    except (ValueError, OSError) as exc:
        print(f"TracePilot flaky analysis error: {exc}", file=sys.stderr)
        return 2
    print("\nTracePilot flaky-test analysis")
    print("=" * 36)
    print(f"Reports analyzed:      {analysis['reports_analyzed']}")
    print(f"Tests identified:      {analysis['tests_found']}")
    print(f"Flaky tests:           {analysis['flaky']}")
    print(f"Consistently failing:  {analysis['consistently_failing']}")
    print(f"Passing:               {analysis['passing']}")
    print(f"Skipped only:          {analysis['skipped_only']}")
    print(f"HTML report:           {output.resolve()}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
