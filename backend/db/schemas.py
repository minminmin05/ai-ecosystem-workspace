from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StudentBase(BaseModel):
    name: str = Field(max_length=50, examples=["Oat"])
    age: int = Field(ge=0, le=150, examples=[22])
    major: str = Field(max_length=100, examples=["AI Engineering"])


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=50)
    age: Optional[int] = Field(default=None, ge=0, le=150)
    major: Optional[str] = Field(default=None, max_length=100)


class StudentOut(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
