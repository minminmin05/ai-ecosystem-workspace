# storage — MinIO

Component นี้จัดการข้อมูล unstructured (ไฟล์/รูปภาพ) เก็บอยู่บน MinIO (bucket `ai-ecosystem`) ต่อยอดจาก `minio_test.py` และ `sandbox/minio/` เดิม แต่ห่อเป็น REST API แทนสคริปต์เดี่ยวๆ

## โครงสร้างไฟล์

| ไฟล์ | หน้าที่ |
|---|---|
| `service.py` | จุดเดียวที่คุยกับ `minio` SDK โดยตรง — client, CRUD บน object, error mapping |
| `schemas.py` | `ObjectOut` — metadata ของไฟล์ที่ตอบกลับ (object_name, size, etag, last_modified) |
| `router.py` | รับ HTTP request/multipart upload แล้วเรียก `service.py` |

## ทำไม route เป็น sync `def`

`minio` (Python SDK) เป็น library sync/blocking ล้วน ไม่มี native async เลย (เช็คซอร์สแล้วไม่มี `asyncio`/`AsyncClient` ใดๆ) เหมือนกับเหตุผลใน `db/` — ประกาศ route เป็น sync `def` ให้ FastAPI รันในเธรดพูลให้เอง ไม่ต้องเขียน `run_in_threadpool` เอง

## Object name กับ path converter

Object key บน MinIO มี `/` อยู่ในชื่อได้ (เช่น `photos/my_photo.jpg`) จึงประกาศ path parameter เป็น `{object_name:path}` (ไม่ใช่ `{object_name}` เฉยๆ) เพื่อให้ FastAPI ยอมรับ `/` ในค่าพารามิเตอร์ ไม่ตัดเป็นคนละ path segment

## Upload เป็น multipart ไม่ใช่ JSON

`POST /storage/objects/{object_name}` รับไฟล์ผ่าน `UploadFile = File(...)` ทำให้ OpenAPI generate `requestBody.content["multipart/form-data"]` แทน `"application/json"` — เป็นจุดสำคัญที่ทดสอบกับสคริปต์ `export_openapi.py` (ข้อ 3.5) ว่า loop content-type แบบ generic ได้จริง ไม่ hardcode เฉพาะ JSON

## Download แบบ stream

`GET /storage/objects/{object_name}` ไม่โหลดไฟล์ทั้งไฟล์เข้า memory ก่อนส่งกลับ แต่ใช้ `StreamingResponse` อ่านทีละ chunk จาก MinIO แล้วส่งต่อผู้เรียกทันที พร้อมปิด connection (`response.close()`/`release_conn()`) ใน `finally` เสมอ

## Error mapping

`minio.error.S3Error` ไม่มี field บอก HTTP status ตรงๆ เหมือน exception ของ Label Studio SDK แต่มี `.response` ที่เป็น HTTP response object ของ MinIO เอง จึงดึง `.response.status` มาใช้เป็น HTTP status code ของ `HTTPException` ตรงๆ

| กรณี | HTTP status | เมื่อไหร่ |
|---|---|---|
| `S3Error` (เช่น `NoSuchKey`) | มาจาก `e.response.status` (มักเป็น 404) | download/delete object ที่ไม่มีอยู่จริง |
| `S3Error` อื่นๆ | มาจาก `e.response.status`, fallback 500 | ปัญหาฝั่ง MinIO ที่ไม่รู้ status ชัดเจน |

`download_object` และ `delete_object` เรียก `stat_object` ก่อนเสมอ เพื่อบังคับให้ MinIO throw `S3Error` (แปลงเป็น 404) เมื่อ object ไม่มีจริง เพราะ `remove_object` ของ S3/MinIO เป็น idempotent (ลบ key ที่ไม่มีอยู่แล้วไม่ error) ถ้าไม่เช็คก่อนจะไม่มีทาง 404 ได้เลย

## Endpoints

| Method | Path | คำอธิบาย |
|---|---|---|
| POST | `/storage/objects/{object_name}` | อัปโหลดไฟล์ (multipart/form-data) |
| GET | `/storage/objects` | ดึงรายการไฟล์ทั้งหมดใน bucket |
| GET | `/storage/objects/{object_name}` | ดาวน์โหลดไฟล์ (stream) — 404 ถ้าไม่พบ |
| DELETE | `/storage/objects/{object_name}` | ลบไฟล์ — 404 ถ้าไม่พบ |
