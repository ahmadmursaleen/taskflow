---
title: Codex worker support with portable quality helpers
status: in_progress
owner: ORION\mursalah
deps: []
prio: 1
lease_until: 
---
## Goal
Add an opt-in Codex worker provider while preserving Claude and custom commands. Port the quality helper definitions and task-scoped coverage instructions, provide a project frontend-design skill, and enforce committed quality evidence before task completion.

## Acceptance criteria
- [ ] Provider selection, launch and JSONL parsing support Codex on Windows/Linux/macOS without changing Claude defaults.
- [ ] Codex claims are reconciled from Git task state; crashes, limits, timeout, stop and ownership loss retain existing recovery behavior.
- [ ] An installer provides Codex helper configurations and a frontend skill from versioned templates, without overwriting existing user configuration.
- [ ] Completion validates committed task-specific quality reports, scope freshness, required fixes and final validation; force/skip-check cannot bypass quality enforcement.
- [ ] Regression tests use temporary local Git remotes and fake workers; setup and limitations are documented.

## Notes
