# Test Report

Date: 2026-10-10

Task: codex-support — Codex worker support with portable quality helpers

Scope: feature/codex-support implementation in agents.py, tasks.py, quality.py, setup_codex.py and installed templates; reviewed revision 696a4ffb09cbb0514ea02b0c05ef288959186e90.

Requirements: tasks/codex-support.md, AGENTS.md, templates/claude-agents/test-writer.md. No SPEC.md or docs/ARCHITECTURE.md exists in this source repository.

## Test files changed

- tests/test_codex.py: 24 stdlib unittest regression cases.
- tests/test_publish.sh: explicitly select main after cloning an empty bare remote, avoiding dependence on a user's Git default branch.

## Requirement coverage

| Requirement | Tests | Result |
|---|---|---|
| Preserve Claude default and explicit overrides | selection_and_override, environment_selection | Pass |
| Decode Codex progress, success, failure and quota | codex_events, limit_requires_error_event | Pass |
| Windows npm launch without shell prompt interpolation | windows_npm_keeps_prompt_literal, windows_unknown_shim_refused | Pass |
| Preserve user configuration; reject conflicting install atomically | InstallerTests (3 cases) | Pass |
| Committed task evidence, freshness, equivalent rebases, matching identity, reports, fixes, findings and validation | QualityTests (10 cases) | Pass |
| force/skip-check cannot bypass evidence or publish unfinished work | force_skip_cannot_bypass_quality_or_publish_work | Pass |
| Task bookkeeping isolates local code until completion | bookkeeping_does_not_publish_work_but_done_does | Pass |
| Windows import does not restart caller | plain_windows_import_does_not_restart_importer | Pass |
| Custom helper names are accepted and retain substantive instructions | helper_configuration_names_and_role_instructions | Pass |
| Real runner: fake Codex claims from Git, heartbeat backups, release/resume, completion | real_runner_fake_codex_claim_backup_release_complete | Pass |

## Focused and broader execution

Command: `python -X utf8 -m unittest discover -s tests -v`

Working directory: Taskflow checkout. Python 3.14.1 on Windows. Parent final validation of reviewed revision 696a4ffb09cbb0514ea02b0c05ef288959186e90: 24 tests passed, exit 0, 53.365 seconds (session 56905). Earlier 23-case post-fix run passed in 62.059 seconds. All mutation tests used temporary local Git repositories and a local bare remote; no real remote writes occurred.

After the live Codex helper-name issue was fixed, focused semantic template validation `python -X utf8 -m unittest discover -s tests -p test_codex.py -k helper_configuration -v` passed (1 test, exit 0). It parses all three TOML templates and checks accepted lowercase/digit/underscore names, distinct role names, substantive descriptions, preserved role references/report paths and parent/state/Git boundaries. All 24 cases subsequently passed on the reviewed commit.

Parent supplied real Codex CLI smoke evidence: persistent code_reviewer independently identified subtraction instead of addition in a temporary calculator fixture and wrote its own report at fixture revision 670e9cfc97f272cefd76c6c203d2419a30f7aef7. It changed no task state, code, tests, commits or remote branches. Ephemeral execution failed spawning and is documented as unsupported for this workflow; the default provider command uses persistent execution.

Sandbox invocation encountered temporary directory ACL failures; the same tests passed with authorized execution outside the sandbox. These failures were infrastructure failures, not product failures.

Existing Bash publication suite: `python3() { /c/Python314/python.exe "$@"; }; export -f python3; bash tests/test_publish.sh`, executed with Git Bash. All 10 scenarios passed, exit 0. The Python function selects this host's actual interpreter because the Windows python3 app alias is disabled.

## .taskcheck

Parent added .taskcheck invoking unittest discover. The same suite is run directly here; parent runs the project .taskcheck for final completion. Local completion tests intentionally use --skip-check to separately verify Git publication and the non-bypassable quality gate.

## Bugs found

TW-1 (resolved by fixer): importing agents.py on Windows without UTF-8 mode invoked its interpreter restart and exited the importer. Original `python -m unittest discover -s tests -v` failed at import with SystemExit 2. Fixer guarded the bootstrap; subprocess regression without PYTHONUTF8 now passes. No unresolved production defect from these tests.

Parent live smoke discovered hyphenated helper names are rejected by Codex spawn. Fixer changed TOML invocation names to test_writer/code_reviewer while preserving hyphenated role files and evidence keys. The semantic configuration regression now passes.

## Coverage

Status: unavailable. Metric: whole-file coverage of task-changed production files. Changed-line coverage: not measured.

No configured Python coverage provider or coverage command exists in this repository. Probe `python -X utf8 -m coverage --version` exited 1 with `No module named coverage`. No tool was installed and no configuration changed. No fresh or stale numerical coverage output is claimed.

Unmeasured production scope: agents.py, tasks.py, quality.py, setup_codex.py. Reported statement, branch, function and line counters are all unavailable. Templates are configuration/instructions and excluded from executable code coverage. Task-specific provider/event, installer and gate behavior is directly covered by the named tests; broader pre-existing runner recovery remains covered by existing scenario tests/manual smoke and requires parent assessment.

Final source/test revision: 696a4ffb09cbb0514ea02b0c05ef288959186e90. Parent confirms no source changes since this commit. Final 24-case validation on this revision passed. Coverage remains unavailable specifically because the repository has no configured coverage command/provider and Python 3.14.1 reports `No module named coverage`; no numerical statement, branch, function or line measurements exist for this revision.

Earlier 23-case passing source SHA256 snapshot (superseded by the reviewed commit for final source identity; setup/helper naming and the 24th test were subsequently added):

- agents.py: DD2E745A0EC3A3C5C1ABEC9DC124E6D969EE4E62696D553ABF4A29FA11AC3EAC
- tasks.py: EBCE710F31EEF0AA495015D08E9A751BC98F9DBFB158B3AC387C01EF677A99C9
- quality.py: D905A3C2B3A25797FF843CF88B982B9D9FF9717B3AA782D624E66D5B7FEFFCFA
- setup_codex.py: 0692F1FFAACE185AA4D1BC59B83CA9CEED42A0562B8A04CFDE11AF3BB7EEBEEA
- tests/test_codex.py: 295486F5D89BA105FFD46B53ED8953D8742314CE5EE95AA548D4F636F441E480

## Unable to test

- Live account quota exhaustion and authentication failures: no account quota deliberately consumed; synthetic error-event parsing tested.
- Linux/macOS runtime execution: this host runs Windows; command selection/parser logic tested here.
- Live ownership-loss process recovery remains outside this helper's local regression execution. Parent supplied real persistent code_reviewer smoke evidence as recorded above; fake-worker normal claim/backup/release/resume/completion is covered separately.

## Summary

Tests added; all 24 regression cases pass at reviewed revision 696a4ffb09cbb0514ea02b0c05ef288959186e90, including the real runner with fake Codex and helper-name validation. Existing publication scenarios pass, and parent supplied real persistent code_reviewer smoke evidence. Import bootstrap issue is resolved. Coverage measurement is unavailable and no percentages are inferred.
