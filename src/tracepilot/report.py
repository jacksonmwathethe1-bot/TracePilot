import csv
import io
import json
from html import escape
from pathlib import Path
def render_report(result: dict, output_path: str | Path) -> Path:
    """Generate a standalone interactive TracePilot HTML report."""
    output_path = Path(output_path)
    categories = [
        ("new_failures", "New failures", "new"),
        ("persistent_failures", "Persistent failures", "persistent"),
        ("resolved_failures", "Resolved failures", "resolved"),
        ("new_tests", "New tests", "new-test"),
        ("removed_tests", "Removed tests", "removed"),
    ]
    all_tests = []
    for key, label, category in categories:
        for test in result.get(key, []):
            item = dict(test)
            item["category"] = category
            item["categoryLabel"] = label
            all_tests.append(item)
    groups = []
    for group in result.get("failure_groups", []):
        groups.append({
            "signature": group["signature"],
            "tests": group["tests"],
            "count": len(group["tests"]),
        })
    payload = json.dumps({
        "tests": all_tests,
        "groups": groups,
        "summary": result.get("summary", {}),
        "baseline": result.get("baseline", ""),
        "current": result.get("current", ""),
        "baselineTotal": result.get("baseline_total", 0),
        "currentTotal": result.get("current_total", 0),
    }, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    template = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>TracePilot | Test Intelligence</title>
<style>
:root {
  --bg:#0b1018; --panel:#111a26; --panel2:#162231; --line:#263648;
  --text:#edf4fc; --muted:#92a4b9; --teal:#54e1c1; --blue:#7caeff;
  --red:#ff7f88; --amber:#ffd27a; --green:#74e0a1;
}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at 15% -10%,#183044 0,transparent 38%),var(--bg);color:var(--text);font:14px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
button,input{font:inherit}
button{cursor:pointer}
button:focus-visible,input:focus-visible{outline:2px solid var(--teal);outline-offset:3px}
.shell{max-width:1450px;margin:auto;padding:30px clamp(16px,4vw,54px) 60px}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;padding-bottom:25px;border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:12px}
.mark{width:42px;height:42px;display:grid;place-items:center;border:1px solid #3b786f;border-radius:13px;background:linear-gradient(145deg,#193d42,#12222d);color:var(--teal);font-weight:900;font-size:20px}
.brand-name{font-size:19px;font-weight:800;letter-spacing:-.6px}
.brand-sub{font-size:12px;color:var(--muted)}
.local-pill{display:flex;align-items:center;gap:8px;border:1px solid var(--line);background:#111b27;padding:8px 12px;border-radius:999px;color:#b7c8da;font-size:12px}
.dot{width:7px;height:7px;border-radius:50%;background:var(--teal);box-shadow:0 0 12px #54e1c166}
.hero{padding:36px 0 25px;display:flex;align-items:flex-end;justify-content:space-between;gap:22px;flex-wrap:wrap}
.eyebrow{text-transform:uppercase;letter-spacing:2px;color:var(--teal);font-size:10px;font-weight:800}
h1{font-size:clamp(30px,4vw,46px);letter-spacing:-1.7px;line-height:1.1;margin:9px 0 12px}
.subtitle{color:var(--muted);margin:0;max-width:680px}
.actions{display:flex;gap:9px;flex-wrap:wrap}
.btn{border:1px solid var(--line);background:#152130;color:var(--text);padding:10px 14px;border-radius:10px;font-weight:700;font-size:12px}
.btn:hover{border-color:#4d7183;background:#1a2b3d}
.btn.primary{background:var(--teal);color:#09201e;border-color:var(--teal)}
.btn.primary:hover{background:#8af2db}
.runbar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:15px 17px;border:1px solid var(--line);border-radius:14px;background:#101a26;margin:10px 0 20px}
.run{min-width:0;flex:1}
.run-label{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:1.3px}
.run-name{font-weight:650;overflow-wrap:anywhere;margin-top:3px}
.arrow{color:var(--teal);font-size:18px}
.stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:18px 0 26px}
.stat{position:relative;overflow:hidden;padding:18px;border:1px solid var(--line);background:linear-gradient(145deg,#152130,#101823);border-radius:15px;min-height:120px}
.stat:before{content:"";position:absolute;top:0;left:18px;right:18px;height:2px;background:var(--accent,var(--teal));opacity:.8}
.stat-label{font-size:12px;color:var(--muted)}
.stat-number{font-size:33px;font-weight:800;letter-spacing:-1px;margin-top:7px}
.stat-note{font-size:11px;color:var(--muted);margin-top:2px}
.stat.red{--accent:var(--red)}.stat.amber{--accent:var(--amber)}.stat.green{--accent:var(--green)}.stat.blue{--accent:var(--blue)}
.section-head{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin:27px 0 14px;flex-wrap:wrap}
h2{font-size:17px;letter-spacing:-.35px;margin:0}
.mini{font-size:12px;color:var(--muted);margin-top:4px}
.workspace{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:16px;align-items:start}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;overflow:hidden;min-width:0}
.panel-head{padding:17px 18px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.panel-title{font-size:14px;font-weight:800}
.search{width:min(100%,300px);background:#0c141f;border:1px solid var(--line);color:var(--text);padding:10px 12px;border-radius:9px}
.search::placeholder{color:#657b91}
.filters{display:flex;gap:6px;flex-wrap:wrap;padding:13px 16px;border-bottom:1px solid var(--line)}
.filter{background:transparent;border:1px solid transparent;color:var(--muted);padding:7px 10px;border-radius:8px;font-size:11px;font-weight:750}
.filter:hover{background:var(--panel2);color:var(--text)}
.filter.active{background:#1b3438;border-color:#2d625a;color:var(--teal)}
.results{padding:5px 15px 15px}
.test{border-bottom:1px solid #223142;padding:14px 3px}
.test:last-child{border-bottom:0}
.test-top{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.test-name{font-weight:750;overflow-wrap:anywhere}
.test-class{font-size:11px;color:var(--muted);margin-top:3px;overflow-wrap:anywhere}
.tag{display:inline-flex;align-items:center;white-space:nowrap;border-radius:6px;padding:4px 7px;font-size:10px;font-weight:800;border:1px solid transparent}
.tag.new{background:#42232b;color:var(--red);border-color:#66333d}
.tag.persistent{background:#3d3020;color:var(--amber);border-color:#63502e}
.tag.resolved{background:#17392f;color:var(--green);border-color:#285c49}
.tag.new-test{background:#1c3047;color:var(--blue);border-color:#314f70}
.tag.removed{background:#292b3c;color:#c2bcff;border-color:#454562}
.error{margin-top:10px;background:#0b131d;border:1px solid #243447;border-radius:9px;padding:10px 12px;color:#ffb5b9;font:12px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere}
.test details{margin-top:9px}
.test summary{font-size:11px;color:var(--muted);cursor:pointer}
.detail{margin-top:8px;color:#b5c5d7;font:11px/1.6 ui-monospace,SFMono-Regular,Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere}
.empty{padding:34px 15px;text-align:center;color:var(--muted)}
.side{display:grid;gap:14px}
.side .panel{padding:17px}
.side h3{font-size:13px;margin:0 0 5px}
.group{padding:12px 0;border-bottom:1px solid #243244}
.group:last-child{border-bottom:0}
.group-head{display:flex;justify-content:space-between;gap:8px;align-items:center}
.count{color:var(--teal);font-size:11px;font-weight:800}
.sig{font:10px ui-monospace,Consolas,monospace;color:var(--muted);overflow-wrap:anywhere;margin-top:7px}
.group ul{padding-left:17px;margin:8px 0 0;color:#c3d1e1;font-size:11px}
.group li{margin:4px 0;overflow-wrap:anywhere}
.insight{font-size:12px;color:#b6c7d9;margin:10px 0 0}
.footer{padding-top:24px;color:#64788f;font-size:11px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.hidden{display:none!important}
@media(max-width:1050px){.stats{grid-template-columns:repeat(3,minmax(0,1fr))}.workspace{grid-template-columns:1fr}.side{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:620px){.shell{padding-top:18px}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.stat:last-child{grid-column:span 2}.side{grid-template-columns:1fr}.hero{padding-top:25px}.runbar{align-items:flex-start}.arrow{display:none}}
/* TracePilot Violet Design System — inspired by SnapSplit */
:root {
  --bg:#0d0b14;
  --panel:#17131f;
  --panel2:#21182e;
  --line:#302538;
  --text:#f7f3ff;
  --muted:#9991ae;
  --teal:#b16cff;
  --blue:#c3a0ff;
  --red:#ff719e;
  --amber:#ffc16e;
  --green:#5be0c0;
}
body {
  background:
    radial-gradient(ellipse at 12% 0%,#291b42 0,transparent 35%),
    radial-gradient(ellipse at 90% 35%,#211326 0,transparent 30%),
    var(--bg);
  color:var(--text);
}
.shell {max-width:1540px;padding-top:24px}
.topbar {border-bottom-color:#292132;padding-bottom:20px}
.mark {
  background:linear-gradient(140deg,#9855f5,#c065df);
  border:0;border-radius:13px;color:white;
  box-shadow:0 7px 25px #a04cff35;
}
.brand-name {letter-spacing:-.7px}
.brand-sub {color:#a49ab9}
.local-pill {
  background:#191420;border-color:#35263e;color:#c8bdd9;
}
.dot {
  background:#bd79ff;
  box-shadow:0 0 13px #a85cff85;
}
.eyebrow {color:#c18aff}
h1 {letter-spacing:-1.8px}
.subtitle {color:#a39ab5}
.btn {
  border-color:#382a45;background:#1b1524;
  border-radius:11px;transition:all .18s ease;
}
.btn:hover {
  border-color:#a66af5;
  box-shadow:0 0 18px #9d55ed18;
  transform:translateY(-1px);
}
.btn.primary {
  background:linear-gradient(115deg,#8f5cf6,#c05cdb);
  border-color:transparent;color:white;
  box-shadow:0 7px 22px #a04cff30;
}
.btn.primary:hover {
  background:linear-gradient(115deg,#a476ff,#d374eb);
  box-shadow:0 9px 27px #a04cff45;
}
.runbar {
  background:linear-gradient(115deg,#191322,#17121d);
  border-color:#33243e;border-radius:17px;
}
.arrow {color:#c18aff}
.stats {gap:14px}
.stat {
  background:linear-gradient(135deg,#1c1727,#17131f);
  border-color:#30243a;border-radius:18px;
  min-height:124px;transition:transform .18s,border-color .18s;
}
.stat:hover {transform:translateY(-2px);border-color:#62427b}
.stat:before {
  height:3px;left:20px;right:20px;
  background:linear-gradient(90deg,#8957f5,#d05fda);
  border-radius:99px;
}
.stat.red:before {background:linear-gradient(90deg,#fa668e,#ff9caa)}
.stat.amber:before {background:linear-gradient(90deg,#f3a34e,#ffd27a)}
.stat.green:before {background:linear-gradient(90deg,#12bfae,#65e3c1)}
.stat.blue:before {background:linear-gradient(90deg,#8660fa,#c59aff)}
.stat-label {color:#a49ab7}
.stat-number {letter-spacing:-1.2px}
.panel {
  background:linear-gradient(145deg,#191420,#15111b);
  border-color:#302438;border-radius:18px;
}
.panel-head {border-bottom-color:#302438}
.search {
  background:#100d16;border-color:#382941;border-radius:11px;
}
.search:focus {border-color:#a56af4}
.filters {border-bottom-color:#302438}
.filter {border-radius:9px}
.filter.active {
  background:linear-gradient(110deg,#6536a7,#8c42a8);
  border-color:#a766e8;color:white;
  box-shadow:0 4px 14px #9b4fce25;
}
.filter:hover {background:#2b2038;color:#fff}
.test {border-bottom-color:#302438}
.error {
  background:#100d16;border-color:#39283b;
  border-radius:11px;color:#ff9fb6;
}
.group {border-bottom-color:#302438}
.count {color:#c28aff}
.sig {color:#a49ab7}
.footer {color:#766b89}
@media(prefers-reduced-motion:reduce) {
  *,*::before,*::after {transition:none!important;scroll-behavior:auto!important}
}
</style>
</head>
<body>
<div class="shell">
<header class="topbar">
  <div class="brand"><div class="mark">T.</div><div><div class="brand-name">TracePilot</div><div class="brand-sub">Test intelligence · Local report</div></div></div>
  <div class="local-pill"><span class="dot"></span> Standalone report · No account required</div>
</header>
<section class="hero">
  <div><div class="eyebrow">Comparison workspace</div><h1>Know what changed.</h1><p class="subtitle">A focused view of test regressions, persistent failures, and resolved issues across two test runs.</p></div>
  <div class="actions"><button class="btn" id="exportCsv">Export CSV ↓</button><button class="btn primary" id="exportJson">Export JSON ↓</button></div>
</section>
<div class="runbar">
  <div class="run"><div class="run-label">Baseline · Earlier run</div><div class="run-name" id="baselineName"></div></div>
  <div class="arrow">→</div>
  <div class="run"><div class="run-label">Current · Latest run</div><div class="run-name" id="currentName"></div></div>
  <div class="local-pill" id="runCount"></div>
</div>
<div class="stats" id="stats"></div>
<div class="section-head"><div><h2>Failure investigation</h2><div class="mini">Search, filter, inspect details, and export the evidence.</div></div><div class="mini" id="resultCount"></div></div>
<div class="workspace">
  <section class="panel">
    <div class="panel-head"><div class="panel-title">Test changes</div><input class="search" id="search" type="search" placeholder="Search tests, classes, errors…"></div>
    <div class="filters" id="filters"></div>
    <div class="results" id="results"></div>
  </section>
  <aside class="side">
    <section class="panel"><h3>Failure signature groups</h3><div class="mini">Matching normalized error signatures, not guaranteed root causes.</div><div id="groups"></div></section>
    <section class="panel"><h3>Comparison notes</h3><p class="insight" id="insight"></p><p class="insight">A new failure means a test passed in the baseline but failed now, or is newly introduced and failing.</p><p class="insight">Validate each suspected cause against the source code and test output before changing code.</p></section>
  </aside>
</div>
<footer class="footer"><span>TracePilot · Local-first test comparison</span><span>Report generated from supplied JUnit XML · Review evidence before acting</span></footer>
</div>
<script>
const DATA = __DATA__;
const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const number = value => Number(value || 0);
const filters = [
  ["all","All changes"],
  ["new","New failures"],
  ["persistent","Persistent"],
  ["resolved","Resolved"],
  ["new-test","New tests"],
  ["removed","Removed"]
];
let activeFilter = "all";
const search = document.getElementById("search");
document.getElementById("baselineName").textContent = DATA.baseline;
document.getElementById("currentName").textContent = DATA.current;
document.getElementById("runCount").textContent = `${DATA.baselineTotal} → ${DATA.currentTotal} tests`;
const stats = [
  ["New failures", "new_failures", "red", "Require attention"],
  ["Persistent", "persistent_failures", "amber", "Still failing"],
  ["Resolved", "resolved_failures", "green", "Now passing"],
  ["New tests", "new_tests", "blue", "Added to current run"],
  ["Failure groups", "failure_groups", "", "Distinct signatures"]
];
document.getElementById("stats").innerHTML = stats.map(([label,key,tone,note]) =>
  `<article class="stat ${tone}"><div class="stat-label">${label}</div><div class="stat-number">${number(DATA.summary[key])}</div><div class="stat-note">${note}</div></article>`
).join("");
document.getElementById("filters").innerHTML = filters.map(([key,label]) =>
  `<button class="filter ${key === activeFilter ? "active" : ""}" data-filter="${key}">${label}</button>`
).join("");
function visibleTests() {
  const q = search.value.trim().toLowerCase();
  return DATA.tests.filter(test => {
    const matchesFilter = activeFilter === "all" || test.category === activeFilter;
    const haystack = [test.key,test.name,test.classname,test.message,test.detail,test.categoryLabel].join(" ").toLowerCase();
    return matchesFilter && (!q || haystack.includes(q));
  });
}
function renderTests() {
  const list = visibleTests();
  document.getElementById("resultCount").textContent = `${list.length} of ${DATA.tests.length} changes`;
  if (!list.length) {
    document.getElementById("results").innerHTML = `<div class="empty">No matching results.<br><span class="mini">Try another filter or search term.</span></div>`;
    return;
  }
  document.getElementById("results").innerHTML = list.map(test => {
    const error = test.message || (test.status === "failed" ? "Failure details not provided" : "");
    const detail = test.detail || "";
    return `<article class="test">
      <div class="test-top"><div><div class="test-name">${escapeHtml(test.name)}</div><div class="test-class">${escapeHtml(test.classname || test.key)}</div></div><span class="tag ${escapeHtml(test.category)}">${escapeHtml(test.categoryLabel)}</span></div>
      ${error ? `<div class="error">${escapeHtml(error)}</div>` : ""}
      ${detail && detail !== error ? `<details><summary>Inspect full error output</summary><div class="detail">${escapeHtml(detail)}</div></details>` : ""}
      <details><summary>Test metadata</summary><div class="detail">Identity: ${escapeHtml(test.key)}\nStatus: ${escapeHtml(test.status)}\nCategory: ${escapeHtml(test.categoryLabel)}\nSignature: ${escapeHtml(test.signature || "None")}</div></details>
    </article>`;
  }).join("");
}
function renderGroups() {
  const root = document.getElementById("groups");
  if (!DATA.groups.length) {
    root.innerHTML = `<p class="insight">No active failure groups in this comparison.</p>`;
    return;
  }
  root.innerHTML = DATA.groups.map(group =>
    `<div class="group"><div class="group-head"><strong>${group.count} related failure${group.count === 1 ? "" : "s"}</strong><span class="count">${group.count} test${group.count === 1 ? "" : "s"}</span></div><div class="sig">Signature · ${escapeHtml(group.signature)}</div><ul>${group.tests.map(name => `<li>${escapeHtml(name)}</li>`).join("")}</ul></div>`
  ).join("");
}
document.getElementById("insight").textContent =
  `${number(DATA.summary.new_failures)} new failure(s), ${number(DATA.summary.persistent_failures)} persistent failure(s), and ${number(DATA.summary.resolved_failures)} resolved failure(s). Signatures group similar error text to help prioritize investigation.`;
document.getElementById("filters").addEventListener("click", event => {
  const button = event.target.closest("[data-filter]");
  if (!button) return;
  activeFilter = button.dataset.filter;
  document.querySelectorAll(".filter").forEach(item => item.classList.toggle("active", item === button));
  renderTests();
});
search.addEventListener("input", renderTests);
function download(filename, content, type) {
  const blob = new Blob([content], {type});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
document.getElementById("exportJson").addEventListener("click", () => {
  download("tracepilot-comparison.json", JSON.stringify(DATA, null, 2), "application/json");
});
document.getElementById("exportCsv").addEventListener("click", () => {
  const rows = [["category","test_name","class_name","status","message","detail","signature"]];
  visibleTests().forEach(test => rows.push([
    test.categoryLabel,test.name,test.classname,test.status,test.message,test.detail,test.signature
  ]));
  const csv = rows.map(row => row.map(value => `"${String(value ?? "").replace(/"/g,'""')}"`).join(",")).join("\r\n");
  download("tracepilot-comparison.csv", "\ufeff" + csv, "text/csv;charset=utf-8");
});
renderGroups();
renderTests();
</script>
</body>
</html>'''
    html = template.replace("__DATA__", payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path

