# jobs — ARQ / Redis background queue

Component นี้ยิงงานเบื้องหลัง (background job) เข้าคิวผ่าน ARQ + Redis (service `redis` ใน `compose.yml`) ต่อยอดจาก `enqueue.py` + `worker_settings.py` เดิม

## ทำไม `jobs` ไม่ใช่ CRUD resource เหมือน 3 domain ก่อนหน้า

`db/`, `storage/`, `annotations/` ทั้งหมดเป็น resource ที่มี state ให้ create/read/update/delete ได้ตรงไปตรงมา แต่ **job ไม่ใช่ resource แบบนั้น** — เป็น "สั่งงานแล้วรอผล" (fire-and-poll): ยิงงานเข้าคิวครั้งเดียว (`POST /jobs`) แล้วมาเช็คสถานะ/ผลลัพธ์ทีหลัง (`GET /jobs/{id}`) ไม่มี update/delete เพราะงานที่เข้าคิวไปแล้วแก้ไม่ได้ ต้องยิงใหม่แทน

## ARQ pool lifecycle — สร้างครั้งเดียว ไม่ใช่ทุก request

`enqueue.py` เดิมเรียก `create_pool()` ทุกครั้งที่รันสคริปต์ ซึ่งใช้ได้เพราะรันครั้งเดียวจบ แต่ endpoint ใน API ถูกเรียกซ้ำได้ทุก request — ถ้าเปิด pool ใหม่ทุก request จะเปิด connection ไปที่ Redis เพิ่มเรื่อยๆ ช้าลงและอาจชน connection limit

แก้โดยสร้าง pool **ครั้งเดียวตอน app startup** ผ่าน `lifespan` ใน `main.py` แล้วเก็บไว้ที่ `app.state.arq_pool`, ปิดตอน shutdown:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    ...
    app.state.arq_pool = await create_arq_pool()
    try:
        yield
    finally:
        await app.state.arq_pool.aclose()
```

แล้ว `service.get_arq_pool(request)` แค่ดึง pool ที่มีอยู่แล้วออกมาจาก `request.app.state.arq_pool` ให้ route ใช้ผ่าน `Depends()` — ไม่มี route ไหนเรียก `create_pool()` เองเลย

## ทำไม route เป็น `async def`

ARQ เป็น async-native อยู่แล้ว (`create_pool`, `enqueue_job`, `Job.status()` ล้วนเป็น coroutine) จึงประกาศ route เป็น `async def` แล้ว `await` ตรงๆ ได้เลย ไม่ต้องพึ่ง threadpool เหมือน `db/`/`storage/`

## Endpoints

| Method | Path | คำอธิบาย |
|---|---|---|
| POST | `/jobs` | ยิงงานเข้าคิว ระบุชื่อ function (ต้องตรงกับที่ลงทะเบียนไว้ใน `worker_settings.py`) + ข้อมูลงาน |
| GET | `/jobs/{job_id}` | เช็คสถานะ/ผลลัพธ์ของงาน (404 ถ้าไม่พบ job) |

**หมายเหตุ:** endpoint นี้แค่ "ส่งงานเข้าคิว" เท่านั้น งานจะไม่ถูกประมวลผลจริงจนกว่าจะมี worker รันอยู่แยกต่างหาก:

```bash
uv run arq worker_settings.WorkerSettings
```
