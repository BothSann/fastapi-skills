# security-authorize-records

**HIGH.** Being logged in isn't permission. Check ownership per record in the use case, and return 404 when existence itself is private.

Avoid:
```python
post = await posts.get(post_id)
await posts.delete(post)
```

Do:
```python
post = await posts.get(post_id)
if post is None or post.author_id != actor.id:
    raise PostNotFound(post_id)
await posts.delete(post)
```

Source: https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/
