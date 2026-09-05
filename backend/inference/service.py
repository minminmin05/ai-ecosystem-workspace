from arq import ArqRedis

from jobs.service import enqueue_job as jobs_enqueue_job


INFERENCE_QUEUE_NAME = "inference_queue"
PREDICT_FUNCTION_NAME = "predict_token_classification"


async def queue_prediction(pool: ArqRedis, text: str) -> str:
    return await jobs_enqueue_job(
        pool,
        PREDICT_FUNCTION_NAME,
        {"text": text},
        queue_name=INFERENCE_QUEUE_NAME,
    )
