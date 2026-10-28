# TracePilot
Local-first comparison of JUnit XML test reports. Detect regressions, track resolved failures, group matching error signatures, and produce HTML and JSON evidence.
## Requirements
- Python 3.10 or newer
- JUnit XML reports from your test runner
## Run automated tests
```powershell
python -m unittest discover -s tests -v
```
## Compare two reports
```powershell
$env:PYTHONPATH = "$PWD\src"
python -m tracepilot .\baseline.xml .\current.xml --out .\tracepilot-report.html
```
## Generate HTML and machine-readable JSON
```powershell
python -m tracepilot .\baseline.xml .\current.xml `
  --out .\tracepilot-report.html `
  --json-out .\tracepilot-results.json
```
## Use a CI regression gate
Fail only when new failures appear:
```powershell
python -m tracepilot .\baseline.xml .\current.xml --fail-on new
```
Fail when new or persistent failures exist:
```powershell
python -m tracepilot .\baseline.xml .\current.xml --fail-on any
```
## Exit codes
- `0`: comparison completed and the selected gate passed
- `1`: selected regression gate failed
- `2`: input or report-generation error
## Important
The reports must come from actual test runs for meaningful results. TracePilot compares test identities and failure evidence; matching signatures are clues, not proof of a shared root cause.
