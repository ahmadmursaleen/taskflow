---
title: Add test runner, linter and `make check`
status: todo
owner:
deps: [repo-scaffold]
prio: 2
---
## Goal
Give every agent one command to validate its work before marking done.

## Acceptance criteria
- [ ] `make check` runs backend tests, frontend tests/typecheck and linters and exits non-zero on failure
- [ ] At least one trivial passing test on each side
- [ ] `.taskcheck` contains `make check`, so `tasks.py done` runs it on every task merged with the latest main
- [ ] `make check` is fast enough to run on every `done` (aim for < 2 min; slow e2e tests go elsewhere)

## Notes
