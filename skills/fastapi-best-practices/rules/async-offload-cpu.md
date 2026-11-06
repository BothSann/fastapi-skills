# async-offload-cpu

**CRITICAL.** CPU work blocks the loop too. Use `asyncio.to_thread` for short work in libraries that release the GIL, such as Pillow and argon2. Send long or pure-Python work to a job worker.

Avoid:
```python
async def login(body: LoginIn) -> Token:
    ok = hasher.verify(body.password, stored_hash)
```

Do:
```python
async def login(body: LoginIn) -> Token:
    ok = await asyncio.to_thread(hasher.verify, body.password, stored_hash)
```

Source: https://docs.python.org/3/library/asyncio-dev.html
