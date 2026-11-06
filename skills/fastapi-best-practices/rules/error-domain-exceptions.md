# error-domain-exceptions

**HIGH.** Lower layers raise their own exceptions and know nothing about HTTP. One handler in `api` maps them to responses.

Avoid:
```python
class CreatePost:
    async def execute(self, command: Command) -> None:
        raise HTTPException(409, "slug taken")
```

Do:
```python
class SlugTaken(Exception):
    pass

@app.exception_handler(SlugTaken)
async def slug_taken(request: Request, exc: SlugTaken) -> JSONResponse:
    return JSONResponse({"detail": "slug taken"}, status_code=409)
```

Source: https://fastapi.tiangolo.com/tutorial/handling-errors/
