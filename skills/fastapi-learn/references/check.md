# "check" and "check and fix"

## Review
1. Read the owner's changes: `git diff <base>`, plus `git status` for new files.
2. Run read-only checks from boundaries.md. Give write requests to the owner as commands.
3. Compare in order: ticket criteria, project rules, then the checklist and rule files below. The reference is a guide, not the only valid answer.
4. Report **Right**, **Breaks**, then **Style**, with file:line and why. Say what you ran and didn't run. Don't fix anything.

A Breaks finding needs a rule, a criterion, or proof you ran. A Style finding without a rule is optional or dropped.

## Check and fix
Fix only what the review found. Report a `File:line | Was | Now | Why` table, then rerun the checks.

## Rule files
Load only touched areas, from `fastapi-best-practices/rules/<name>.md`.

| Work | Rules |
|---|---|
| Structure | arch-domain-packages, arch-public-contracts, arch-no-cycles |
| Routes | arch-thin-routes, async-route-kind, api-return-annotation |
| Input | api-constrained-input, api-pydantic-at-edge |
| Output | security-response-filtering, api-return-annotation |
| Use cases | di-constructor-below-edge, di-protocol-at-consumer, error-domain-exceptions |
| Async code | async-no-blocking-calls, async-offload-cpu, async-structured-tasks |
| Dependencies | di-annotated-aliases, di-yield-teardown |
| Queries | db-session-per-request, db-no-implicit-io, db-sqlalchemy-2-style, db-avoid-n-plus-one, db-module-table-ownership |
| Writes | db-explicit-transactions |
| Schema | db-migrations-reviewed, db-naming-convention |
| Startup, config | arch-lifespan-composition, api-typed-settings, db-explicit-driver |
| Auth | security-password-hashing, security-jwt, security-authorize-records |
| Browser access | security-cors-docs |
| Errors | error-domain-exceptions, error-narrow-except |
| Uploads | media-verify-by-decoding, media-limit-size-pixels, media-strip-metadata, media-short-presigned-urls |
| Jobs, logs | ops-background-vs-queue, ops-structlog-context |
| Tests | test-real-postgres, test-single-event-loop, test-overrides-for-edges, test-readable-by-learner |

## Checks that have no rule file

| Area | Check |
|---|---|
| Layers | Routes call use cases. `api` imports `infrastructure` only for wiring. `lint-imports` can't see this. |
| Data | Bounded paging and useful indexes. Unique constraints handle races, with the conflict mapped to 409. |
| Transactions | No slow outside calls inside one. After a Postgres error the transaction is aborted, so catching isn't recovery. |
| Concurrency | Quotas and one-time tokens claim conditionally or under locks. Jobs recheck state and have a final failure state. |
| Contract | Stable keys, dates, and paging. Status codes match the ticket. OpenAPI lists reachable errors. |
| Python | Mutable defaults, `is` on values, unawaited coroutines, naive datetimes, and vague names. |
