from typing import Any, Optional

from pydantic import BaseModel, Field


class JobEnqueueRequest(BaseModel):
    function: str = Field(examples=["simple_work"])
    job_data: dict[str, Any] = Field(default_factory=dict, examples=[{"name": "Oat", "task": "Test ARQ Worker"}])


class JobEnqueueResponse(BaseModel):
    job_id: str


class JobStatusOut(BaseModel):
    job_id: str
    status: str
    result: Optional[Any] = None
