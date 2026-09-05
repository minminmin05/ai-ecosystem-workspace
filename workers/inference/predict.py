import asyncio

import mlflow

from config import settings
from logger import get_logger


logger = get_logger("inference_worker")

mlflow.set_tracking_uri(settings.mlflow_tracking_uri)

# โหลดโมเดลครั้งเดียวตอน worker เริ่มทำงาน (import-time) แล้วเก็บไว้ใน memory
# ไม่โหลดใหม่ทุก request — Inference Worker "รอรับคำสั่ง" ตามโจทย์ โดยมีโมเดลพร้อมใช้อยู่แล้ว
_MODEL_URI = f"models:/{settings.mlflow_model_name}/latest"
logger.info(f"กำลังโหลดโมเดลจาก MLflow: {_MODEL_URI}")
pipeline = mlflow.transformers.load_model(_MODEL_URI)
logger.info("โหลดโมเดลสำเร็จ พร้อมรับงาน")


def _predict_sync(text: str) -> list[dict]:
    entities = pipeline(text)
    # numpy float32 จาก pipeline ต้องแปลงเป็น python float ก่อน ไม่งั้น serialize
    # เป็น JSON ตอนตอบกลับผ่าน FastAPI ไม่ได้ (jsonable_encoder ไม่รู้จัก numpy type)
    return [
        {
            "word": e["word"],
            "entity_group": e.get("entity_group", e.get("entity")),
            "score": float(e["score"]),
            "start": e.get("start"),
            "end": e.get("end"),
        }
        for e in entities
    ]


async def predict_token_classification(ctx, job_data: dict) -> dict:
    """ARQ job function ต้องเป็น async def แต่การรัน pipeline ของ transformers เป็นงาน
    CPU-bound แบบ blocking เหมือนเหตุผลเดียวกับ Trainer Worker เลย offload ไป thread
    executor แทน ไม่บล็อก event loop ของ worker เอง"""
    text = job_data["text"]
    logger.info(f"ทำนาย text={text!r}")

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, _predict_sync, text)

    logger.info(f"ผลลัพธ์: {result}")
    return {"text": text, "entities": result}
