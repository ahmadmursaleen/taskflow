# Codex workers

Taskflow can run Claude and Codex workers against the same Git board. Each laptop uses its own
installed CLI, login, dependencies and Git credentials. A Taskflow worker claims a task; its
test-writer/reviewer/fixer helpers remain inside that task. Helpers do not become board workers.

## Install into a project

Prerequisites: Python 3.11+ for the template tests (runtime scripts use Python's standard library),
Git, and Codex CLI. The Codex default command requires a CLI supporting `exec --json --approve-for-me`
and project custom-agent TOML files; development smoke validation used Codex CLI 0.158.0.
Run `codex exec --help` on each laptop and update an older CLI before starting workers.
On Windows use Git for Windows, including its Bash, and Node when using npm-installed Codex.

From a checkout of Taskflow:

```sh
python setup_codex.py --project /path/to/project --dry-run
python setup_codex.py --project /path/to/project
```

Existing differing Taskflow files are refused before any writes. For an intentional upgrade,
review `--dry-run --overwrite`, then run with `--overwrite`. Existing user `.codex/config.toml`
is never replaced. Project `AGENTS.md` is retained and a marked Codex workflow section is appended
or updated. Commit and review all installed files before starting workers.

The installer supplies the five runtime scripts, custom helper configs, full role references,
`docs/TASKFLOW-QUALITY.md`, the frontend design skill and `.taskquality`. Role reference bodies are
derived from the existing Claude templates so detailed task-scoped coverage guidance is preserved.
Codex configurations override their dated report examples with the common task-specific paths.
Invoke custom agents as `test_writer`, `code_reviewer` and `fixer`: Codex agent names use
underscores. Quality-record role keys remain `test-writer`, `code-reviewer` and `fixer`.

Configure custom-agent delegation in the project's `.codex/config.toml` if needed:

```toml
[agents]
enabled = true
max_concurrent_threads_per_session = 3
```

Do not replace existing configuration wholesale. Confirm your CLI supports these fields and trusts
the project configuration. The reviewer needs report-write access; its role instructions prohibit
production/test edits. Check actual helper behavior rather than treating instructions as an ACL.

Each laptop logs in locally (`codex login`), checks `codex login status`, and configures Git access.
Do not copy another teammate's auth files or commit credentials. Taskflow neither stores nor shares
account authentication. Saved CLI authentication and API-key environments follow Codex's own rules;
check which mode you intend to use before running. Workers sharing an account share its limits.

Prepare tasks, `SPEC.md`, project dependencies and a meaningful `.taskcheck` as in SETUP.md.
The toolkit does not generate your application's plan automatically.

## Start and operate

```sh
python agents.py start 1 --provider codex --host alice
python agents.py status
python agents.py logs 1
python tasks.py watch
python agents.py stop --finish
```

After a successful one-worker dry run, teammates can start their own workers with unique host names.
Use separate local clones for different accounts/runtimes. An already running worker slot is not
reconfigured by another `start`; stop/restart it or use `--first` to allocate another slot.

The default command is `codex exec --json --approve-for-me`, using automatic approval review with
a workspace-write sandbox. A rejected or unavailable action must be resolved or handed off/held;
the runner does not secretly escalate it. Check that commit, task CLI, validation and Git access
work in this mode. The host runner itself executes Git heartbeat/status/backup commands outside
the model's sandbox using the host's Git credentials.

`--cmd`/`AGENT_CMD` override the command; `--provider`/`AGENT_PROVIDER` select provider semantics.
Explicit options win over environment values. For Codex overrides, retain `exec --json` and choose
permissions your environment supports. `--provider custom` requires a command override.
Claude remains the default with its existing settings behavior. `--yolo` explicitly bypasses
protections for isolated environments and is not the recommended setup.

On Windows, npm's Codex JavaScript entry point is launched with Node directly; prompts never
become shell source. For another `.cmd`/`.bat` shim, supply a native executable or a direct
interpreter command such as `node <launcher.js>`.

## Quality, coverage and interface design

Follow [QUALITY.md](QUALITY.md), installed as `docs/TASKFLOW-QUALITY.md` in projects. The required
sequence is implement, test-writer, reviewer, fixer when valid findings need fixes, renewed
validation/review after changes, and completion. Preserve coverage from the application's existing
tool with task-scoped results and gaps; unavailable measurement needs a concrete explanation.
Taskflow does not install an application coverage provider.

Use `$taskflow-frontend-design` for user-facing frontend changes. This portable skill establishes
visual direction within requirements and the existing design system, and calls for checking the
actual browser UI. It is not Anthropic's plugin or a guarantee of identical output. Browser tools
must be available on each worker; record missing visual verification rather than claiming it ran.

The enabled gate blocks missing, uncommitted, stale or failed evidence, including force/skip-check
attempts. Concurrent project changes require renewed review. Only this task's reports are required.
Existing projects without `.taskquality` keep legacy completion behavior. Claude projects can
enable the same gate by copying `quality.py` and following QUALITY.md.

## Recovery and limitations

Existing timeout, task budget, lease, WIP backup, hold, release and restart workflows apply.
Codex ownership is reconciled from task files, not CLAIMED text. Successful turns require
`turn.completed`. Quota detection considers structured errors; incidental test output containing
429 does not classify the account as limited. Unknown reset times use `--limit-wait`.
Three failed sessions hand off, matching the existing runner behavior. Do not add `--ephemeral`
to helper-enabled worker commands: CLI 0.158.0 could not spawn helpers without a persisted rollout.

Only committed, successfully backed-up work survives a lost laptop. Logs may contain local command
output; keep credentials out of them. The current session log is overwritten next session; preserve
dry-run invocation evidence beforehand. Git quality reports are durable.

Tests use fake events and temporary local Git repositories. A real CLI smoke verifies launch/auth/
events, not complete multi-laptop operation. Before unattended use, run one real implementation task
and inspect helper invocation, permissions, coverage, refusal behavior and committed reports, then
test takeover on two machines. Git coordination is a cooperative protocol.

Official references (checked 10 October 2026):

- [Noninteractive Codex](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Custom subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Skills](https://learn.chatgpt.com/docs/build-skills)
