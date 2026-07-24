from pathlib import Path

from client import ensure_bucket, get_client
from core.config import settings


# แก้ชื่อไฟล์ตรงนี้ให้เป็นรูปของตัวเอง ที่วางไว้ใน assets/
ASSET_PATH = Path(__file__).parent.parent.parent / "assets" / "my_photo.jpg"
OBJECT_NAME = "sandbox/my_photo.jpg"
DOWNLOAD_PATH = Path(__file__).parent / "downloaded_my_photo.jpg"


def upload(client):
    """fput_object: อ่านไฟล์จาก disk แล้วอัปโหลดขึ้น bucket/object_name ที่กำหนด"""
    client.fput_object(
        settings.minio_bucket,
        OBJECT_NAME,
        str(ASSET_PATH),
    )
    print(f"Uploaded {ASSET_PATH.name} -> {settings.minio_bucket}/{OBJECT_NAME}")


def download(client):
    """fget_object: ดึง object จาก bucket แล้วเขียนลง disk ตาม path ที่กำหนด"""
    client.fget_object(
        settings.minio_bucket,
        OBJECT_NAME,
        str(DOWNLOAD_PATH),
    )
    print(f"Downloaded {settings.minio_bucket}/{OBJECT_NAME} -> {DOWNLOAD_PATH}")


def show_object_info(client):
    """stat_object: ดู metadata ของ object โดยไม่ต้องโหลดไฟล์ทั้งหมด"""
    stat = client.stat_object(settings.minio_bucket, OBJECT_NAME)
    print(f"size={stat.size} bytes, last_modified={stat.last_modified}, etag={stat.etag}")


if __name__ == "__main__":
    client = get_client()
    ensure_bucket(client, settings.minio_bucket)

    upload(client)
    show_object_info(client)
    download(client)
