---
name: fastapi-modular-monolith
description: Add FastAPI modules, generate import-linter boundaries, prove them with a self-test, or assess an existing app's structure.
license: MIT
metadata:
  author: BothSann
  version: "0.1.0"
---

# FastAPI modular monolith

Sets up structure and checks. Never designs business boundaries, invents modules, or moves existing code unasked. Read [structure.md](references/structure.md) before writing module code. For code-level rules, use installed `fastapi-best-practices`.

## Commands
Copy [scripts/boundaries.py](scripts/boundaries.py) to `<app>/tools/boundaries.py` once, so the gates work without this skill. Run from the app root, or pass `--root <path>` in a monorepo:

| Task | Command |
|---|---|
| Read-only state | `python tools/boundaries.py inspect` |
| New module skeleton | `python tools/boundaries.py add-module <snake_name>` |
| Regenerate contracts after adding or removing a layer | `python tools/boundaries.py sync` |
| Prove the rules fail on bad imports | `uv run python tools/boundaries.py selftest` |
| Check real imports | `uv run lint-imports` |

Requires `import-linter` in dev dependencies. Add `sync --check`, `lint-imports`, and `selftest` to existing gates.

## Steps
1. Run `inspect`. Stop on errors. If several apps are found, ask which one.
2. **No modules:** the first module is built by hand with [structure.md](references/structure.md). During a `fastapi-learn` lesson, the owner types it, and also types the first contract from the same reference.
3. **Later modules:** run `add-module`. It creates empty files and updates contracts, with no business code and no route wiring.
4. **Existing app:** report `inspect` and any `lint-imports` violations, then suggest one first module. Change nothing without a request.
5. Verify `sync --check`, `lint-imports`, `selftest`, and the project's other gates. All must pass.

## Report
Give the mode, changes, module count, contract result, and self-test count. A passing check proves import direction only. It doesn't review design, table ownership, or whether routes stay thin.

Never edit the generated block by hand, add `ignore_imports`, or weaken a contract to pass. If a rule seems wrong, explain it and let the owner decide.
