# test-readable-by-learner

**MEDIUM-HIGH, agent-owned.** The owner reads these tests and doesn't write them. Name the behaviour, add a one-line docstring, keep Given, When, Then order, and use plain factory functions.

Avoid:
```python
async def test_post_2(client: AsyncClient) -> None:
    assert (await client.post("/posts", json=DATA)).status_code == 201
```

Do:
```python
async def test_author_can_publish_a_post(client: AsyncClient) -> None:
    """A logged-in author gets the created post back."""
    body = post_body(text="hello")
    response = await client.post("/posts", json=body)
    assert response.status_code == 201
```

Source: https://hynek.me/articles/document-your-tests/
