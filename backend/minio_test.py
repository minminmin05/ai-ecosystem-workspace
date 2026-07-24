from pathlib import Path

from minio import Minio

from core.config import settings


PHOTO_PATH = Path(__file__).parent.parent / "assets" / "my_photo.jpg"
OBJECT_NAME = "photos/my_photo.jpg"


client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)


def create_bucket():
    if client.bucket_exists(settings.minio_bucket):
        print(f"Bucket already exists: {settings.minio_bucket}")
        return

    client.make_bucket(settings.minio_bucket)
    print(f"Create bucket success: {settings.minio_bucket}")


def upload_photo():
    client.fput_object(
        settings.minio_bucket,
        OBJECT_NAME,
        str(PHOTO_PATH),
    )
    print(f"Upload photo success: {OBJECT_NAME}")


def list_objects():
    print("\n=== Objects in bucket ===")
    for obj in client.list_objects(settings.minio_bucket, recursive=True):
        print(f"{obj.object_name} ({obj.size} bytes)")


if __name__ == "__main__":
    create_bucket()
    upload_photo()
    list_objects()
