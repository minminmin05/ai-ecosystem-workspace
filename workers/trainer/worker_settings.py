from arq.connections import RedisSettings

from config import settings
from train import train_token_classification


class WorkerSettings:
    functions = [train_token_classification]
    queue_name = "training_queue"
    redis_settings = RedisSettings(host=settings.redis_host, port=settings.redis_port, database=0)
    # เทรนทีละงานเท่านั้น กัน GPU (4GB VRAM) ชนกันถ้ามีหลายงานพร้อมกัน
    max_jobs = 1
    # เทรนโมเดลใช้เวลานานกว่า job ทั่วไปมาก กัน ARQ retry ทั้งที่ยังเทรนไม่เสร็จ
    job_timeout = 3600
