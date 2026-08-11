from typing import Any, Optional

from pydantic import BaseModel


class ProjectOut(BaseModel):
    id: int
    title: Optional[str] = None
    description: Optional[str] = None
    task_number: Optional[int] = None


class TaskOut(BaseModel):
    id: int
    project: Optional[int] = None
    data: dict[str, Any]
