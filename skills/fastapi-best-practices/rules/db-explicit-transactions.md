# db-explicit-transactions

**HIGH.** The use case opens an injected `Transaction` and keeps sqlalchemy out of `application`. Open it before the first query: a read starts a transaction, and `session.begin()` then raises `InvalidRequestError`. Leaving the block commits, and an exception rolls back.

Avoid:
```python
async def execute(self, command: CreatePost) -> None:
    if await self._posts.exists(command.slug):
        raise SlugTaken(command.slug)
    async with self._tx():
        await self._posts.add(Post.new(command))
```

Do:
```python
class Transaction(Protocol):
    def __call__(self) -> AbstractAsyncContextManager[Any]: ...

async def execute(self, command: CreatePost) -> None:
    async with self._tx():
        if await self._posts.exists(command.slug):
            raise SlugTaken(command.slug)
        await self._posts.add(Post.new(command))
```

Source: https://docs.sqlalchemy.org/en/21/orm/session_transaction.html
