---
name: fastapi-best-practices
description: Write, review, or refactor FastAPI code using ranked async, architecture, database, security, testing, and media rules.
license: MIT
metadata:
  author: BothSann
  version: "0.1.0"
---

# FastAPI rules

45 rules; read only those relevant to the task. Project conventions and installed versions come first, then official FastAPI and Python docs, then these rules. Earlier categories win conflicts. Never choose a tool because it resembles another language's tooling.

Each rule is `rules/<prefix><name>.md`, e.g. `rules/db-explicit-transactions.md`. Do not load the whole directory. For versions and proven stack limits, read [stack.md](references/stack.md).

| Category / impact | Prefix | Names |
|---|---|---|
| Async / CRITICAL | async- | no-blocking-calls, offload-cpu, route-kind, structured-tasks |
| Architecture / CRITICAL | arch- | domain-packages, thin-routes, public-contracts, lifespan-composition, no-cycles |
| DI / CRITICAL | di- | annotated-aliases, constructor-below-edge, yield-teardown, protocol-at-consumer |
| Database / HIGH | db- | session-per-request, no-implicit-io, sqlalchemy-2-style, explicit-driver, explicit-transactions, migrations-reviewed, naming-convention, module-table-ownership, avoid-n-plus-one |
| Errors / HIGH | error- | domain-exceptions, narrow-except |
| Security / HIGH | security- | password-hashing, jwt, authorize-records, response-filtering, cors-docs |
| API / MEDIUM-HIGH | api- | return-annotation, pydantic-at-edge, constrained-input, typed-settings |
| Testing / MEDIUM-HIGH | test- | real-postgres, single-event-loop, overrides-for-edges, readable-by-learner |
| Media / MEDIUM-HIGH | media- | verify-by-decoding, limit-size-pixels, strip-metadata, short-presigned-urls |
| Operations / MEDIUM | ops- | background-vs-queue, structlog-context, toolchain-gate, docker-loopback |
