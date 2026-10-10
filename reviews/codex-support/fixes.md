# Fixer report

Task: codex-support
Reviewed revision: 696a4ffb09cbb0514ea02b0c05ef288959186e90
Date: 2026-10-10

## Resolved findings

- CR-1: `tasks.py done` now distinguishes missing/stale quality evidence using `QUALITY REQUIRED` from ownership errors using `REFUSED`. Quality failures direct the worker to refresh evidence and retry, and accurately explain that this failure does not change ownership. Ownership checks and publication rules remain intact.
- CR-2: `quality.py` validates that the full reviewed revision identifies a commit, then compares project fingerprints. Equivalent task-only rebases no longer fail an ancestry check; actual project-content changes still invalidate evidence. Missing objects and non-commit object IDs remain invalid.
- Additional validated test-writer bug: the Windows UTF-8 bootstrap in `agents.py` now runs only as a script. Importing the runner no longer restarts or exits the importing test/application process.
- Live CLI finding: Codex 0.158.0 rejects hyphenated custom agent names. TOML names and Codex invocation instructions now use `test_writer`, `code_reviewer`, and `fixer`. Role filenames and quality artifact keys retain their existing hyphenated names. Persistent Codex execution remains enabled; the live smoke found that ephemeral execution cannot provide helper thread context.

## Validation

- Production AST parsing passed for `agents.py`, `tasks.py`, and `quality.py`.
- Plain Windows import regression passed under the UTF-8 test runner while its subprocess intentionally omitted `PYTHONUTF8`.
- Test-writer confirmed the full 23-case unittest suite passed after the production fixes (62.059 seconds), including quality diagnostics, equivalent rebase freshness, project-change staleness, plain Windows import, and real runner integration with a fake Codex executable. Existing Bash publication scenarios also passed. This run precedes the subsequent custom-agent naming correction.
- TOML parsing and assertions verified all three Codex custom-agent names and the installer invocation instructions after the naming correction.
- Parent final validation for revision 696a4ffb09cbb0514ea02b0c05ef288959186e90 passed: 24 unittest cases in 53.365 seconds (exit 0), plus all 10 existing Bash Git scenarios. Persistent execution with the real Codex `code_reviewer` custom agent succeeded and produced an independent report.
- The code-reviewer renewed its report for the same final revision, confirming CR-1 and CR-2 resolved with no residual material issues.
- Initial sandboxed unittest attempts encountered temporary-directory ACL permission errors. Test-writer reran successfully with approved sandbox escalation for offline temporary fixtures. Fixer-created workspace temporary fixtures were removed after verifying the exact cleanup target.
- `git diff --check` passed.

No task lifecycle commands, commits, pushes, branch changes, or additional workers were performed by this helper. The implemented fixes are included in revision 696a4ffb09cbb0514ea02b0c05ef288959186e90. Final validation and fresh review passed as reported by the parent; evidence reconciliation belongs to the parent.
