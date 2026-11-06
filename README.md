# FastAPI skills

[![CI](https://github.com/BothSann/fastapi-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/BothSann/fastapi-skills/actions/workflows/ci.yml)

Agent skills for learning FastAPI, and Python along the way, by typing real projects yourself. You write the app. The agent teaches one step at a time, proves a reference solution, writes the tests, and reviews your code.

The skills teach a modular monolith with clean layers, and they're built to use few tokens.

## Skills

| Skill | Use it to |
|---|---|
| `fastapi-learn` | Pick a task, get a proven lesson, and be coached while you type it |
| `fastapi-best-practices` | Write or review FastAPI code against 45 small rules |
| `fastapi-modular-monolith` | Add modules and enforce their boundaries with `import-linter` |

## Install

```bash
npx skills add BothSann/fastapi-skills
```

Node is needed only for this install command and the token benchmark. The skills' scripts use the Python standard library.

To build the lessons' stack you also need [uv](https://docs.astral.sh/uv/), Docker for throwaway Postgres, Git, and optionally the GitHub CLI, `gh`, which lets the agent see merged PRs.

## How a lesson works

1. **"What next?"** The agent scans your project, offers up to three tasks, and writes a ticket for the one you pick.
2. **"Write the lesson."** In a separate Git worktree, the agent builds the whole solution and proves it against throwaway Postgres. It then writes the guide and copies the failing tests into your project.
3. **You type.** Each step takes 5–15 minutes and explains What, Why, When, and How, with a command that checks it.
4. **"Ship it."** You run the gates, commit, and open the PR. After the merge, the agent deletes the lesson's worktree.

| You say | The agent |
|---|---|
| `done` | Checks the step, then gives the next one |
| `check` | Reviews your code without changing it |
| `check and fix` | Reviews, fixes what it found, and shows what changed |
| `you write it: <item>` | Writes that one item and explains it |
| `ship it` | Walks you through proof, gates, commits, and the PR |

Paste an error or ask a question at any time, and you'll get the root cause and the smallest fix.

You type all app code, including models, and run every migration and commit. The agent writes the tests and, if you turn them on, docstrings.

Python ideas go into `learn/python-concepts.md` the first time they appear, in plain words with a TypeScript comparison.

## Stack taught

Python 3.15, uv, ruff, `mypy --strict`, async SQLAlchemy 2.1, asyncpg, Alembic, `import-linter`, pytest with anyio and testcontainers, PyJWT, `pwdlib[argon2]`, structlog, taskiq, Pillow, and S3-compatible storage. Proven versions and limits are in [stack.md](skills/fastapi-best-practices/references/stack.md).

Works in a monorepo: the agent finds the app with a `pyproject.toml` depending on `fastapi`, and stays inside it.

## Token use

Limits are tested in `scripts/check-tokens.mjs`, counted with `o200k_base`.

| Loaded for | Limit | Measured |
|---|---|---|
| A skill's description | 40 | 38 at most |
| `done`, including the current step | 1,800 | 1,787 at most |
| `check` | 3,000 | 1,669 |
| Picking a task | 2,000 | 1,563 |
| Writing a lesson | 5,000 | 2,749 |
| A rule file | 350 | 251 at most |
| A lesson guide | 4,000 | 2,377 |

These count the instructions an agent reads, not a whole session. During coaching, `learn.py step` prints one guide step, so the rest stays unread.

## What's been tested

- Claude Code, on one Windows 11 machine, with Python 3.15.1 and uv 0.12.0. Other agents should work, but they're untested. macOS and Linux are untested too.
- A scripted two-lesson trial on a disposable project: a learner script typed each step from the guide, and every step check passed. Its code matched the reference, and the gates caught all 10 mistakes planted on purpose.
- The full stack, against real containers. Details and known gaps are in [docs/research.md](docs/research.md).
- This repo's own tests, lint, and token budgets, on every push and PR, on Linux and Windows. This doesn't run a lesson on Linux.

Not tested: a person completing a lesson, real Cloudflare R2, real photos, or production load. Merged-PR cleanup was tested with stubbed `gh` output.

## Disk use

The agent removes a lesson's worktree, including its `.venv`, once its PR is merged. Your `learn/NN-slug/` notes stay. uv keeps a shared package cache, which you can shrink with `uv cache prune`.

## Development

```bash
python -m unittest discover -s tests
cd scripts && npm ci && node check-tokens.mjs
```

## Credits

Some rule ideas came from reading [zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices). That repo has no licence, so no text or code was copied from it. Each rule links to its official source.

## Licence

[MIT](LICENSE)
