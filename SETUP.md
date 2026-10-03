# Setup: from repos + brief to autonomous agents

For the team lead. Open Claude Code in the folder that contains `taskflow/` and say:
**"Guide me through taskflow/SETUP.md, one phase at a time."**

Claude: work through the phases in order. Do each step yourself where you can; ask me only for
decisions, credentials and GitLab clicks. Keep the conversation going until phase F is done: this
takes a few hours, most of it in phases C and D. Don't start phase D before I approve SPEC.md.

## A. Plumbing (30 min)
1. Check every tool: `python3 --version`, `git subtree -h` (Fedora: `sudo dnf install git-subtree`),
   `claude --version`, and that `ANTHROPIC_API_KEY` is not set. If the project's tests will need Docker
   (e.g. Testcontainers), `docker info` must answer: start Docker Desktop and let it start at login.
2. I create an empty GitLab repo for the working repo (e.g. `org/contest`) and protect only `main`.
   Ask me for its URL and the URLs of the original repos.
3. Follow README.md "Contest quick start", steps 2–3: clone, copy taskflow, `repos add` for each repo.
4. Copy `taskflow/TEAM.md` into the repo root and fill in its `<working-repo-url>`.
5. Commit `.claude/settings.json`, so that headless agents may run what they need (anything not
   allowed is denied without asking). Adjust the list to the stack:
   ```json
   {"permissions": {
     "allow": ["Bash(python tasks.py:*)", "Bash(python3 tasks.py:*)", "Bash(git:*)", "Bash(make:*)",
               "Bash(npm:*)", "Bash(npx:*)", "Bash(pytest:*)", "Bash(ls:*)", "Bash(cat:*)"],
     "deny":  ["Bash(git push:*)"]
   }}
   ```
   The deny rule enforces "agents never push": `tasks.py done` pushes for them. `agents.py` passes this
   file with `--settings`, because Claude Code ignores it in the agents' clones (untrusted folders).
   It also applies to Claude in your own clone: from now on you push, Claude commits. Once agents run,
   they push to main every minute, so push with a retry loop:
   `for i in 1 2 3 4 5 6; do git pull -q --rebase && git push && break; sleep 3; done`.

## B. Understand the code (30–60 min)
1. Read `backend/` and `frontend/`. Write `docs/ARCHITECTURE.md`: stack, an "Install" section for
   Linux/macOS/Windows (teammates' agents run the tests on their laptops), how to run and test each part,
   env vars, and the API between frontend and backend.
2. Make one fast check (< 2 min) that runs lint + tests of all folders, and put the command in
   `.taskcheck`. It always runs in `sh` (on Windows: Git for Windows' bash), but tools like `make`
   are missing on Windows, so prefer e.g. `npm run check` or a small script. Run it and fix it until
   it passes on a clean clone. Everything the check needs (JDK, Node version, Docker...) goes into the
   "Install" section and TEAM.md: an agent whose check can't run puts its task on hold.
3. Add a short "Project notes" section to AGENTS.md: how to run, how to test, and the code
   conventions every agent must follow.

## C. Agree on what to build (1–2 h, the important part)
I paste the contest brief into `BRIEF.md`. Then interview me, a few questions at a time:
- What do the judges reward? What does a winning demo look like, step by step?
- Must-haves vs nice-to-haves; what we deliberately skip.
- Features: for each, the user story, which folders it touches, API changes, data changes.
- Constraints: deadline, deployment target, AI/LLM usage, secrets, anything that needs a human.

Write the answers into `SPEC.md` as they come: goals, demo script, features (MoSCoW), API contract
changes, out of scope, open questions. Show it to me until I say "approved". Commit and push.

## D. Generate the task board (1 h)
Replace the template tasks with ones derived from SPEC.md (`python tasks.py new ...`, then write
Goal / Acceptance criteria into each file). Rules for good tasks:
- One agent, 30–90 min, one clear outcome. Acceptance criteria are checkable, and tests are included.
- Contract first: API/data model tasks come before the backend and frontend tasks that use them.
- Two tasks that could run in parallel must not edit the same files. Split or add a dep if they would.
- `deps` only where really needed. The board must be wide enough to keep all agents busy
  (count: agents on all laptops).
- `prio: 1` for the demo-critical path. End with demo polish, README and a final smoke test.

Then `python tasks.py check` and `python tasks.py graph`, and walk me through board.html: the critical
path, how many tasks can run in parallel, and anything unclear. Revise until I approve. Push.

## E. Dry run (30 min)
1. Set up the sync: README step 6 (GitLab CI template, or `repos sync --every 30m` in a spare clone).
   Run one sync by hand and check the original repos.
2. Check that every tool of `.taskcheck` works in the shell you start agents from (agents inherit its
   PATH, e.g. the nvm Node version; Docker running). Then `python3 agents.py start 1` and watch
   `python3 tasks.py watch` until the first task is done. Look at `../<repo>-agents/logs/agent-1.log`
   and grep `agent-1.session.txt` for `permission_denied`: each denial is a command to allow or avoid.
3. Fix whatever went wrong (permissions denied, a failing check, vague tasks) in
   `.claude/settings.json`, AGENTS.md or the task files. Repeat until one task goes through cleanly.

## F. Go autonomous
1. `python3 agents.py start <n>` here (2 per Claude subscription is a good start).
2. Send teammates the repo URL and TEAM.md.
3. From now on I only watch the dashboard. Things to act on: the **Needs a human** panel (fix the
   cause, then `python tasks.py unhold <id>`), stale tasks, a failing sync. Add tasks with
   `python tasks.py new` any time.
