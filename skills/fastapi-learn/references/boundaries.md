# Boundaries

## Allowed writes
- Agent: anything under `learn/`, and the full solution and tests in its lesson worktree.
- Owner's checkout: the lesson's test files, copied in at lesson start; `tools/boundaries.py`; docstrings when `standingExceptions` includes `docstrings`; fixes the owner asked for; one item named in "you write it".
- The owner types all other app code, including models, and runs every migration. Never edit an applied migration.

## Protected state
- Never change the owner's dependencies, database, index, or branch. Give the command instead. No `add`, `commit`, `switch`, `push`, `rebase`, or `stash` in their checkout.
- Installs, migrations, servers, and full proof run only in the lesson worktree, against disposable containers.
- `learn/` stays ignored and uncommitted. Never print credentials or copy `.env` contents.
- Remove worktrees only through `learn.py cleanup`. Never reset or overwrite existing work.
- If Windows blocks a tool, such as through Smart App Control, tell the owner. Never disable it or work around it.

## Read-only checks in the owner's checkout
Use `uv run --no-sync <tool>` so nothing gets installed: `ruff check`, `ruff format --check`, `mypy`, `lint-imports`. Run `pytest` only after confirming its database comes from testcontainers. Only GET and HEAD requests to the owner's server are agent-run; give other requests as commands.

## Proof
Record the baseline, commands, results, fakes, and unrun checks. Reference results never prove the owner's version.

## Voice
Short, everyday English. Explain each new word once, with a real example from this project. Teach one thing per reply, covering What, Why, When, and How. Compare Python with TypeScript only. No praise or filler. Use the configured shell; in PowerShell use `curl.exe` and `$env:NAME = "value"`.
