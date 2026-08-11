# AI Ecosystem Workspace

Workspace สำหรับสร้างและเรียนรู้ระบบ "AI Ecosystem" แบบ end-to-end ทีละส่วน โดยแต่ละ assignment จะต่อยอด component ใหม่เข้าไปในระบบเดิมเรื่อยๆ (database → queue/worker → annotation platform → object storage → logging → ...) เป้าหมายปลายทางคือระบบหลังบ้านสำหรับรับข้อมูล ให้คน label ข้อมูล เทรนโมเดล และให้บริการ inference

## ระบบทำอะไรได้บ้าง (ปัจจุบัน)

- **FastAPI backend** (`backend/main.py`) เป็น entrypoint หลักของระบบจริงแล้ว เปิด REST API + Swagger UI (`/docs`) และ ReDoc (`/redoc`) ให้เรียกใช้ 4 component ด้านล่างผ่าน HTTP
- **เก็บข้อมูลเชิงโครงสร้าง** ด้วย PostgreSQL ผ่าน SQLAlchemy (CRUD ผ่าน REST API แล้ว ดู `backend/db/README.md`)
- **เก็บข้อมูล unstructured** (รูปภาพ, ไฟล์) ด้วย MinIO รองรับ upload/download/delete แบบ stream ผ่าน REST API (ดู `backend/storage/README.md`)
- **Label/Annotate ข้อมูล** ผ่าน Label Studio พร้อม SDK สำหรับดึง project/task ผ่าน REST API (ดู `backend/annotations/README.md`)
- **คิวงานเบื้องหลัง (background job queue)** ด้วย Redis + ARQ worker ยิงงานผ่าน REST API แล้วเช็คสถานะทีหลัง (ดู `backend/jobs/README.md`)
- **Custom logging** รองรับหลายระดับ (DEBUG–CRITICAL) พร้อม log rotation ทั้งฝั่ง Python และฝั่ง Docker container
- **API snapshot** — `backend/export_openapi.py` แปลง OpenAPI schema ของระบบเป็น `openapi_snapshot.xlsx`/`.csv`

> ส่วนที่ยังไม่มีโค้ดจริง: **training worker / model จริง** — ปัจจุบันมีแค่ตัวอย่าง job worker พื้นฐานผ่าน ARQ (`backend/worker_settings.py`) ยังไม่มี logic เทรนโมเดลจริง

## สถาปัตยกรรม

ออกแบบไว้ใน `diagrams/overview_v2.drawio` (เวอร์ชันล่าสุด, `overview.drawio` เป็นแผนผังตั้งต้นก่อนเริ่ม implement backend):

- ผู้ใช้ทั่วไป (End user) เข้าระบบผ่าน **Inference Channel** และแอดมิน (Admin) เข้าผ่าน **Management Channel** โดยทั้งคู่วิ่งเข้า **FastAPI** เป็นประตูหลัก
- FastAPI เขียน/อ่านข้อมูลเชิงโครงสร้างผ่าน **SQLAlchemy → PostgreSQL** และส่งงานเบื้องหลังผ่าน **ARQ → Redis**
- **Job worker** ดึงงานจาก Redis ไปประมวลผล เชื่อมกับโมเดล/AI logic และ **PostgreSQL**
- **Training worker** ดึงงานเทรนโมเดลจาก Redis เช่นกัน เชื่อมกับโมเดลและอ่าน/เขียนข้อมูล (เช่น dataset, checkpoint) ที่ **MinIO**
- **Label Studio** ใช้เป็นแพลตฟอร์ม annotation ข้อมูล เชื่อมต่อกับ PostgreSQL เป็น database ของตัวเอง
- ทุก service รันอยู่บน **Docker** (docker compose)

## องค์ประกอบปัจจุบันของระบบ

### Docker services (`compose.yml`)

| Service | Image | Port | หน้าที่ |
|---|---|---|---|
| `postgres` | postgres:17 | 5432 | ฐานข้อมูลหลัก (`ai_ecosystem`) |
| `redis` | redis:8.8.0-alpine | 6379 | Message broker/queue ให้ ARQ |
| `label-studio` | heartexlabs/label-studio | 8080 | แพลตฟอร์ม annotation ข้อมูล |
| `minio` | minio/minio | 9000 (API) / 9001 (Console) | Object storage สำหรับข้อมูล unstructured |

ทุก service ตั้งค่า logging driver แบบ `json-file` พร้อม rotation (`max-size: 10m`, `max-file: 3`) ผ่าน YAML anchor `x-logging` ร่วมกัน

### Backend (`backend/`)

โครงสร้างแบบ **domain-based**: แยกโค้ดตาม component (`db/`, `storage/`, `annotations/`, `jobs/`) แต่ละตัวมี `router.py` + `service.py` + `schemas.py` + `README.md` ของตัวเอง แทนที่จะแยกตาม layer — เหตุผลและรายละเอียดเต็มอยู่ที่ [`backend/README.md`](backend/README.md)

