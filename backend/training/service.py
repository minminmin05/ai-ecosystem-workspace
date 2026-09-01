from datetime import datetime
from typing import Optional

from arq import ArqRedis
from datasets import load_dataset

from core.config import settings
from jobs.service import enqueue_job as jobs_enqueue_job


# "conll2003" ตัวจริงบน HF Hub ยังใช้ loading script แบบเก่าที่ datasets library เวอร์ชันปัจจุบัน
# เลิกรองรับแล้ว ("Dataset scripts are no longer supported") ใช้ mirror ที่แปลงเป็น Parquet
# แล้วแทน (คนละ repo แต่ schema/จำนวนแถวตรงกับตัวต้นฉบับทุกประการ)
DATASET_NAME = "lhoestq/conll2003"
DATASET_MINIO_PREFIX = "datasets/conll2003"
TRAINING_QUEUE_NAME = "training_queue"
TRAIN_FUNCTION_NAME = "train_token_classification"


def _s3_storage_options() -> dict:
    protocol = "https" if settings.minio_secure else "http"
    return {
        "key": settings.minio_access_key,
        "secret": settings.minio_secret_key,
        "client_kwargs": {"endpoint_url": f"{protocol}://{settings.minio_endpoint}"},
    }


def import_dataset_to_minio() -> dict:
    """ดึง dataset จาก Hugging Face Hub แล้วเขียนตรงเข้า MinIO ผ่าน s3fs
    (S3-compatible filesystem interface ของ `datasets`) ไม่ต้อง save ลง disk แล้ว upload เอง"""
    dataset = load_dataset(DATASET_NAME)
    uri = f"s3://{settings.minio_bucket}/{DATASET_MINIO_PREFIX}"
    dataset.save_to_disk(uri, storage_options=_s3_storage_options())
    return {
        "dataset": DATASET_NAME,
        "minio_uri": uri,
        "splits": {split: len(dataset[split]) for split in dataset},
    }


async def queue_training(pool: ArqRedis, epochs: int, start_at: Optional[datetime]) -> str:
    return await jobs_enqueue_job(
        pool,
        TRAIN_FUNCTION_NAME,
        {"epochs": epochs},
        start_at=start_at,
        queue_name=TRAINING_QUEUE_NAME,
    )
