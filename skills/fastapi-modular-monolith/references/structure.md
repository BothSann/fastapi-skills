# Module structure

```text
src/<package>/
  main.py              # creates the app, includes each module's router
  shared/              # optional; never imports modules
  modules/<module>/
    api.py             # routes, Pydantic schemas, wiring
    infrastructure.py  # SQLAlchemy rows, repositories, clients
    application.py     # use cases with execute(), Protocols, Transaction
    domain.py          # optional; business rules, no third-party imports
    contracts.py       # dataclasses and Protocols other modules may import
```

Each layer starts as one file. Convert it to a package with the same name when it grows.

## Import direction

`api` → `infrastructure` → `application` → `domain` → `contracts`. Lower layers never import higher ones. Layers may skip levels.

- `api` imports `infrastructure` only for wiring. Keep that in `api/dependencies.py` once `api` is a package. Routes call use cases, and the contracts can't enforce this, so `check` reviews it.
- `infrastructure` implements Protocols defined in `application`.
- Other modules import only `contracts`. Only `main.py` imports another module's `api`.
- Omit `domain` for pure CRUD.

## Module communication

Use the first level that works:
1. **Contract:** a Protocol and dataclasses in `contracts.py`, implemented by the owning module and passed in during wiring. Use IDs across modules, with no joins.
2. **In-process event:** a small hand-written bus for side effects, such as `posts` announcing a like. It's synchronous and not durable.
3. **Outbox:** a table written in the same transaction, plus a relay, only when losing an event is unacceptable. Consumers must be idempotent.

## First contract

The owner types this once in `pyproject.toml`. After that, `sync` maintains the block, so keep the markers:

```toml
# BEGIN fastapi-modular-monolith (generated: boundaries.py sync)
[tool.importlinter]
root_package = "<package>"

[[tool.importlinter.contracts]]
name = "module layers"
type = "layers"
layers = ["(api)", "(infrastructure)", "(application)", "(domain)", "(contracts)"]
containers = ["<package>.modules.<module>"]
# END fastapi-modular-monolith
```

Parentheses make a layer optional, so a module can be built one layer at a time.
