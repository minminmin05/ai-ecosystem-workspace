from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import settings
from annotations.router import router as annotations_router
from db.router import router as db_router
from db.service import Base, engine
from inference.router import router as inference_router
from jobs.router import router as jobs_router
from jobs.service import create_arq_pool
from storage.router import router as storage_router
from storage.service import ensure_bucket
from training.router import router as training_router


tags_metadata = [
    {
        "name": "students",
        "description": "จัดการข้อมูลนักศึกษาใน PostgreSQL ผ่าน SQLAlchemy",
    },
    {
        "name": "storage",
        "description": "จัดการไฟล์/รูปภาพใน MinIO (upload, list, download, delete)",
    },
    {
        "name": "annotations",
        "description": "ดึงข้อมูล project/task ของ annotation จาก Label Studio",
    },
    {
        "name": "jobs",
        "description": "ยิงงานเบื้องหลังเข้าคิวผ่าน ARQ/Redis แล้วเช็คสถานะ/ผลลัพธ์ทีหลัง",
    },
    {
        "name": "training",
        "description": "ดึง dataset จาก Hugging Face เข้า MinIO และเข้าคิวสั่งเทรนโมเดล token classification",
    },
    {
        "name": "inference",
        "description": "เข้าคิวสั่งทำนายด้วยโมเดลที่เทรนไว้ (โหลดจาก MLflow Model Registry)",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_bucket()
    app.state.arq_pool = await create_arq_pool()
    try:
        yield
    finally:
        await app.state.arq_pool.aclose()


app = FastAPI(
    title="AI Ecosystem API",
    description=(
        "Backend API ของโปรเจค AI Ecosystem — endpoint สำหรับเรียกใช้งาน component "
        "ต่างๆ ในระบบ (PostgreSQL, MinIO, Label Studio, background job queue)"
    ),
    version="0.1.0",
    contact={
        # TODO: แก้เป็นชื่อ/อีเมลของคุณเอง
        "name": "Bunyamin Sensan",
        "email": "Dgkhamin@gmail.com",
    },
    license_info={"name": "MIT"},
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.include_router(db_router)
app.include_router(storage_router)
app.include_router(annotations_router)
app.include_router(jobs_router)
app.include_router(training_router)
app.include_router(inference_router)


@app.get("/health", tags=["health"], summary="Health check")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
