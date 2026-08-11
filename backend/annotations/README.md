# annotations — Label Studio

Component นี้เรียกดูข้อมูล annotation project/task จาก Label Studio (service `label-studio` ใน `compose.yml`) ต่อยอดจาก `labelstudio_test.py` เดิม

## โครงสร้างไฟล์

| ไฟล์ | หน้าที่ |
|---|---|
| `service.py` | จุดเดียวที่คุยกับ `label_studio_sdk` โดยตรง — client, ดึง project/task, error mapping |
| `schemas.py` | `ProjectOut`, `TaskOut` — เลือกเฉพาะ field ที่ API เราต้องการโชว์ (ไม่ mirror ทุก field ของ SDK ที่มีเป็นร้อย field) |
| `router.py` | รับ HTTP request แล้วเรียก `service.py` |

## ทำไม route เป็น `async def` (ต่างจาก db/ และ storage/)

`label_studio_sdk` มี client 2 แบบ: `LabelStudio` (sync, ใช้ `httpx.Client`) และ **`AsyncLabelStudio`** (async, ใช้ `httpx.AsyncClient`) — ต่างจาก `psycopg2`/`minio` ที่เป็น sync ล้วนไม่มีทางเลือก โดเมนนี้จึงใช้ `AsyncLabelStudio` แล้วประกาศ route เป็น `async def` ได้ตรงๆ โดยไม่บล็อก event loop ไม่ต้องพึ่ง threadpool เหมือนสองโดเมนก่อนหน้า

## Error mapping

`label_studio_sdk` โยน exception ที่สืบทอดจาก `ApiError` (เช่น `NotFoundError`, `BadRequestError`, `UnauthorizedError`) ซึ่งแต่ละตัวมี `status_code`/`body` ติดตัวมาอยู่แล้วจากฝั่ง Label Studio API ตรงๆ — ไม่ต้องเดา status code เองแบบ MinIO's `S3Error`:

```python
def _raise_from_api_error(exc: ApiError) -> HTTPException:
    status_code = exc.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
    return HTTPException(status_code=status_code, detail=str(exc.body))
```

## Config ที่ต้องตั้งเอง

ต้องใส่ `LABELSTUDIO_API_KEY` ใน `backend/.env` เอง (เป็น token เฉพาะ account ของแต่ละคน หา/copy ได้จากหน้า Account & Settings ใน Label Studio) — ไม่ใส่ default ไว้ใน `config.py` เพราะเป็นข้อมูลที่ไม่ควร hardcode ในซอร์สโค้ด

## Endpoints

| Method | Path | คำอธิบาย |
|---|---|---|
| GET | `/annotations/projects` | ดึงรายชื่อ project ทั้งหมด |
| GET | `/annotations/projects/{project_id}/tasks` | ดึงรายการ task ใน project นั้น (404 ถ้า project ไม่พบ) |
