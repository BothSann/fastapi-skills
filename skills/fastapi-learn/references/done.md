# "done": check, then give the next step

For start or resume, skip to step 2.

## 1. Check the finished step
Run its check if it's read-only (see boundaries.md), otherwise ask the owner to paste the output.

| Step kind | Quick check |
|---|---|
| Install, `uv` setup | Package is in `pyproject.toml`, and `uv.lock` changed |
| Typed a file | Read it for the step's one idea, then `uv run --no-sync mypy <file>` |
| Route or wiring | `learn.py scan <repo> --no-gh` shows the route without STUB, then read the wiring |
| Test turned green | `uv run --no-sync pytest <file>::<test>` |
| Migration | Owner pastes `alembic upgrade head` output; read the generated file |
| Request with a write | Owner pastes the output; compare with the ticket |

Passes: say so in one line. Fails: say what you saw in one or two lines, and don't give the next step. Offer **check** for a full review.

## 2. Give the next step
Run `python <skill-dir>/scripts/learn.py step learn/NN-slug/GUIDE.md <N>`. Don't read the whole guide. Give:
- The step number and title.
- What, Why, When, and How, shortened. For code, point to "GUIDE.md, step N" rather than pasting it, and name the one new idea.
- A new Python idea: one line, plus its `python-concepts.md` heading.
- The check and its expected output.
- The cue: **done** or **check**.

## 3. Update the README
In "Where you are now", write what's verified and the next step.

No steps left: tell the owner to say **ship it**.
