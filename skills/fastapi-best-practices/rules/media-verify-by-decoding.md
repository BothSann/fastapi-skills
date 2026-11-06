# media-verify-by-decoding

**MEDIUM-HIGH.** Never trust a file name or `Content-Type`. Decode and re-encode on the server, off the event loop. Garbage, SVG, and truncated JPEG, PNG, and WebP files were all caught by the tuple below on Pillow 13.

Avoid:
```python
if file.content_type != "image/jpeg":
    raise InvalidImage
await storage.save(key, await file.read())
```

Do:
```python
try:
    with Image.open(BytesIO(data)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
except (OSError, ValueError, Image.DecompressionBombError) as err:
    raise InvalidImage from err
```

Source: https://pillow.readthedocs.io/en/stable/reference/Image.html
