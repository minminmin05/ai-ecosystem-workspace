from typing import Iterator

from fastapi import HTTPException, UploadFile, status
from minio import Minio
from minio.error import S3Error

from core.config import settings


client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)


def _raise_from_s3_error(exc: S3Error) -> HTTPException:
    status_code = getattr(exc.response, "status", None) or status.HTTP_500_INTERNAL_SERVER_ERROR
    return HTTPException(status_code=status_code, detail=exc.message or exc.code)


def ensure_bucket() -> None:
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def list_objects() -> list[dict]:
    objects = client.list_objects(settings.minio_bucket, recursive=True)
    return [
        {
            "object_name": obj.object_name,
            "size": obj.size,
            "etag": obj.etag,
            "last_modified": obj.last_modified,
        }
        for obj in objects
    ]


def upload_object(object_name: str, file: UploadFile) -> dict:
    try:
        client.put_object(
            settings.minio_bucket,
            object_name,
            data=file.file,
            length=-1,
            part_size=10 * 1024 * 1024,
            content_type=file.content_type or "application/octet-stream",
        )
        stat = client.stat_object(settings.minio_bucket, object_name)
    except S3Error as exc:
        raise _raise_from_s3_error(exc) from exc
    return {
        "object_name": object_name,
        "size": stat.size,
        "etag": stat.etag,
        "last_modified": stat.last_modified,
    }


def download_object(object_name: str) -> Iterator[bytes]:
    try:
        client.stat_object(settings.minio_bucket, object_name)
        response = client.get_object(settings.minio_bucket, object_name)
    except S3Error as exc:
        raise _raise_from_s3_error(exc) from exc

    def iterator() -> Iterator[bytes]:
        try:
            for chunk in response.stream(32 * 1024):
                yield chunk
        finally:
            response.close()
            response.release_conn()

    return iterator()


def delete_object(object_name: str) -> None:
    try:
        client.stat_object(settings.minio_bucket, object_name)
        client.remove_object(settings.minio_bucket, object_name)
    except S3Error as exc:
        raise _raise_from_s3_error(exc) from exc
