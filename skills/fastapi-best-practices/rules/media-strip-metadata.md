# media-strip-metadata

**MEDIUM-HIGH.** Photos can carry GPS location in EXIF. Apply orientation first, because it's stored in EXIF too, and then save without metadata. Check the output in a test rather than assuming it.

Avoid:
```python
Image.open(raw).save(out, "WEBP", exif=Image.open(raw).getexif())
```

Do:
```python
with Image.open(raw) as source:
    upright = ImageOps.exif_transpose(source).convert("RGB")
upright.thumbnail((1080, 1080))
upright.save(out, "WEBP", quality=80)
```

Source: https://pillow.readthedocs.io/en/stable/reference/ImageOps.html
