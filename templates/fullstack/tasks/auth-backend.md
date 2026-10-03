---
title: Authentication and authorization (backend)
status: todo
owner:
deps: [data-model, api-contract]
prio: 2
---
## Goal
Skip if SPEC.md says no login is needed: then mark done with a note.

## Acceptance criteria
- [ ] Register/login/logout (or a demo-user shortcut) per the contract; protected endpoints reject anonymous calls with the contract's error shape
- [ ] Passwords hashed; secrets from env, never committed
- [ ] Tests: happy path, wrong password, missing token

## Notes
