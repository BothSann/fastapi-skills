# Project config

`learn/learn.config.json` holds personal facts. Preserve existing values, and adapt to the project rather than reshaping it.

| Field | Meaning |
|---|---|
| appRoot | Required. App folder from the repo root; `.` or e.g. `apps/api` |
| baseBranch | Required. Shipping target, e.g. `origin/main` |
| shell | Required. `powershell` or `bash` |
| baseUrl | Required. Local API URL with prefix; use `127.0.0.1` |
| planDoc | Plan with endpoint tables and a "Build order" list, or checklists |
| gates | Required commands; default below |
| commitStyle | Message convention |
| lessonWorktreesPath | Default: sibling `<repo-name>-lessons` |
| standingExceptions | `["docstrings"]` or `[]` |

Default gates, run from `appRoot`: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run lint-imports`, `uv run python tools/boundaries.py sync --check`, `uv run python tools/boundaries.py selftest`, `uv run pytest`. Use only those the project has set up. In a monorepo, give commands with `uv run --directory <appRoot>`.

## First run
Read `learn.py scan` output, `git symbolic-ref refs/remotes/origin/HEAD`, and `main.py`. Ask for the rest in one message, with your guesses as defaults. Then:
1. Write the config.
2. Run `git check-ignore learn/`. If it isn't ignored, tell the owner to add `learn/` to `.git/info/exclude`.
3. Scan again.

## Empty repo
With `no_fastapi_app`, the first lesson is `kind: scaffold`. With `no_commits`, give the owner the commands for a first commit, because worktrees need one. Default `appRoot` to `apps/api` if a frontend is planned, otherwise `.`.

## No plan
Offer to draft `docs/plan.md` with the owner, or use `idea-to-plan`. The owner owns and commits it. Use full paths:

```markdown
## 1. Identity
| Method | Path | Auth | Does |
|---|---|---|---|
| POST | `/api/v1/auth/register` | public | Sign up |

## Build order
1. Identity
```
