# async-structured-tasks

**CRITICAL.** `gather` leaves siblings running after a failure, and the loop keeps only weak references to `create_task` tasks. Prefer `TaskGroup` and `timeout`.

Avoid:
```python
asyncio.create_task(send_email(user))
a, b = await asyncio.gather(fetch_a(), fetch_b())
```

Do:
```python
async with asyncio.timeout(5):
    async with asyncio.TaskGroup() as group:
        a = group.create_task(fetch_a())
        b = group.create_task(fetch_b())
```

Source: https://docs.python.org/3/library/asyncio-task.html
