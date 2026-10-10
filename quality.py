"""Committed quality evidence for Taskflow projects that enable .taskquality.

Stdlib only. Checks recorded evidence, not the authenticity of an independent review.
The fingerprint covers every tracked project path except task bookkeeping, reports
and generated boards. Concurrent project changes therefore require fresh evidence.
"""
import hashlib
import json
import re


def read(T, revision, path):
    p = T.git("show", f"{revision}:{path}", check=False)
    return p.stdout if p.returncode == 0 else None


def fingerprint(T, revision):
    p = T.git("ls-tree", "-r", "-z", revision, check=False)
    if p.returncode:
        raise ValueError("reviewed_revision does not resolve to a Git tree")
    entries = []
    for entry in p.stdout.split("\0"):
        if not entry:
            continue
        _, path = entry.split("\t", 1)
        if path.startswith(("tasks/", "reviews/")) or path in ("BOARD.md", "board.html"):
            continue
        entries.append(entry)
    return hashlib.sha256("\0".join(entries).encode("utf-8")).hexdigest()


def validate(T, task):
    """Return an actionable error, or None. All artifacts are read from HEAD."""
    tid = task["id"]
    marker = read(T, "HEAD", ".taskquality")
    if marker is None:
        if (T.ROOT / ".taskquality").exists():
            return "commit .taskquality before completing tasks"
        return None  # existing projects retain their current completion behavior
    if marker.strip() != "required":
        return ".taskquality must contain 'required'"
    if task.get("quality") == "exempt":
        if task.get("quality_reason", "").strip():
            return None
        return "quality exemption requires a planning-time quality_reason"
    if task.get("quality") not in (None, "", "required"):
        return "quality must be required or an explicitly justified exempt"
    prefix = f"reviews/{tid}/"
    raw = read(T, "HEAD", prefix + "quality.json")
    if raw is None:
        return f"commit {prefix}quality.json and helper reports (see docs/QUALITY.md)"
    try:
        q = json.loads(raw)
        if not isinstance(q, dict) or q.get("schema_version") != 1 or q.get("task_id") != tid:
            raise ValueError("schema_version must be 1 and task_id must match")
        revision = q.get("reviewed_revision", "")
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40,64}", revision):
            raise ValueError("reviewed_revision must be a full Git commit ID")
        reviewed_object = T.git("cat-file", "-t", revision, check=False)
        if reviewed_object.returncode or reviewed_object.stdout.strip() != "commit":
            raise ValueError("reviewed_revision must resolve to a Git commit")
        # Task-only upstream updates can rebase reviewed commits without changing
        # project content. Identity of that content, not ancestry, defines freshness.
        if fingerprint(T, revision) != fingerprint(T, "HEAD"):
            raise ValueError("review evidence is stale: project content changed; rerun helpers and validation")
        helpers = q.get("helpers")
        if not isinstance(helpers, dict):
            raise ValueError("helpers must describe test-writer, code-reviewer and fixer")
        for role, filename in (("test-writer", "tests.md"), ("code-reviewer", "review.md"), ("fixer", "fixes.md")):
            helper = helpers.get(role)
            if not isinstance(helper, dict):
                raise ValueError(f"missing {role} result")
            if role == "fixer" and q.get("fixes_required") is False:
                if helper.get("status") != "not_required" or not str(helper.get("reason", "")).strip():
                    raise ValueError("fixer not_required needs a reason")
                continue
            if helper.get("status") != "completed" or helper.get("report") != prefix + filename:
                raise ValueError(f"{role} must complete and report to {prefix}{filename}")
            report = read(T, "HEAD", prefix + filename)
            if not report or len(report.strip()) < 40 or tid not in report or revision not in report:
                raise ValueError(f"{filename} must be committed, nonempty, and identify task and reviewed_revision")
            if re.search(r"^\s*(TODO|TBD|PLACEHOLDER)\s*$", report, re.M | re.I):
                raise ValueError(f"{filename} contains a placeholder")
        if type(q.get("fixes_required")) is not bool:
            raise ValueError("fixes_required must be true or false")
        findings = q.get("findings")
        if not isinstance(findings, list):
            raise ValueError("findings must be a list (empty when no findings)")
        for finding in findings:
            if not isinstance(finding, dict) or not finding.get("id") or type(finding.get("blocking")) is not bool:
                raise ValueError("each finding needs id, blocking and disposition")
            if finding.get("disposition") not in ("resolved", "accepted", "open"):
                raise ValueError("finding disposition must be resolved, accepted or open")
            if finding["blocking"] and finding["disposition"] != "resolved":
                raise ValueError(f"blocking finding {finding['id']} is unresolved")
        validation = q.get("validation")
        if not isinstance(validation, dict) or validation.get("status") != "passed" or not validation.get("command"):
            raise ValueError("validation must record a passed command")
        coverage = q.get("coverage")
        if not isinstance(coverage, dict):
            raise ValueError("coverage must record measured results or an unavailable reason")
        if coverage.get("status") == "measured":
            if not coverage.get("command") or not coverage.get("scope") or not coverage.get("summary"):
                raise ValueError("measured coverage needs command, scope and summary")
        elif coverage.get("status") != "unavailable" or not str(coverage.get("reason", "")).strip():
            raise ValueError("unavailable coverage needs a concrete reason")
    except (ValueError, TypeError, AttributeError) as ex:
        return f"{prefix}quality.json: {ex}"
    return None


def scope(T, tid):
    revision = T.git("rev-parse", "HEAD").stdout.strip()
    return {"task_id": tid, "reviewed_revision": revision, "project_fingerprint": fingerprint(T, revision)}
