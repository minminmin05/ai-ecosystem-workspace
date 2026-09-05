from arq import ArqRedis
from fastapi import APIRouter, Depends, status

import jobs.service as jobs_service

from . import service
from .schemas import PredictRequest, PredictResponse


router = APIRouter(prefix="/inference", tags=["inference"])


@router.post(
    "/predict",
    status_code=status.HTTP_202_ACCEPTED,
    summary="เข้าคิวสั่งทำนาย (token classification)",
    responses={409: {"description": "Duplicate job id"}},
)
async def predict(
    data: PredictRequest,
    pool: ArqRedis = Depends(jobs_service.get_arq_pool),
) -> PredictResponse:
    job_id = await service.queue_prediction(pool, data.text)
    return PredictResponse(job_id=job_id, queue_name=service.INFERENCE_QUEUE_NAME)
