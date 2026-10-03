---
title: End-to-end smoke test of the demo scenario
status: todo
owner:
deps: [fe-core, fe-auth, core-logic]
prio: 2
---
## Goal
Automate the demo path from SPEC.md with Playwright (or equivalent).

## Acceptance criteria
- [ ] One command runs a browser test walking the entire demo scenario against seeded data
- [ ] Failures are reported clearly; test is added to CI/`make check` if it is fast (<60s)

## Notes
