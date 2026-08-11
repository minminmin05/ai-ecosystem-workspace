from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ObjectOut(BaseModel):
    object_name: str
    size: int
    etag: Optional[str] = None
    last_modified: Optional[datetime] = None
