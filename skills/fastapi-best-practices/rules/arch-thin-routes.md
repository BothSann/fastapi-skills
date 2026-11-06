# arch-thin-routes

**CRITICAL.** A route parses input, calls one use case, and maps the result. Business rules and queries live below it.

Avoid:
```python
@router.post("/posts", status_code=201)
async def create(body: PostIn, session: SessionDep) -> PostOut:
    if await session.scalar(select(Post).where(Post.slug == body.slug)):
        raise HTTPException(409)
    ...
```

Do:
```python
@router.post("/posts", status_code=201)
async def create(body: PostIn, use_case: CreatePostDep) -> PostOut:
    return PostOut.from_result(await use_case.execute(body.to_command()))
```

Source: https://fastapi.tiangolo.com/tutorial/bigger-applications/
