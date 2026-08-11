from arq import ArqRedis
from fastapi import APIRouter, Depends, status

from . import service
from .schemas import JobEnqueueRequest, JobEnqueueResponse, JobStatusOut


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue a background job",
    responses={409: {"description": "Duplicate job id"}},
)
async def enqueue_job(
    data: JobEnqueueRequest,
    pool: ArqRedis = Depends(service.get_arq_pool),
) -> JobEnqueueResponse:
    job_id = await service.enqueue_job(pool, data.function, data.job_data)
    return JobEnqueueResponse(job_id=job_id)


@router.get(
    "/{job_id}",
    summary="Check the status/result of a background job",
    responses={404: {"description": "Job not found"}},
)
async def get_job_status(
    job_id: str,
    pool: ArqRedis = Depends(service.get_arq_pool),
) -> JobStatusOut:
    return await service.get_job_status(pool, job_id)
