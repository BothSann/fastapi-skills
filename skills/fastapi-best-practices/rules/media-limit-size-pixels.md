# media-limit-size-pixels

**MEDIUM-HIGH.** Limit bytes before reading the rest, and pixels before decoding. A small file can expand hugely in memory. `Image.open` is lazy, so `size` is available before pixel data loads.

Avoid:
```python
data = await file.read()
image = Image.open(BytesIO(data)).convert("RGB")
```

Do:
```python
data = await file.read(MAX_BYTES + 1)
if len(data) > MAX_BYTES:
    raise ImageTooLarge

with Image.open(BytesIO(data)) as source:
    width, height = source.size
    if width * height > MAX_PIXELS:
        raise ImageTooLarge
```

Source: https://pillow.readthedocs.io/en/stable/reference/Image.html
