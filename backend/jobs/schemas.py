from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class JobEnqueueRequest(BaseModel):
    function: str = Field(examples=["simple_work"])
    job_data: dict[str, Any] = Field(default_factory=dict, examples=[{"name": "Oat", "task": "Test ARQ Worker"}])
    start_at: Optional[datetime] = Field(
        default=None,
        description="เวลาที่ต้องการให้งานเริ่มทำงาน (UTC) ไม่ระบุ = เริ่มทันทีที่ worker ว่าง",
        examples=["2026-08-13T10:00:00Z"],
    )
    queue_name: Optional[str] = Field(
        default=None,
        description="ชื่อคิวที่ต้องการยิงงานเข้า ไม่ระบุ = ใช้คิวมาตรฐานของ ARQ",
        examples=["training_queue"],
    )


class JobEnqueueResponse(BaseModel):
    job_id: str


class JobStatusOut(BaseModel):
    job_id: str
    status: str
    result: Optional[Any] = None
