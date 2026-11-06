# ops-background-vs-queue

**MEDIUM.** `BackgroundTasks` runs in the web process, so a crash loses the work. Use it only for work you can lose. Use a persistent queue, currently taskiq with Redis, and record a status for work that must finish.

Avoid:
```python
background_tasks.add_task(optimize_image, media_id)
```

Do:
```python
media.status = MediaStatus.PENDING
await optimize_image.kiq(media.id)
```

Source: https://fastapi.tiangolo.com/tutorial/background-tasks/
