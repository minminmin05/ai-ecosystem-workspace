from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    text: str = Field(examples=["Apple is looking at buying U.K. startup for $1 billion"])


class PredictResponse(BaseModel):
    job_id: str
    queue_name: str
