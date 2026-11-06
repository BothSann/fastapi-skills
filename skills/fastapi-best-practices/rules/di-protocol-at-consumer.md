# di-protocol-at-consumer

**CRITICAL.** Define a `Protocol` in the layer that consumes it, and only where a fake or second implementation earns it. Implementations don't inherit it. Don't wrap everything in an ABC.

Avoid:
```python
class IPostRepository(ABC):
    @abstractmethod
    async def add(self, post: Post) -> None: ...

class SqlPostRepository(IPostRepository): ...
```

Do:
```python
class PostRepository(Protocol):
    async def add(self, post: Post) -> None: ...

class SqlPostRepository:
    async def add(self, post: Post) -> None: ...
```

Source: https://peps.python.org/pep-0544/
