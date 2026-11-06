# FastAPI skills research

Verified 2026-11-06. "Inferred" means read from source or docs, not run. The raw notes, smoke project, and trial project were deleted after their results were recorded here.

Versions (PyPI): fastapi 0.162.0, starlette 1.10.0, uvicorn 0.54.0, pydantic 2.14.3, pydantic-settings 2.16.2, sqlalchemy 2.1.8, alembic 1.20.1, asyncpg 0.32.0, psycopg 3.3.8, uv 0.13.7 (machine: 0.12.0), ruff 0.17.4, mypy 2.4.1, pyright 1.1.414, ty 0.0.99, pytest 9.2.0, pytest-asyncio 1.4.1.post1, anyio 4.16.0, httpx 0.28.1, testcontainers 4.15.0, structlog 26.1.0, taskiq 0.13.0, arq 0.28.0, celery 5.7.0, dramatiq 2.2.1, PyJWT 2.15.1, pwdlib 0.3.1, import-linter 2.15, tach 0.35.3, pytest-archon 0.0.7, dishka 1.10.1, dependency-injector 4.49.1.

Python 3.15 Windows wheels: pydantic-core, asyncpg and psycopg-binary have `cp315-win_amd64`. uvloop has cp315 wheels for macOS and Linux only; [asyncpg's CI says "uvloop does not support windows"](https://raw.githubusercontent.com/MagicStack/asyncpg/master/.github/workflows/tests.yml) and [uvicorn skips it on win32](https://github.com/encode/uvicorn/blob/master/pyproject.toml).

## A. Decisions

| Decision | Options | Recommendation | Why | Source |
|---|---|---|---|---|
| Python version | 3.15.x, 3.14.x, 3.13 | **3.15** (`requires-python = ">=3.15,<3.16"`). Python has no LTS; 3.15 is supported to about Oct 2031. | The full stack passed on 3.15.1. `fastapi[standard]` only backtracks to 0.110.3 in a wheels-only resolve, because pyyaml 6.0.3 has no cp315 wheel; a normal install builds PyYAML from source. The skills use plain `fastapi`, so this does not arise. | Section F, [PEP 790](https://peps.python.org/pep-0790/) |
| ORM | SQLAlchemy 2.1, SQLModel, raw asyncpg | **SQLAlchemy 2.1** `Mapped[]`, `sqlalchemy[asyncio]`, Alembic `async` template | SQLModel (0.0.x) merges table and schema classes, which works against layering. 2.1 no longer installs greenlet by default and needs the extra. | [2.1 migration](https://docs.sqlalchemy.org/en/21/changelog/migration_21.html), [Alembic cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html) |
| DB driver | asyncpg, psycopg async | **asyncpg, with an explicit `postgresql+asyncpg://`** | Psycopg async rejects Windows' default ProactorEventLoop. Uvicorn picks Proactor unless using a subprocess, so psycopg could pass under reload and fail under plain run (inferred). Bare `postgresql://` means psycopg in 2.1. asyncpg's CI covers windows-2025. | [psycopg](https://www.psycopg.org/psycopg3/docs/advanced/async.html), [uvicorn loop](https://github.com/Kludex/uvicorn/blob/main/uvicorn/loops/asyncio.py), [asyncpg CI](https://raw.githubusercontent.com/MagicStack/asyncpg/master/.github/workflows/tests.yml) |
| Sync vs async | async, sync, mixed | **Async end to end**, guarded by ruff `ASYNC`, `lazy="raise"`, `expire_on_commit=False` | Matches the owner's Node event-loop model. Trade-off: docs say "if you just don't know, use normal def", and the official template is sync. | [FastAPI async](https://fastapi.tiangolo.com/async/), [SQLAlchemy asyncio](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html) |
| DI | Depends, dishka, dependency-injector | **`Annotated[T, Depends]` at the api edge; plain constructors below it.** dishka only as a later opt-in. | No extra dependency; a real FastAPI modular starter made this choice. dishka's critique holds (FastAPI-only, per-level declaration), but it is a rival's claim. dependency-injector lacks autowiring and per-request caching, per dishka. | [dishka alternatives](https://dishka.readthedocs.io/en/stable/alternatives.html), [starter kit](https://github.com/arctikant/fastapi-modular-monolith-starter-kit) |
| Boundary tool | import-linter, tach, pytest-archon | **import-linter** `layers` with `containers` and optional `(domain)`, plus `independence`/`protected`; add a NestJS-style self-test | Pushed 2026-11-06; Stable classifier; Windows smoke test in CI; cp315 grimp wheel; proven at Kraken (27,637 modules, 40+ contracts). tach: active but Beta and blocked on 3.15 by pyyaml. pytest-archon: no push since 2025-09, 92 stars. | [layers](https://import-linter.readthedocs.io/en/stable/contract_types/layers/), [CI](https://raw.githubusercontent.com/seddonym/import-linter/main/.github/workflows/main.yml), [Kraken](https://blog.europython.eu/kraken-technologies-how-we-organize-our-very-large-pythonmonolith/) |
| Layering depth | flat Dispatch, 3-tier, full 5 layers | **Fixed names: `api`, `application`, `domain` (optional), `infrastructure`, `contracts`.** Each starts as one file and becomes a package when it grows. Omit `domain` for pure CRUD. | Keeps the NestJS skill's vocabulary. Cosmic says CRUD wrappers need no domain model. Optional layers are native to import-linter. | [Cosmic ch2](https://www.cosmicpython.com/book/chapter_02_repository.html), [layers](https://import-linter.readthedocs.io/en/stable/contract_types/layers/) |
| Repository / UoW | generic base, per-aggregate, none, full UoW | **Concrete repository per aggregate where `domain` exists; no generic base. No repository-holding UoW:** one shared `Transaction` Protocol (~10 lines over `session.begin()`) keeps sqlalchemy out of `application`. | Cosmic: a repository costs indirection, passing a session around often goes far, and `Session` already is a UoW; a narrow interface is its reason to wrap. The starter kit injects `AsyncSession` into services and admits this breaks isolation. | [Cosmic ch6](https://www.cosmicpython.com/book/chapter_06_uow.html), [starter kit](https://github.com/arctikant/fastapi-modular-monolith-starter-kit) |
| Commit placement | yield teardown, use case, `scope="function"` | **The use case opens the injected `Transaction`**; never commit in yield teardown | Yield exit code runs after the response is sent by default, so a teardown commit can fail after a 200 (inferred). | [yield docs](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/) |
| Module communication | direct imports, contracts, events, outbox | **Ladder: (1) `contracts` DTOs and Protocol for queries and commands; (2) hand-written in-process bus for side effects, ~30 lines; (3) outbox table and relay only when loss is unacceptable, with idempotent consumers.** IDs across modules, no joins. | Cosmic's bus is synchronous and not a task queue. fastapi-events last released 2024-12. | [Cosmic ch8](https://www.cosmicpython.com/book/chapter_08_events_and_message_bus.html), [outbox](https://microservices.io/patterns/data/transactional-outbox.html), [public_api example](https://github.com/deadislove/fastapi-modular-monolith-template) |
| Type checker | mypy, pyright, ty | **`mypy --strict`** | Python's reference type checker, and what the official FastAPI template uses. pyright was first recommended for resembling `tsc`, then rejected: the owner's rule is that tools are never chosen for similarity to TypeScript. ty is beta. | [template](https://github.com/fastapi/full-stack-fastapi-template/blob/master/backend/pyproject.toml), [ty](https://github.com/astral-sh/ty/blob/main/README.md) |
| Test stack | TestClient, pytest-asyncio, anyio plugin | **pytest + anyio plugin (`anyio_mode="auto"`, session-scoped `anyio_backend="asyncio"`) + `httpx.AsyncClient`/`ASGITransport` + testcontainers Postgres + savepoint rollback + plain factory functions.** One command: `uv run pytest`. Fallback: pytest-asyncio, auto mode, session loop scope. | Reads cleanly (no markers, `async def` only); anyio comes with Starlette; FastAPI's own docs use it; anyio warns pytest-asyncio splits fixture setup and teardown across tasks. Real DB, since mocks hide SQL. Docker 29.6.2 is running here. Sync TestClient can't share an async fixture's loop (inferred). | [async tests](https://fastapi.tiangolo.com/advanced/async-tests/), [anyio](https://anyio.readthedocs.io/en/stable/testing.html), [savepoints](https://docs.sqlalchemy.org/en/21/orm/session_transaction.html), [Hynek on documenting tests](https://hynek.me/articles/document-your-tests/) |
| Job queue | taskiq, arq, celery, dramatiq | **`BackgroundTasks` for work you can lose; taskiq with Redis otherwise**, first used for image optimization in `media`. | Taskiq is asyncio-native with `taskiq-fastapi`, but classified Alpha. Celery: "Windows is no longer supported". Arq: Redis-only, pickle default. Dramatiq: LGPL, and taskiq itself steers sync projects there. Worker tested in the smoke run. | [Celery FAQ](https://docs.celeryq.dev/en/stable/faq.html), [arq](https://arq-docs.helpmanual.io/), [taskiq](https://taskiq-python.github.io/guide/) |
| Auth | PyJWT, pwdlib, python-jose, passlib | **PyJWT + `pwdlib[argon2]`**, with the dummy-hash timing defence; offload hashing from `async def` | Current FastAPI docs. | [JWT tutorial](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) |
| Object storage | R2, S3, SeaweedFS, RustFS | **Cloudflare R2 once deployed; RustFS locally, for development only (1.0 beta)**, behind a `Storage` Protocol using boto3 through `asyncio.to_thread`. | SeaweedFS's first write took 11-15s per fresh container against RustFS's 0.1s, and its image was larger (735 MB vs 419 MB). | Section F |
| Image uploads | client or server optimization | **The server always optimizes, in a worker:** decode, strip metadata, resize, WebP. Avatars at most 5 MB through `UploadFile`; post images at most 10 MB through presigned URLs. | Clients can't be trusted to send safe or small files. | Section F |
| Layer order | `api` beside or above `infrastructure` | **`api` above `infrastructure`.** `api` imports `infrastructure` only for wiring, which review checks because contracts can't. | The smoke project's `api : infrastructure` contract blocked wiring. | Section F |
| Skill shape | large vs routed | **Description ~50 tokens; SKILL.md ~500-850; one-level refs; keep versions in one file; script deterministic checks; 3 evals first.** Keep one `fastapi-learn` skill, with routes for pick, write, done, and check. | Anthropic: ~100 tokens metadata, under 5k body, under 500 lines, no time-sensitive text. NestJS measured: entrypoints cut 62-78%; coach-done 10,652 to 3,266 through routing; reading a 187-token settings block instead of 1,702. These are instruction counts, not runtime usage. | [overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview), [best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), NestJS skills' token benchmark |

## B. First rule inventory (40, ranked)

The skill ships 45 rules, and its index is the current list. This was the starting inventory.

**Async / CRITICAL**
- `async-no-blocking-calls`: no blocking I/O in `async def`; ruff `ASYNC` enforces.
- `async-offload-cpu`: `to_thread` for hashing and sync SDKs; a worker for heavy CPU.
- `async-route-kind`: choose `async def` or `def` per route, never a sync driver inside async.
- `async-structured-tasks`: `TaskGroup` over `gather`; keep task references; use `timeout()`.

**Architecture / CRITICAL**
- `arch-domain-packages`: package by business domain, not file type.
- `arch-thin-routes`: routes parse, call one use case, and map the result.
- `arch-public-contracts`: other modules import only `contracts`.
- `arch-lifespan-composition`: create engine and clients in `lifespan`, none at import.
- `arch-no-cycles`: fix import cycles by moving code, not hiding imports in functions.

**Dependency injection / CRITICAL**
- `di-annotated-aliases`: reusable `Annotated[T, Depends(...)]`; ruff `FAST002`.
- `di-constructor-below-edge`: no `Depends` below `api`.
- `di-yield-teardown`: re-raise in yield dependencies; no commit in teardown.
- `di-protocol-at-consumer`: define a Protocol only where a second implementation or fake earns it.

**Database / HIGH**
- `db-session-per-request`: one `AsyncSession` per request, never shared across tasks.
- `db-no-implicit-io`: `lazy="raise"`, `selectinload`, `expire_on_commit=False`.
- `db-sqlalchemy-2-style`: `Mapped[]` and `select()`, no legacy `Query`.
- `db-explicit-driver`: `postgresql+asyncpg://`; dispose the engine at shutdown.
- `db-explicit-transactions`: the use case opens the injected `Transaction`.
- `db-migrations-reviewed`: Alembic async; read every autogenerated diff; static and reversible.
- `db-naming-convention`: `MetaData(naming_convention=...)` from the first migration.
- `db-module-table-ownership`: only the owning module touches its tables; cross-module by ID.
- `db-avoid-n-plus-one`: eager-load or shape reads in SQL.

**Errors / HIGH**
- `error-domain-exceptions`: domain raises its own errors; one handler maps to HTTP.
- `error-narrow-except`: no broad `except`; use `raise ... from`.

**Security / HIGH**
- `security-password-hashing`: `pwdlib[argon2]` with a dummy hash for unknown users.
- `security-jwt`: PyJWT, pinned `algorithms`, expiry checked.
- `security-authorize-records`: deny by default; check ownership per record.
- `security-response-filtering`: separate In and Out schemas; never return ORM rows.
- `security-cors-docs`: explicit CORS origins; expose docs per environment.

**API and Pydantic / MEDIUM-HIGH**
- `api-return-annotation`: prefer a return type over `response_model`; ruff `FAST001`.
- `api-pydantic-at-edge`: Pydantic in `api`; stdlib dataclasses in `application`, `domain`, and `contracts`.
- `api-constrained-input`: `Field`, `StrEnum`, `extra="forbid"` on inputs.
- `api-typed-settings`: per-module `BaseSettings` behind a cached dependency.

**Testing / MEDIUM-HIGH (agent-owned)**
- `test-real-postgres`: testcontainers with savepoint rollback; no SQLite stand-in.
- `test-single-event-loop`: session-scoped backend; create loop-bound objects inside fixtures.
- `test-overrides-for-edges`: `dependency_overrides` for auth and third parties only.
- `test-readable-by-learner`: behaviour names, one-line docstring, Given/When/Then, plain factories.

**Operations / MEDIUM**
- `ops-background-vs-queue`: `BackgroundTasks` only for work you can lose.
- `ops-structlog-context`: `merge_contextvars`; clear per request in middleware.
- `ops-toolchain-gate`: `uv.lock`, ruff, `mypy --strict`, lint-imports, pytest; one uvicorn process per container.

## C. Python idioms for a TypeScript developer

- Annotations aren't enforced at runtime by Python; only Pydantic and FastAPI read them.
- Default arguments are built once: [never `def f(x=[])`](https://docs.python.org/3/faq/programming.html#why-are-default-values-shared-between-objects); ruff `B006`.
- [Loop closures bind late](https://docs.python.org/3/faq/programming.html#why-do-lambdas-defined-in-a-loop-with-different-values-all-return-the-same-result); `let` in a TS loop does not.
- Coroutines are lazy, promises are eager: [unawaited `f()` never runs](https://docs.python.org/3/library/asyncio-dev.html).
- [Keep `create_task` references](https://docs.python.org/3/library/asyncio-task.html): the loop holds weak references, so tasks can vanish.
- [`gather` doesn't cancel siblings on failure; `TaskGroup` does](https://docs.python.org/3/library/asyncio-task.html).
- `async` doesn't make CPU work concurrent; [blocking code stalls every request](https://docs.python.org/3/library/asyncio-dev.html).
- There's one `None`, no `undefined`; `x: int | None` still needs `= None` to be omittable.
- `[]` and `{}` are falsy, unlike JS; [use `is None` to test for None](https://google.github.io/styleguide/pyguide.html#214-truefalse-evaluations).
- `==` compares value and `is` compares identity; never use `is` for strings or numbers.
- `d["k"]` raises `KeyError`; `.get()` is the `?.` equivalent. Missing attributes raise too.
- Protocol is TS-style structural typing; [classes needn't inherit it](https://peps.python.org/pep-0544/). Plain classes are nominal.
- [Prefer Protocol over ABC, and composition over subclassing](https://hynek.me/articles/python-subclassing-redux/); no `@Injectable()` decorators.
- `_name` is a convention; there's no `private`. [Public attributes beat trivial getters](https://google.github.io/styleguide/pyguide.html#315-getters-and-setters).
- Modules are singletons, and import executes top-level code; keep it free of I/O.
- [Circular `from x import y` fails at import time](https://docs.python.org/3/faq/programming.html#what-are-the-best-practices-for-using-import-in-a-module), unlike TS elided type imports.
- `__init__.py` is the barrel file; use `__all__` and absolute imports ([Google §2.2](https://google.github.io/styleguide/pyguide.html#22-imports)).
- [Exceptions are normal flow](https://google.github.io/styleguide/pyguide.html#24-exceptions): narrow `except`, small `try`; no `assert` for validation.
- Use `raise New() from err` to keep the cause; a bare `raise` re-raises.
- `with`/`async with` is the resource pattern, not `try/finally` boilerplate.
- [`datetime.utcnow()` is deprecated](https://docs.python.org/3.14/library/datetime.html); use `datetime.now(UTC)`. Ruff `DTZ` catches naive datetimes.
- Dataclass for internal data, Pydantic for untrusted input. Pydantic coerces unless strict.
- `/` always yields float and `//` floors; ints are arbitrary precision, no `Number`.
- `*` forces keyword-only arguments, the options-object equivalent; slices copy, spread-like.
- Comprehensions replace `.map/.filter` chains; [keep them simple](https://google.github.io/styleguide/pyguide.html#27-comprehensions--generator-expressions).
- Python 3.14: [deferred annotations, and `except A, B:` without brackets](https://docs.python.org/3.14/whatsnew/3.14.html), valid syntax rather than a Python 2 relic.

## D. Where sources disagree

**zhanymkanov/fastapi-best-practices (commit 5e00aa6, 2026-05): NO LICENCE.** No file, and the GitHub API returns null. Use ideas only; do not copy text or code. Flags:

- *Outdated:* response "constructed twice" and the AGENTS anti-pattern. [Current source](https://github.com/fastapi/fastapi/blob/master/fastapi/routing.py) validates then serializes (Rust since 0.130), and [`revalidate_instances` defaults to `never`](https://pydantic.dev/docs/validation/latest/api/pydantic/config/). Likely stale (inferred); the log is dated 2022.
- *Outdated:* README uses default-arg `Depends`, `encode/databases`, `requirements/*.txt` and `populate_by_name` ([not recommended since 2.11](https://pydantic.dev/docs/validation/latest/api/pydantic/config/)); `get_db` is mistyped as returning `AsyncSession`.
- *Incomplete:* plain async fixtures with `pytest.mark.asyncio` need auto mode (inferred from [mode docs](https://pytest-asyncio.readthedocs.io/en/stable/concepts.html)). The compatibility table's minimums lag current releases.
- *Conflicts with layering:* `from src.auth import service` across modules; dependencies doing DB validation and ownership checks in the HTTP layer; dict-typed services; ORM models as the domain; global `settings = Config()` at import.
- *Keep:* async trust model, per-domain settings, naming conventions, BackgroundTasks limits, real DB in tests. `Prefer async deps`: for cheap non-I/O checks only.

Other conflicts:

- **Structure:** official template is layer-based (`api/routes`, `crud.py`, `models.py`) with sync SQLModel; [Dispatch is archived](https://github.com/Netflix/dispatch) and domain-flat. Neither is a modular monolith. Use Dispatch for package shape only.
- **Settings:** [FastAPI docs prefer `lru_cache` + Depends](https://fastapi.tiangolo.com/advanced/settings/); zhanymkanov uses module globals. Choose the former, since it can be overridden.
- **`async def` vs `def`:** FastAPI's default-when-unsure is `def`; zhanymkanov says prefer async dependencies. [Sync dependencies run in the threadpool](https://fastapi.tiangolo.com/async/). Both are true; the async stack decides here.
- **Tests:** FastAPI's main page teaches [sync TestClient](https://fastapi.tiangolo.com/tutorial/testing/), its advanced page anyio; community starters use pytest-asyncio.
- **Imports:** [Google bans relative imports and imports modules only](https://google.github.io/styleguide/pyguide.html#22-imports); [FastAPI's tutorial uses relative imports](https://fastapi.tiangolo.com/tutorial/bigger-applications/). Choose absolute, as boundary contracts read better.
- **Domain/ORM split:** Cosmic uses imperative mapping; the 2.x default is declarative `Mapped`. Choose declarative plus explicit mappers, for typing and learnability (judgment).
- **Result vs exceptions:** the [deadislove template](https://github.com/deadislove/fastapi-modular-monolith-template) returns `Result`; Google and Python idiom use exceptions. Choose exceptions.
- **Mocks:** zhanymkanov rejects DB mocks; Cosmic favours in-memory fakes. Use both: fakes for pure `domain`/`application`, real Postgres for the rest.

## E. Not verified

- **Psycopg on Windows** was never run; the skills use asyncpg, so it isn't needed.
- **`fastapi[standard]` on 3.15:** installs, by building PyYAML from source, but the test suite hasn't run against it.
- **Psycopg reload vs run** behaviour is read from source.
- **Effective Python, Fluent Python:** not read; no claims rest on them. PEP 8/20/484 not re-read; rules come via Google's guide, PEP 544 and Python docs.
- **ty:** Pydantic and SQLAlchemy support depth unknown, no conformance numbers. Astral's speed figures are vendor claims.
- **tach:** "active" rests on push date and release; commit authorship not checked (API rate-limited). pytest-archon Windows support unstated. Arq's "not actively maintained" is taskiq's claim.
- **Celery 5.7 asyncio** and **dishka's FastAPI integration:** pages not read. Dishka's comparison is self-published; [one benchmark](https://maldoinc.github.io/wireup/latest/benchmarks) is from a competitor.
- **Partial reads:** long pages (release notes, Google guide, ruff rules, 3.15 what's new) were read in part or by grep.
- **Python modular-monolith repos are small** (4 and 56 stars): patterns, not proof.

## F. Smoke test results (2026-11-06)

Full suite passed 20/20 twice on SeaweedFS and 20/20 twice on RustFS on Python 3.15.1, Windows 11, uv 0.12.0. `ruff`, `ruff format`, `mypy --strict`, and `lint-imports` were clean. Verified with real containers: FastAPI under plain and `--reload` uvicorn, asyncpg, savepoint rollback, Alembic autogenerate/`--sql`/upgrade/check, Pillow (WebP, AVIF, GPS stripped, non-image and pixel limit rejected), `UploadFile` limits, boto3 presigned PUT, tampered signature rejected, taskiq worker with Redis, src layout with `uv_build`, and import-linter failing on bad imports.

Findings for the skills:
- **Use `127.0.0.1`, never `localhost`, for Docker services on this machine.** `localhost` connects took about 21s against 0.03s, on both event loops. testcontainers returns `localhost`, so tests must replace it.
- Plain uvicorn runs ProactorEventLoop; `--reload` runs `_WindowsSelectorEventLoop`. asyncpg works on both.
- Import from `testcontainers.community.*`; the old paths are deprecated.
- One import-linter `protected` contract per module. A shared contract let modules import each other's internals, and only the negative test caught it.
- First SeaweedFS write took 11-15s per fresh container. RustFS took 0.1s, so RustFS was chosen.
- Signed `Content-Length` blocked an oversized presigned PUT (403) on both containers.
- Reading before `session.begin()` raises `InvalidRequestError`. `session.begin` works under a savepoint, and an exception rolls it back. `lazy="raise"` raises.
- A shared session under `gather` did not error here, so that rule says "documented unsafe; passing once proves nothing".
- A failing yield teardown still returned 200. `openapi_url=None` keeps `app.openapi()` working.
- PyJWT rejects a missing `exp` and `alg: none`. Pillow errors are caught by `(OSError, ValueError, Image.DecompressionBombError)`.
- Windows Smart App Control blocked a generated `lint-imports.exe` in uv's throwaway environment once (WinError 4551; later runs passed). It was not bypassed, and `boundaries.py` now reports it and says not to work around it.

Not verified: real R2 (the worker's size re-check stays), real photos (the 9.8 MB to 183 KB result is synthetic noise resized to 1080px), `fastapi[standard]` under this suite, Python 3.15.2, uv 0.13, load or production behaviour.

## G. Trial results (2026-11-06)

Two lessons on a disposable project, each with the reference built in a detached worktree. A script acted as the learner: it read each step with `learn.py step`, typed the code, ran the commands, and ran the step's check. No real agent session or person took part, so wording and pacing are still untested.

| Lesson | Steps | Guide tokens | Step checks | Learner vs reference | Gates |
|---|---|---|---|---|---|
| 01 scaffold, health route | 6 | 1,768 | all passed; server answered `{"status":"ok"}` | identical | all passed, 2 tests |
| 02 create a post, database, first migration | 6 | 2,377 | all passed | identical, except the generated revision ID | all passed, 7 tests |

The largest `done` turn was 1,787 tokens with one step, against 3,731 if it had read the whole guide.

Planted mistakes, each caught by the expected check:

| Mistake | Caught by |
|---|---|
| Unknown fields allowed | pytest |
| Empty text allowed | pytest |
| Column added with no migration | pytest, `command.check` |
| Importing another module's internals | lint-imports |
| `application` importing `infrastructure` | lint-imports |
| `time.sleep` in an async route | ruff `ASYNC251` |
| Broad `except` | ruff `BLE001` |
| Wrong return type | mypy |
| Missing transaction | pytest, new commit test |
| Session factory never created | pytest, new commit test |

Bugs the trial found, now fixed:
- `uv init` adds no `.gitignore` inside an existing repo, so `__pycache__` was committed. The scaffold now starts with one.
- Alembic's generated files failed `ruff`. The fix is Alembic's ruff `post_write_hooks`.
- `create_all` in tests hid a forgotten migration. Tests now build the schema with `alembic upgrade head` and call `command.check`.
- Savepoint rollback hid a missing commit, so a post could be lost while every test passed. Each write route now also gets a test using the real `lifespan` and a second connection.
- The scanner listed every finished lesson and called `gh` for each. It now counts them, and calls `gh` only for in-progress lessons.
- A simulator bug counted a missing guide as a pass. That was in the trial script, not the skills, and the affected results were rerun.

Cleanup removed both worktrees (193 MB) and the empty parent folder, and left `learn/` in place. No trial containers remained. It kept worktrees when the merge state was unknown, and unit tests confirm it refuses paths that aren't its own worktrees.

Not run: `check-yourself.md` wasn't written in the trial; the `check` and `ship` routes were exercised through their commands, not through an agent's judgement; merged-PR cleanup used stubbed `gh` output, with the real command's JSON shape confirmed against a public repo.
