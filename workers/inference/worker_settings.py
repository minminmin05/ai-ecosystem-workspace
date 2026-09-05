from arq.connections import RedisSettings

from config import settings
from predict import predict_token_classification


class WorkerSettings:
    functions = [predict_token_classification]
    queue_name = "inference_queue"
    redis_settings = RedisSettings(host=settings.redis_host, port=settings.redis_port, database=0)
    # inference ต่อ request เร็วมาก (< 1 วินาที) รับหลายงานพร้อมกันได้ ไม่ต้องจำกัดเหมือน Trainer Worker
    job_timeout = 60
