# Taskflow quality evidence

A project opts into committed evidence enforcement by committing `.taskquality` containing
`required`, with `quality.py` next to `tasks.py`. The Codex installer enables it. Existing
Claude projects without that marker retain their previous behavior; they can enable the same gate.

By default every task in an enabled project requires evidence. A human may classify a non-implementation
task during planning with `quality: exempt` and a nonempty `quality_reason:`. Workers must not add
exemptions to bypass review. This is a cooperative protocol: Git write access can change these files.

## Parent and helper workflow

1. Implement and commit the task. Invoke test-writer, have it add/run relevant tests and return
   coverage results and production defects. The parent commits its test changes.
2. Run `python tasks.py quality <id>` to obtain the full committed `reviewed_revision`.
   Supply that revision and the task's acceptance criteria to the helpers. Final tests/review
   reports must refer to this committed project content.
3. Invoke code-reviewer. Each helper writes its own report. For valid issues, invoke fixer,
   commit its changes, rerun tests and renew review evidence for the changed content. Retain
   a fixer report describing the findings and final revision when fixes were required.
4. Run the project check and construct `reviews/<id>/quality.json` from actual helper results.
   Commit the reports and record. Do not fabricate missing helper reports.
5. Run `python tasks.py done <id>`. It integrates the shared branch, runs the configured check
   and validates the committed evidence. Force/skip-check flags do not bypass this evidence gate.

Helpers never claim/complete tasks, commit, push, change branches or launch Taskflow workers.
If an invocation fails, resolve the failure or hold the task. Only the parent owns lifecycle decisions.
Run writing helpers sequentially to avoid concurrent file edits. On Codex, the reviewer needs file
write access for its report; its instructions prohibit production/test edits. This is a role boundary,
not an operating-system ACL. Verify actual helper invocations during the initial dry run.

## Artifact contract (schema version 1)

All artifacts live under `reviews/<id>/`. `tests.md` and `review.md` are always required; `fixes.md`
is required when fixes were needed. Reports must be nonempty, identify the task and full final
reviewed revision, and describe inspected scope, commands/results, findings and dispositions.
The test report retains task-scoped coverage results and significant gaps, or explains why
measurement was unavailable. Raw generated coverage may stay Git-ignored.

Example record (replace illustrative values with actual results):

```json
{
  "schema_version": 1,
  "task_id": "auth-login",
  "reviewed_revision": "FULL_COMMITTED_GIT_REVISION",
  "helpers": {
    "test-writer": {"status": "completed", "report": "reviews/auth-login/tests.md"},
    "code-reviewer": {"status": "completed", "report": "reviews/auth-login/review.md"},
    "fixer": {"status": "not_required", "reason": "No validated findings required fixes"}
  },
  "fixes_required": false,
  "findings": [],
  "validation": {"status": "passed", "command": "python -m unittest discover -s tests"},
  "coverage": {"status": "unavailable", "reason": "This project has no configured coverage provider"}
}
```

When fixes are required, fixer uses `status: completed` and the task's `fixes.md` report path.
Each finding has `id`, boolean `blocking`, and `disposition` (`resolved`, `accepted` or `open`).
Blocking findings must be resolved. Measured coverage instead uses `status: measured`, a command,
scope (the production files/behavior measured), and summary (results and material gaps).

## Freshness and limits

The reviewed revision must be a full commit ID that resolves locally. The gate compares tracked
project tree entries at that revision and HEAD, excluding `tasks/`, `reviews/`, `BOARD.md` and
`board.html`. This conservative whole-project comparison avoids silently accepting unrelated
code changes; concurrent code integration requires renewed evidence. It does not invalidate
reviews for report-only or task bookkeeping commits, including equivalent code commits rewritten
by task-only upstream rebases. Report files are validated for this task only.

The gate reads committed artifacts, rejects missing/placeholder/stale records, unresolved blocking
findings and unsuccessful validation. A record is evidence, not cryptographic proof that an independent
helper ran or that its judgment was correct. It cannot prevent authorized actors editing the gate,
exemptions or reports. The project check still needs to cover meaningful behavior.
