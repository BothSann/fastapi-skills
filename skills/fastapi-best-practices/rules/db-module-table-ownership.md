# db-module-table-ownership

**HIGH.** Only the owning module touches its tables. Refer to other modules by ID and read through their contract, with no cross-module joins or ORM relationships.

Avoid:
```python
stmt = select(Post, User).join(User, Post.author_id == User.id)
```

Do:
```python
posts = await self._posts.recent(limit)
authors = await self._users.summaries({post.author_id for post in posts})
```

Source: https://www.cosmicpython.com/book/chapter_08_events_and_message_bus.html
