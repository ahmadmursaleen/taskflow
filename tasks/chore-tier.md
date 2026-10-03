---
title: Chore tier: optional tests/refactors on an extras branch
status: todo
owner:
deps: []
prio: 2
---
## Goal

Let agents use leftover time and tokens for useful, low-risk work (extra test coverage, small
behaviour-preserving refactors) without ever competing with necessary tasks or putting `main` at risk.
Such "chores" land on a separate long-lived `extras` branch, never on `main`. `main` alone means
"our stuff works"; `extras` is an optional extra that humans can review and take all, some or none of.

## Acceptance criteria

Tier and priority
- [ ] Tasks can be marked as chores (`kind: chore` in the front matter; `tasks.py new <id> "<title>" --chore`).
- [ ] `ranked()` / `next` / `claim` without id offer a chore only when no required (non-chore) task is ready.
      A required task always ranks above every chore, whatever their `dependents`/`prio`.
- [ ] Chores are ignored by the runner's "all tasks done, exiting" check and by the "blocked" detection
      (`agents.py` main loop). Required progress in `status`, `list` and `BOARD.md` excludes them; chores are
      listed in their own section.
- [ ] Capacity: at most half of the active agents (rounded down, at least 1) hold a chore at the same time,
      so there is always spare capacity when required tasks become ready. Chores may be taken while an agent
      would otherwise sit in "waiting for dependencies to finish". No human setting is needed for any of this.

Token budget (automatic, no configuration)
- [ ] The runner records the latest `rate_limit_event` from each session's stream-json output
      (`rate_limit_info.unifiedWindows.{five_hour,seven_day}.{utilization,resetsAt}`) and publishes it with its
      status, so `agents.py status` and the dashboard show per agent: utilization of each window, time to reset.
- [ ] Before taking a new chore, the runner checks its own account's numbers. For each window:
      `elapsed = 1 - time_to_reset / window_length`. A chore is allowed only if, in both windows,
      utilization <= elapsed (we are on or under pace, so the tokens would otherwise expire unused) and
      utilization <= 1 - reserve, where reserve = 25% while required tasks are still open, 5% once they are all
      done. Required tasks are never gated by this.
- [ ] No numbers yet (no session run so far on this account): chores are allowed, still under the capacity cap.
- [ ] A running chore is not interrupted when the numbers change; the check applies only to taking the next one.
- [ ] Once all required tasks are done, a runner that may not take a chore (cap, pace or reserve) waits and
      re-checks (pace improves as the window runs out); it exits when no chore is ready or open.

The extras branch
- [ ] `done` on a chore targets `extras`, not `main`: it creates `extras` from `main` if it does not exist,
      merges the latest `origin/main` into `extras`, then merges the chore as **one merge commit per chore**
      (so it can be reverted or cherry-picked on its own), runs `.taskcheck` on the result and pushes `extras`.
      Only `main` → `extras` merging, never automatically back.
- [ ] Before marking a chore done, `done` runs the check several times (default 3, configurable) and refuses if
      any run fails, so flaky tests don't reach `extras`.
- [ ] A chore's work never reaches `main`: `done` for chores never pushes `main`. The task-file status change
      (the chore's `status: done`) still goes to `main` like any other board change.
- [ ] `tasks.py status` shows how far `extras` is ahead of `main` (number of chores, changed files) and how
      many chores have been merged into `extras`.
- [ ] `repos sync` publishes `main` only (unchanged behaviour); publishing `extras` is left to humans.

Agent guidance
- [ ] `AGENTS.md` gets a short "Chores" section: chores never before required work; behaviour-preserving only;
      no public API/signature changes; small diffs with concrete acceptance criteria (no "improve module X");
      if a new test reveals a bug, don't fix it in the chore: file a task (or record it with `assume`);
      while on a real task, write noticed improvements down as chores (`new --chore`) instead of doing them.
- [ ] Tests for the tier ranking, the exit logic ignoring chores, `done` targeting `extras`
      (including the one-merge-commit-per-chore shape), the capacity cap, and the pace/reserve rule
      (fed with recorded `rate_limit_event` lines, e.g. utilization 0.02 at 10% elapsed -> allowed,
      0.60 at 40% elapsed -> not allowed, 0.80 with required tasks open -> not allowed).

## Notes

- Why a branch and not main: flaky tests or a bad refactor can't break `.taskcheck` for required tasks, and
  refactor conflicts are only ever resolved on the extras side. Tests will usually merge back easily;
  refactors are where a final merge into main can hurt, so keep them small.
- Chosen over per-chore `extra/<id>` branches: one branch kept current with main avoids dozens of branches going
  stale independently, and one merge commit per chore keeps the pick-and-choose flexibility.
- Budget is deliberately automatic: humans shouldn't have to size it. Pace rule idea: tokens left in a window
  expire at reset, so spending them on chores when we are under pace costs nothing; the reserve keeps room for
  required work that may still become ready. Verified with Claude Code 2.1.284: stream-json emits
  `{"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "rateLimitType": "five_hour",
  "unifiedWindows": {"five_hour": {"utilization": 0.02, "resetsAt": 1790719800}, "seven_day": {...}}}}`.
  Other agent CLIs (`--cmd`) may not emit it: treat that as "no numbers".
- Open for humans: whether `extras` should also be published to the original repos, and whether refactors
  should be allowed at all or only tests to begin with.