| ไฟล์/โฟลเดอร์ | หน้าที่ | เอกสารเพิ่มเติม |
|---|---|---|
| `main.py` | FastAPI app จริง — entrypoint หลัก, ตั้ง metadata/lifespan, รวม router ทั้ง 4 domain | [`backend/README.md`](backend/README.md) |
| `core/` | Settings กลาง + custom logger ที่ทุก domain เรียกใช้ร่วมกัน | [`backend/core/README.md`](backend/core/README.md) |
| `db/` | REST API จัดการข้อมูลนักศึกษาใน PostgreSQL ผ่าน SQLAlchemy | [`backend/db/README.md`](backend/db/README.md) |
| `storage/` | REST API upload/download/delete ไฟล์ใน MinIO | [`backend/storage/README.md`](backend/storage/README.md) |
| `annotations/` | REST API ดึง project/task จาก Label Studio | [`backend/annotations/README.md`](backend/annotations/README.md) |
| `jobs/` | REST API ยิงงานเข้าคิว ARQ/Redis แล้วเช็คสถานะ | [`backend/jobs/README.md`](backend/jobs/README.md) |
| `worker_settings.py` | ARQ worker — รันแยก process จาก API server เพื่อประมวลผลงานที่ `jobs/` ยิงเข้าคิว | — |
| `export_openapi.py` | Snapshot API list: ดึง OpenAPI schema จาก `app.openapi()` แปลงเป็น `openapi_snapshot.xlsx`/`.csv` | ดูหัวข้อ "Snapshot API list" ใน [`backend/README.md`](backend/README.md) |
| `postgres_test.py`, `minio_test.py`, `labelstudio_test.py`, `logger_test.py`, `enqueue.py` | สคริปต์ทดสอบเดี่ยวจาก assignment ก่อนหน้า ยังเก็บไว้อ้างอิง ไม่ได้ลบ (logic จริงย้ายเข้า `service.py` ของแต่ละ domain แล้ว) | — |

Dependency หลัก (`pyproject.toml`): `fastapi`, `uvicorn`, `arq`, `label-studio-sdk`, `minio`, `psycopg2-binary`, `pydantic` / `pydantic-settings`, `redis`, `sqlalchemy`, `pandas` / `openpyxl` (สำหรับ `export_openapi.py`) — จัดการด้วย [uv](https://docs.astral.sh/uv/)

### Sandbox / สคริปต์ทดลอง

- `sandbox/test_settings.py` — ทดสอบโหลด settings จากนอก backend
- `sandbox/minio/` — สคริปต์ทดสอบ MinIO แยกจาก backend: `client.py` (shared client), `upload_download.py` (upload/download), `versioning.py` (เปิด versioning + ดึงข้อมูลแยกเวอร์ชัน)

### อื่นๆ

- `assets/` — รูปภาพประกอบ diagram, screenshot ของแต่ละ assignment, และรูปส่วนตัวที่ใช้ทดสอบอัปโหลดขึ้น MinIO
- `diagrams/overview.drawio` — แผนผังสถาปัตยกรรมตั้งต้น (ก่อนเริ่ม implement backend), `overview_v2.drawio` — เวอร์ชันล่าสุด (เปิดด้วย [draw.io](https://app.diagrams.net/))
- `docs/` — รายงานประกอบแต่ละ assignment (ไฟล์ `.docx`, ไม่ commit ขึ้น git)
- `dev/test_label.json` — ข้อมูลตัวอย่างสำหรับทดสอบ Label Studio
- `frontends/`, `workers/` — โฟลเดอร์เตรียมไว้สำหรับพัฒนาในอนาคต ปัจจุบันยังว่างเปล่า
- `storage/` (ระดับบนสุด, root) — โฟลเดอร์ placeholder ว่างเปล่า **คนละตัวกับ** `backend/storage/` ที่เป็น domain module ของ MinIO ที่มีโค้ดจริงแล้ว (ดู [`backend/storage/README.md`](backend/storage/README.md)) — ตั้งชื่อชนกันโดยไม่ได้ตั้งใจ ระวังอย่าสับสนตอนอ่านโครงสร้าง repo

## เริ่มใช้งาน

```bash
# เปิด service ทั้งหมด (postgres, redis, label-studio, minio)
docker compose up -d

# ติดตั้ง dependency ฝั่ง backend
cd backend
uv sync

# รัน API server จริง (Swagger UI ที่ http://127.0.0.1:8000/docs, ReDoc ที่ /redoc)
uv run python main.py

# รัน worker แยกอีก process ถ้าต้องการให้ job ที่ยิงผ่าน /jobs ถูกประมวลผลจริง
uv run arq worker_settings.WorkerSettings

# Snapshot API list เป็น Excel/CSV
uv run python export_openapi.py
```

รายละเอียดแต่ละ endpoint, error mapping, และเหตุผลเบื้องหลังการออกแบบ อยู่ใน [`backend/README.md`](backend/README.md) และ README ย่อยของแต่ละ domain (`backend/db/`, `backend/storage/`, `backend/annotations/`, `backend/jobs/`, `backend/core/`)

สคริปต์ทดสอบเดี่ยวจาก assignment ก่อนหน้า (`postgres_test.py`, `minio_test.py`, `logger_test.py` ฯลฯ) ยังรันได้ตามปกติถ้าต้องการอ้างอิง:
```bash
uv run python postgres_test.py
uv run python minio_test.py
uv run python logger_test.py
```
