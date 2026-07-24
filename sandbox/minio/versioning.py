from pathlib import Path

from minio.versioningconfig import ENABLED, VersioningConfig

from client import ensure_bucket, get_client
from core.config import settings


BUCKET = settings.minio_bucket
OBJECT_NAME = "sandbox/my_photo.jpg"

ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
# วางรูปสองรูปของตัวเองไว้ที่ assets/ ก่อนรัน (คนละรูปกัน เพื่อให้เห็นความต่างระหว่าง version)
PHOTO_V1 = ASSETS_DIR / "my_photo.jpg"
PHOTO_V2 = ASSETS_DIR / "my_photo_v2.jpeg"


def enable_versioning(client):
    client.set_bucket_versioning(BUCKET, VersioningConfig(ENABLED))
    print(f"Enabled versioning on bucket: {BUCKET}")


def upload_two_versions(client):
    client.fput_object(BUCKET, OBJECT_NAME, str(PHOTO_V1))
    print(f"Uploaded version 1 from {PHOTO_V1.name}")

    client.fput_object(BUCKET, OBJECT_NAME, str(PHOTO_V2))
    print(f"Uploaded version 2 from {PHOTO_V2.name}")


def list_versions(client):
    print("\n=== Object versions ===")
    versions = list(client.list_objects(BUCKET, prefix=OBJECT_NAME, include_version=True))
    for v in versions:
        print(f"version_id={v.version_id}  is_latest={v.is_latest}  size={v.size} bytes")
    return versions


def get_without_version(client):
    """ไม่ระบุ version_id -> MinIO จะคืนค่า object เวอร์ชันล่าสุด (is_latest=True) เสมอ"""
    resp = client.get_object(BUCKET, OBJECT_NAME)
    data = resp.read()
    resp.close()
    resp.release_conn()
    print(f"\n[No version specified] got {len(data)} bytes (this is the latest version)")


def get_with_version(client, version_id: str):
    """ระบุ version_id -> MinIO จะคืนค่า object เวอร์ชันนั้นเจาะจง แม้จะไม่ใช่เวอร์ชันล่าสุดแล้วก็ตาม"""
    resp = client.get_object(BUCKET, OBJECT_NAME, version_id=version_id)
    data = resp.read()
    resp.close()
    resp.release_conn()
    print(f"[version_id={version_id}] got {len(data)} bytes")


if __name__ == "__main__":
    client = get_client()
    ensure_bucket(client, BUCKET)

    enable_versioning(client)
    upload_two_versions(client)

    versions = list_versions(client)

    get_without_version(client)

    oldest_version = next(v for v in versions if v.is_latest != "true")
    get_with_version(client, oldest_version.version_id)
