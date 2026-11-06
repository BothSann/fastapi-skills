# di-constructor-below-edge

**CRITICAL.** `Depends` stays in `api`. Lower layers take plain constructor arguments, so they run without FastAPI. Wiring lives in `api` (`api/dependencies.py` once it's a package), the only `api` code that imports `infrastructure`.

Avoid:
```python
class CreatePost:
    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        self._session = session
```

Do:
```python
class CreatePost:
    def __init__(self, posts: PostRepository, tx: Transaction) -> None:
        self._posts = posts
        self._tx = tx

def get_create_post(session: SessionDep) -> CreatePost:
    return CreatePost(SqlPostRepository(session), session.begin)
```

Source: https://fastapi.tiangolo.com/tutorial/dependencies/
