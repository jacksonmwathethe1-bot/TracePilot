from __future__ import annotations
import hashlib
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
def _normalize(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\bline \d+\b", "line <n>", text)
    text = re.sub(r":\d+(?=[:\]])", ":<n>", text)
    return text
def _failure_signature(kind: str, message: str, detail: str) -> str:
    evidence = message.strip() or detail.strip() or kind
    normalized = _normalize(f"{kind} {evidence}")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
def load_report(path: str | Path) -> dict:
    """Read JUnit XML and return tests indexed by classname and test name."""
    path = Path(path)
    root = ET.parse(path).getroot()
    if _local_name(root.tag) not in {"testsuite", "testsuites"}:
        raise ValueError(f"Unsupported JUnit XML root: {root.tag}")
    tests = {}
    for case in root.iter():
        if _local_name(case.tag) != "testcase":
            continue
        name = case.attrib.get("name", "(unnamed)")
        classname = case.attrib.get("classname", "")
        key = f"{classname}::{name}"
        # Include an occurrence number if the report repeats a test identity.
        occurrence = 2
        unique_key = key
        while unique_key in tests:
            unique_key = f"{key} [duplicate {occurrence}]"
            occurrence += 1
        failure_node = next(
            (
                node for node in case
                if _local_name(node.tag) in {"failure", "error"}
            ),
            None,
        )
        if failure_node is None:
            status = "passed"
            kind = ""
            message = ""
            detail = ""
            signature = ""
        else:
            kind = _local_name(failure_node.tag)
            message = failure_node.attrib.get("message", "").strip()
            detail = (failure_node.text or "").strip()
            status = "failed"
            signature = _failure_signature(kind, message, detail)
        tests[unique_key] = {
            "key": unique_key,
            "name": name,
            "classname": classname,
            "status": status,
            "kind": kind,
            "message": message,
            "detail": detail,
            "signature": signature,
        }
    if not tests:
        raise ValueError(f"No test cases found in {path}")
    return {
        "source": path.name,
        "tests": tests,
        "total": len(tests),
    }
def compare_reports(baseline: dict, current: dict) -> dict:
    """Compare two parsed runs and group failures by error signature."""
    before = baseline["tests"]
    after = current["tests"]
    new_failures = []
    persistent_failures = []
    resolved_failures = []
    new_tests = []
    removed_tests = []
    for key, test in after.items():
        previous = before.get(key)
        if previous is None:
            if test["status"] == "failed":
                new_failures.append(test)
            else:
                new_tests.append(test)
            continue
        if previous["status"] == "passed" and test["status"] == "failed":
            new_failures.append(test)
        elif previous["status"] == "failed" and test["status"] == "passed":
            resolved_failures.append(test)
        elif test["status"] == "failed":
            persistent_failures.append(test)
    for key, test in before.items():
        if key not in after:
            removed_tests.append(test)
    groups = defaultdict(list)
    for test in new_failures + persistent_failures:
        groups[test["signature"]].append(test["key"])
    failure_groups = [
        {"signature": signature, "tests": sorted(keys)}
        for signature, keys in sorted(
            groups.items(), key=lambda item: (-len(item[1]), item[0])
        )
    ]
    return {
        "baseline": baseline["source"],
        "current": current["source"],
        "baseline_total": baseline["total"],
        "current_total": current["total"],
        "new_failures": new_failures,
        "persistent_failures": persistent_failures,
        "resolved_failures": resolved_failures,
        "new_tests": new_tests,
        "removed_tests": removed_tests,
        "failure_groups": failure_groups,
        "summary": {
            "new_failures": len(new_failures),
            "persistent_failures": len(persistent_failures),
            "resolved_failures": len(resolved_failures),
            "new_tests": len(new_tests),
            "removed_tests": len(removed_tests),
            "failure_groups": len(failure_groups),
        },
    }
