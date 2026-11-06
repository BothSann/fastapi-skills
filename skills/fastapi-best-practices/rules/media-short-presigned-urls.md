# media-short-presigned-urls

**MEDIUM-HIGH.** Sign each upload for one key, a short expiry, and the declared size. RustFS and SeaweedFS rejected an oversized body when this was checked, and R2 wasn't tested, so the worker must also re-check the stored size.

Avoid:
```python
url = client.generate_presigned_url(
    "put_object", Params={"Bucket": bucket, "Key": name}, ExpiresIn=86400
)
```

Do:
```python
url = client.generate_presigned_url(
    "put_object",
    Params={"Bucket": bucket, "Key": f"raw/{uuid4()}", "ContentLength": size},
    ExpiresIn=300,
)
```

Source: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html
