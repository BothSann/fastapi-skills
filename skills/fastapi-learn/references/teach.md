# How to teach

Show the idea in plain Python first when it helps, then what FastAPI adds. Use this project's names and real output.

## Python concepts ledger
`learn/python-concepts.md` holds each idiom once. Search headings with `grep`; don't read the whole file. Add an entry only the first time an idea appears, and link to it afterwards. Keep it plain and short:

````markdown
## Context manager (`with`)
Sets something up, then always cleans it up, even after an error.
TS: like `try/finally`, but the object owns the cleanup.
```python
async with session.begin():
    session.add(post)
```
Trap: leaving the block ends the transaction, so finish your writes inside it.
Seen in: lesson 03
````

Common TS traps to cover when they appear:
- Annotations aren't enforced at runtime; only Pydantic and FastAPI read them.
- Coroutines are lazy, so an unawaited call never runs.
- `def f(x=[])` shares one list between calls.
- `[]` and `{}` are falsy, so use `is None` for absence.
- `x: int | None` still needs `= None` to be optional.
- `d["k"]` raises; `.get()` is the `?.` equivalent.
- Modules run top to bottom on import, so keep them free of I/O.
- Closures in loops bind late.
- `/` always gives a float.
- `except A, B:` is valid from Python 3.14.

## Open the magic once
| Magic | Show it with |
|---|---|
| `Depends` | Print inside a dependency: it runs once per request, and its result is cached within that request |
| Pydantic validation | Send a bad body: the 422 comes before the route runs |
| `lifespan` | Print before and after `yield`: startup and shutdown |
| `async def` vs `def` | Add `time.sleep(5)` to a route in the worktree and watch other requests wait |
| Decorators | `@router.get("/x")` is a function call that registers the route on import |
| SQLAlchemy | `create_async_engine(url, echo=True)` shows the real SQL |

## Layers, the first time
| Layer | One line |
|---|---|
| `api` | Reads the request, calls one use case, shapes the answer |
| `application` | The steps of a use case, and the Protocols it needs |
| `domain` | Business rules with no framework |
| `infrastructure` | SQLAlchemy rows, repositories, and outside clients |
| `contracts` | What other modules may import |

## Notes
For "explain in the learn folder", write `learn/notes/<idea>.md`: the question, a plain answer, a small code sample, and one "try it" command. Link it from the lesson README.
