from datetime import datetime
from typing import Optional

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings
from arq.constants import default_queue_name
from arq.jobs import Job, JobStatus
from fastapi import HTTPException, Request, status

from core.config import settings


def get_redis_settings() -> RedisSettings:
    return RedisSettings(host=settings.redis_host, port=settings.redis_port, database=0)


async def create_arq_pool() -> ArqRedis:
    return await create_pool(get_redis_settings())


def get_arq_pool(request: Request) -> ArqRedis:
    return request.app.state.arq_pool


async def enqueue_job(
    pool: ArqRedis,
    function: str,
    job_data: dict,
    start_at: Optional[datetime] = None,
    queue_name: Optional[str] = None,
) -> str:
    job = await pool.enqueue_job(
        function,
        job_data,
        _defer_until=start_at,
        _queue_name=queue_name,
    )
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job with this id already exists (duplicate job)",
        )
    return job.job_id


async def get_job_status(pool: ArqRedis, job_id: str, queue_name: Optional[str] = None) -> dict:
    job = Job(job_id, pool, _queue_name=queue_name or default_queue_name)
    job_status = await job.status()
    if job_status == JobStatus.not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    result_info = await job.result_info()
    return {
        "job_id": job_id,
        "status": job_status.value,
        "result": result_info.result if result_info else None,
    }
