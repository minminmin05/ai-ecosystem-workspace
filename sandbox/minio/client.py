import sys
from pathlib import Path

# เพิ่ม backend เข้า python path
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

from minio import Minio
from core.config import settings


def get_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket(client: Minio, bucket: str):
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f"Created bucket: {bucket}")
    else:
        print(f"Bucket already exists: {bucket}")
