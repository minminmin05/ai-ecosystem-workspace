# Backend — AI Ecosystem API

Backend ของโปรเจค AI Ecosystem สร้างด้วย FastAPI เปิด REST API ให้เรียกใช้งาน component หลักของระบบ 4 ตัว ได้แก่ PostgreSQL, MinIO, Label Studio, และ ARQ/Redis job queue

## แนวคิดโครงสร้างโปรเจกต์ที่เลือกใช้: Domain-based (ไม่ใช่ Layer-based)

โครงสร้างที่เลือกคือแยกโค้ดตาม **domain/component** (`db/`, `storage/`, `annotations/`, `jobs/`) โดยแต่ละ domain มี `router.py` + `service.py` + `schemas.py` + `README.md` อยู่ในโฟลเดอร์ตัวเอง — แทนที่จะแยกตาม **layer** (เช่น รวม router ทุกตัวไว้ที่ `api/routers/`, รวม service ทุกตัวไว้ที่ `services/`)

**เหตุผลที่เลือกแบบนี้:**
- Component ทั้ง 4 ตัวของระบบนี้แทบไม่ผูกกันเลย (postgres/minio/label-studio/redis) แต่ละตัวมี library, error type, และ sync/async model ของตัวเอง การแก้ 1 feature ไม่ควรต้องกระโดดข้าม 3 โฟลเดอร์ตลอด
- แนวทางนี้อ้างอิงจาก FastAPI official guide ["Bigger Applications - Multiple Files"](https://fastapi.tiangolo.com/tutorial/bigger-applications/) ที่แนะนำว่าแอปขนาดใหญ่ควรแยกเป็น module/domain โดยแต่ละ module มี router/schema/service ของตัวเอง
- ได้ผลพลอยได้คือแก้โจทย์ข้อ 4 (README ต่อ component หลัก) ไปในตัว เพราะ 1 โฟลเดอร์ = 1 component พอดี ไม่ต้องแยกคิดว่า README ควรอยู่ตรงไหน

**หลักการแบ่งงานภายในแต่ละ domain (ทุกตัวเหมือนกัน):**

| ไฟล์ | หน้าที่ |
|---|---|
| `router.py` | รับ HTTP request, validate ผ่าน schema, เรียก `service.py` — **ไม่คุยกับ library ภายนอกตรงๆ** |
| `service.py` | จุดเดียวที่คุยกับ library ภายนอก (SQLAlchemy / minio SDK / label_studio_sdk / ARQ) รวมถึง error mapping |
| `schemas.py` | Pydantic model คุม input/output ของ API |

## โครงสร้างไดเรกทอรี

```
backend/
├── main.py                 # FastAPI() + lifespan + include_router x4
├── export_openapi.py       # snapshot API list -> Excel/CSV
├── core/
│   ├── config.py           # Settings กลาง อ่านจาก .env
│   └── logger.py           # custom logger (จาก assignment ก่อนหน้า)
├── db/                     # PostgreSQL / SQLAlchemy — ดู db/README.md
├── storage/                 # MinIO — ดู storage/README.md
├── annotations/             # Label Studio — ดู annotations/README.md
├── jobs/                    # ARQ / Redis — ดู jobs/README.md
├── worker_settings.py       # ARQ worker (แยกรันคนละ process จาก API)
└── *_test.py                # สคริปต์ทดสอบเดี่ยวจาก assignment ก่อนหน้า (ของเดิม ยังเก็บไว้อ้างอิง ไม่ได้ลบ)
```

`postgres_test.py`, `minio_test.py`, `labelstudio_test.py`, `logger_test.py`, `enqueue.py` เป็นสคริปต์ทดสอบเดี่ยวจาก assignment ก่อนหน้าที่ยังไม่ได้ลบ — ตอนนี้ logic การเชื่อมต่อ library เดียวกันถูกย้ายไปอยู่ใน `service.py` ของแต่ละ domain แทนแล้ว (เข้าถึงผ่าน REST API ได้จริง ไม่ใช่แค่รันสคริปต์ทดสอบ)

## Sync กับ Async ต่างกันไปตาม domain ไหน

ไม่ได้ประกาศทุก route เป็น `async def` เหมือนกันหมด แต่เลือกตาม library ที่แต่ละ domain ใช้จริง:

| Domain | Route | เหตุผล |
|---|---|---|
| `db/` | sync `def` | `psycopg2` เป็น driver sync/blocking ล้วน ไม่มี native async |
| `storage/` | sync `def` | `minio` SDK เป็น sync/blocking ล้วน (เช็คซอร์สแล้วไม่มี asyncio เลย) |
| `annotations/` | `async def` | `label_studio_sdk` มี `AsyncLabelStudio` (httpx.AsyncClient) ให้ใช้ตรงๆ |
| `jobs/` | `async def` | ARQ เป็น async-native อยู่แล้วทั้งหมด |

Route ที่เป็น sync `def` ไม่ได้บล็อก event loop เพราะ FastAPI รัน sync path operation ในเธรดพูลให้อัตโนมัติ — ไม่ต้องเขียน `run_in_threadpool` เอง

## Error mapping

ทุก domain มี pattern เดียวกัน: `service.py` ดัก exception เฉพาะของ library นั้นๆ แล้วแปลงเป็น `HTTPException` ให้ `router.py` แค่ปล่อยผ่าน รายละเอียดของแต่ละ domain ดูใน README ย่อยของแต่ละโฟลเดอร์ สรุปภาพรวม:

| Domain | Exception ต้นทาง | วิธี map เป็น HTTP status |
|---|---|---|
| `db/` | `IntegrityError` / `SQLAlchemyError` / not found | 409 / 500 / 404 |
| `storage/` | `minio.error.S3Error` | อ่านจาก `exc.response.status` |
| `annotations/` | `label_studio_sdk` `ApiError` (และ subclass) | อ่านจาก `exc.status_code` ที่ SDK ให้มาตรงๆ |
| `jobs/` | job not found | 404 |

## FastAPI metadata & Swagger documentation

`main.py` ตั้งค่า `title`, `description`, `version`, `contact`, `license_info`, `openapi_tags` ตาม [FastAPI metadata tutorial](https://fastapi.tiangolo.com/tutorial/metadata/) ทุก route มี `tags=[...]` ที่ระดับ `APIRouter` (จำเป็นต้องใส่จริง ไม่ใช่แค่ประกาศ `openapi_tags` ที่ตัวแอปเฉยๆ — ไม่งั้นจะไม่ถูกจัดกลุ่มใน Swagger) และ `summary=`/`responses={}` ต่อ endpoint เพื่อให้ error response (404/409/...) มีคำอธิบายใน Swagger ด้วย ไม่ใช่โชว์แค่ 200

Response schema ส่วนใหญ่มาจาก **return type annotation** ของฟังก์ชัน (เช่น `-> StudentOut`) ที่ FastAPI ใช้เป็น `response_model` ให้อัตโนมัติ ยกเว้น endpoint ดาวน์โหลดไฟล์ (`storage/router.py`) ที่ต้องปิด response_model inference เอง (`response_model=None` + `response_class=StreamingResponse`) เพราะ return type เป็น `Response` ไม่ใช่ Pydantic model

หน้า documentation ดูได้ที่ `/docs` (Swagger UI) และ `/redoc` (ReDoc) โดย FastAPI generate ให้อัตโนมัติจาก schema/metadata ข้างต้น

## Snapshot API list เป็น Excel/CSV

`export_openapi.py` ดึง OpenAPI schema จาก `app.openapi()` โดยตรง (ไม่ต้องมี server รันอยู่) แล้วแปลงเป็นตาราง 1 แถวต่อ 1 endpoint บันทึกเป็น `openapi_snapshot.xlsx`/`.csv`

จุดที่ต้องระวังตอนเขียน script แบบนี้ (ที่ script แบบ naive มักพลาด):
- Request/response ส่วนใหญ่อ้างอิงผ่าน `"$ref": "#/components/schemas/XXX"` ไม่ใช่ schema แบบ inline — ต้อง resolve ชื่อ schema ออกมาเอง
- Endpoint upload ไฟล์ (`storage/`) ใช้ `multipart/form-data` ไม่ใช่ `application/json` — ต้อง loop content-type แบบ generic ไม่ hardcode

รัน:
```bash
uv run python export_openapi.py
```

## การตั้งค่า (`.env`)

ทุก setting อ่านจาก `backend/.env` ผ่าน `core/config.py` (pydantic-settings) ไม่มีค่า sensitive ใดๆ hardcode อยู่ในซอร์สโค้ด ยกเว้นค่า default สำหรับ local dev (เช่น MinIO/Postgres ที่รันบนเครื่องตัวเองผ่าน `docker compose`) — ส่วน `LABELSTUDIO_API_KEY` ไม่มี default เพราะเป็น token เฉพาะ account ต้องใส่เอง

## วิธีรัน

```bash
docker compose up -d        # postgres, redis, label-studio, minio
cd backend
uv sync
uv run python main.py       # API server ที่ http://127.0.0.1:8000/docs
```

รัน worker แยกอีก process ถ้าต้องการให้ job ใน `jobs/` ถูกประมวลผลจริง:
```bash
uv run arq worker_settings.WorkerSettings
```
