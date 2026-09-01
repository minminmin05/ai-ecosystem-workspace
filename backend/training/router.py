from arq import ArqRedis
from fastapi import APIRouter, Depends, status

import jobs.service as jobs_service

from . import service
from .schemas import DatasetImportResponse, TrainQueueRequest, TrainQueueResponse


router = APIRouter(prefix="/training", tags=["training"])


@router.post(
    "/datasets/import",
    summary="ดึง dataset จาก Hugging Face มาเก็บใน MinIO",
)
def import_dataset() -> DatasetImportResponse:
    return service.import_dataset_to_minio()


@router.post(
    "/queue",
    status_code=status.HTTP_202_ACCEPTED,
    summary="เข้าคิวสั่งเทรนโมเดล (token classification)",
    responses={409: {"description": "Duplicate job id"}},
)
async def queue_training(
    data: TrainQueueRequest,
    pool: ArqRedis = Depends(jobs_service.get_arq_pool),
) -> TrainQueueResponse:
    job_id = await service.queue_training(pool, data.epochs, data.start_at)
    return TrainQueueResponse(job_id=job_id, queue_name=service.TRAINING_QUEUE_NAME)
