---
title: Model-aware picking: task difficulty, per-task model, reserve scarce models
status: todo
owner:
deps: [chore-tier]
prio: 2
---
## Goal

Match tasks to models. Each task says how hard it is; the runner runs it on a fitting model, chosen per
task, not per agent. A scarce strong model (e.g. Fable, available to only one team member) is kept for
the hardest tasks and doesn't spend capacity on easy ones, but the critical path never waits for it for long.
All of it is deterministic in `tasks.py` / `agents.py`; agents don't reason about who else could take a task.

## Acceptance criteria

Difficulty
- [ ] Tasks have `difficulty: 1|2|3|4` in the front matter (default 2 when missing). Not `level`: `analyze()`
      already uses `level` for the layer in the dependency graph.
      1 = mechanical (Haiku), 2 = normal (Sonnet), 3 = hard (Opus), 4 = needs the best available model (Fable).
- [ ] `tasks.py new <id> "<title>" --difficulty N`; `split` subtasks inherit the parent's difficulty unless the
      split file gives a `difficulty:` line per subtask (next to `deps:`).
- [ ] Escalation: each `release` (not `--handoff`) and each `redo` raises the difficulty by one (max 4),
      recorded in the task's log line, so a task that failed on Sonnet runs on Opus next. `unhold` doesn't reset it.
- [ ] `list`, `next`, `BOARD.md` and board.html show the difficulty.

Per-task model (runner)
- [ ] `agents.py start ... --models <list>` (default `haiku,sonnet,opus`) sets the models the agent may use.
      A mapping difficulty -> model lives in one place in `agents.py` and can be overridden with
      `--model-map 1=haiku,2=sonnet,3=opus,4=claude-fable-5-1`.
- [ ] After `CLAIMED`, the runner starts the session with `--model <m>`, where m is the model for the task's
      difficulty; if the agent doesn't have that model, the nearest stronger one it has, else its strongest.
      With a custom `--cmd`/`AGENT_CMD` that already contains `--model`, the runner does not add one.
- [ ] The runner publishes `models` in its status (`status/<owner>`); `agents.py status` and the dashboard show it.

Picking (`ranked()` gets the agent's models; `next`/`claim` without id read them from `AGENT_MODELS`,
which the runner sets; a human without it is treated as having every model, i.e. today's behaviour)
- [ ] An agent only sees tasks it can run well: difficulty <= the difficulty of its strongest model + 1
      (Sonnet-only can do up to 3, so nothing stalls when Opus is missing; Haiku-only up to 2).
- [ ] Strong models avoid easy tasks: an agent whose weakest model is level k (e.g. `--models fable` -> 4)
      takes tasks with difficulty >= k; if none is ready, k-1; never lower. Among those it prefers the highest
      difficulty, then the usual `(-dependents, prio, id)`.
- [ ] Reservation: a difficulty-4 task is hidden from agents without a level-4 model while a level-4 agent is
      alive (its status updated within the last 5 min, state not stopped/finished), unless the task has been
      ready for more than 30 min, or it has >= 5 dependents. Both values are constants at the top of `tasks.py`.
      "Ready since" is derived from git (the commit that marked its last dependency done, or its creation).
- [ ] With no reservation in play, ranking among eligible tasks is unchanged (`-dependents, prio, id`).
- [ ] The chore tier (`chore-tier`) still applies on top: required tasks before chores, whatever the difficulty.
- [ ] `claim <id>` by explicit id ignores all of this (humans and agents may still pick deliberately);
      `next` explains hidden tasks in one line, e.g. `2 tasks reserved for fable agents (bob/agent-3)`.
- [ ] If every ready task is filtered out for an agent, the runner waits (as for "waiting for dependencies")
      instead of exiting; it never counts as "blocked".

Guidance and docs
- [ ] `AGENTS.md`: set `--difficulty` when creating or splitting tasks, record it with `assume`; don't lower a
      task's difficulty to grab it.
- [ ] `TEAM.md`: how a member with a scarce model runs a dedicated agent next to the normal ones:
      `python agents.py start 2 --host bob` and `python agents.py start 1 --first 3 --host bob --models fable`,
      and that both share one subscription limit.
- [ ] Tests: model choice per difficulty (incl. fallback to stronger/strongest), escalation on release/redo,
      fable-only agent skips difficulty 1-2 and falls back to 3, Opus agent skips a difficulty-4 task while a
      fable agent is alive and takes it after 30 min / with >= 5 dependents / when the fable agent's status is
      stale, `AGENT_MODELS` unset = old ranking, explicit `claim <id>` bypasses the filter.

## Notes

- Decided by the team lead: strong models should avoid easy tasks; a member with a scarce model runs it as a
  separate agent (`--first`), not mixed into the normal agents.
- Why per-task models: most members have Haiku/Sonnet/Opus, so choosing per task removes most coordination;
  only the scarce model needs cross-agent awareness, which the existing status branches provide.
- Difficulty guesses will be wrong; escalation via release/redo corrects them using data the board already has.
- Assumed, revisit: grace period 30 min, override at >= 5 dependents, the "+1" rule for weaker agents, and the
  CLI name of the Fable model (`claude-fable-5-1`; check `claude --model` aliases).
- Possible follow-up (not in this task): use the `rate_limit_event` numbers from `chore-tier` to step down to a
  cheaper model when an account is over pace.
