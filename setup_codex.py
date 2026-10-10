#!/usr/bin/env python3
"""Install the versioned Taskflow Codex worker files into a project. Stdlib only."""
import argparse
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
START = "<!-- taskflow-codex:start -->"
END = "<!-- taskflow-codex:end -->"
INSTRUCTIONS = """## Codex workers

Read docs/TASKFLOW-QUALITY.md before completing tasks. Follow the Taskflow task protocol.
For implementation tasks, invoke the custom test_writer and code_reviewer agents, then fixer
when validated issues require fixes. Each helper writes its own task-specific report. The parent
commits implementation/tests, supplies the reviewed revision, verifies reports and builds quality.json.
Use $taskflow-frontend-design for tasks that create or materially change user-facing UI.
The parent owns task claims, assumptions, validation and completion. Helpers cannot change task
state or Git branches, commit, push or launch Taskflow workers. A missing/failed required helper
must be resolved or the parent must hold the task; do not fabricate reports or skip it.
"""


def plan(project):
    files = {}
    for name in ("tasks.py", "agents.py", "board.py", "repos.py", "quality.py"):
        files[name] = (HERE / name).read_text(encoding="utf-8")
    for role in ("test-writer", "code-reviewer", "fixer"):
        files[f".codex/agents/{role}.toml"] = (HERE / "templates" / "codex-agents" / f"{role}.toml").read_text(encoding="utf-8")
        # One maintained source for the substantive role/coverage guidance.
        prompt = (HERE / "templates" / "claude-agents" / f"{role}.md").read_text(encoding="utf-8")
        if prompt.startswith("---\n"):
            prompt = prompt.split("---\n", 2)[2]
        files[f".codex/taskflow/roles/{role}.md"] = prompt.replace("Bash", "the shell tool")
    files[".agents/skills/taskflow-frontend-design/SKILL.md"] = (
        HERE / "templates" / "skills" / "taskflow-frontend-design" / "SKILL.md").read_text(encoding="utf-8")
    files["docs/TASKFLOW-QUALITY.md"] = (HERE / "docs" / "QUALITY.md").read_text(encoding="utf-8")
    files[".taskquality"] = "required\n"
    agent_file = project / "AGENTS.md"
    existing = agent_file.read_text(encoding="utf-8") if agent_file.exists() else (HERE / "AGENTS.md").read_text(encoding="utf-8")
    section = START + "\n" + INSTRUCTIONS + END
    if START in existing:
        if existing.count(START) != 1 or existing.count(END) != 1 or existing.index(END) < existing.index(START):
            raise ValueError("AGENTS.md has malformed Taskflow managed markers")
        before, rest = existing.split(START, 1)
        _, after = rest.split(END, 1)
        files["AGENTS.md"] = before + section + after
    else:
        files["AGENTS.md"] = existing.rstrip() + "\n\n" + section + "\n"
    return files


def install(project, overwrite=False, dry_run=False):
    project = Path(project).resolve()
    files = plan(project)
    conflicts = []
    changed = []
    for name, content in files.items():
        dest = project / name
        # Refuse symlink escapes, including links in parent directories.
        if not dest.resolve().is_relative_to(project):
            raise ValueError(f"destination escapes project: {name}")
        if dest.exists() and dest.read_text(encoding="utf-8") == content:
            continue
        if dest.exists() and name != "AGENTS.md" and not overwrite:
            conflicts.append(name)
        changed.append(name)
    if conflicts:
        raise ValueError("existing files differ: " + ", ".join(conflicts) + "; review --dry-run --overwrite before replacing them")
    for name in changed:
        print(("would write " if dry_run else "write ") + name)
        if not dry_run:
            dest = project / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(files[name])
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--overwrite", action="store_true", help="replace differing Taskflow files; never replaces user config.toml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        install(args.project, args.overwrite, args.dry_run)
    except (OSError, ValueError) as ex:
        sys.exit(str(ex))


if __name__ == "__main__":
    main()
