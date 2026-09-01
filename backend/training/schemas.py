from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DatasetImportResponse(BaseModel):
    dataset: str
    minio_uri: str
    splits: dict[str, int]


class TrainQueueRequest(BaseModel):
    epochs: int = Field(default=1, ge=1, le=10, examples=[1])
    start_at: Optional[datetime] = Field(
        default=None,
        description="เวลาที่ต้องการให้เริ่มเทรน (UTC) ไม่ระบุ = เริ่มทันทีที่ Trainer Worker ว่าง",
        examples=["2026-09-01T10:00:00Z"],
    )


class TrainQueueResponse(BaseModel):
    job_id: str
    queue_name: str
