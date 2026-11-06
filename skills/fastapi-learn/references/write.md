# Write a proven lesson

Build the complete solution in a separate worktree, then write docs from what was tested. Keep the project's stack and layout. Read [config.md](config.md) for gates.

## 1. Prepare
1. Read the ticket. Expect status proposed. Confirm open decisions, keeping answers already given.
2. Read project rules, sibling code in the layers you'll touch, and the `fastapi-best-practices` rules mapped in [check.md](check.md). Verify version-sensitive APIs against installed packages. Report a missing source once.
3. Record `git status --short` and `git rev-parse HEAD`. Copy only needed uncommitted changes into the worktree, never secrets or `.venv`. If a change is unclear, ask.

## 2. Worktree
Use `<lessonWorktreesPath>/NN-slug`, resolved and confirmed outside the repo:

```text
git worktree add --detach <path> <starting-commit>
```

If the folder exists, reuse it only if it belongs to this lesson and baseline. In `<path>/<appRoot>`, run `uv sync --locked`. A scaffold has no lock yet, so run the same `uv init` and `uv add` commands the guide teaches, with no nested Git repo.

## 3. Isolate services
Use only containers from testcontainers, with no dev database and no copied `.env`. Connect through `127.0.0.1`. Before any server proof, print the effective database host and name, without credentials, and confirm it's the container. Use fakes for mail and payments, and record each one. Pick a free port, and never touch the owner's server.

## 4. Build and prove
1. Run the existing tests first, and record baseline failures.
2. Write the solution at normal paths with `uv add` for packages and `alembic revision --autogenerate` for schema changes, reviewing each file.
3. Write tests for each criterion and refusal, following the `test-*` rules. Step checks name a test file, because a lesson's not-yet-valid imports stop collection for that file only. Keep a package's first `uv add` ahead of any test check, since `conftest.py` imports it. Prove "at the same time" criteria with concurrent requests.
4. Review against the loaded rules, fix, and rerun. A new failure in an old test must be fixed, not hidden.
5. Run every gate in the worktree. Stop only servers you started.

## 5. Write docs in `learn/NN-slug/`
1. Write README, GUIDE, and `check-yourself.md` from [templates.md](templates.md). GUIDE code comes from tested files.
2. Add first-seen Python ideas to `learn/python-concepts.md`, using the format in [teach.md](teach.md). Check existing headings first.
3. Run `python <skill-dir>/scripts/learn.py guide-size learn/NN-slug/GUIDE.md`. Over the limit: split the ticket and rebuild the smaller slice. Never remove teaching to fit.

## 6. Start the lesson
1. Copy this lesson's test files into the owner's checkout. Never overwrite an existing file: if a shared file such as `conftest.py` changed, show the diff and let the owner apply it. A scaffold copies them at a named step, once `tests/` and its dependencies exist.
2. Set the ticket to in-progress. Disclose any incomplete proof.
3. Reply with the ticket and reference paths, baseline, changed-file count, criterion and gate results, rules and clashes, and limits. Then say: "Start a fresh session here to keep token use low, and say **start**." The owner may continue here if they prefer.
