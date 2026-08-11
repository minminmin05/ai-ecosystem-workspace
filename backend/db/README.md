# db — PostgreSQL / SQLAlchemy

Component นี้จัดการข้อมูลเชิงโครงสร้าง (structured data) ของระบบ เก็บอยู่ใน PostgreSQL (`ai_ecosystem` database, service `postgres` ใน `compose.yml`) เข้าถึงผ่าน SQLAlchemy ORM ตัวอย่าง resource ที่ทำไว้คือ **students** (ต่อยอดจาก `postgres_test.py` เดิมที่เคยทำ CRUD ด้วย raw SQL)

## โครงสร้างไฟล์

| ไฟล์ | หน้าที่ |
|---|---|
| `service.py` | จุดเดียวที่คุยกับ SQLAlchemy โดยตรง — engine, session, ORM model, CRUD function, และ error mapping |
| `schemas.py` | Pydantic model คุม input/output ของ API (`StudentCreate`, `StudentUpdate`, `StudentOut`) |
| `router.py` | รับ HTTP request, validate ผ่าน schema, เรียก `service.py`, ไม่คุยกับ SQLAlchemy ตรงๆ |

## Session lifecycle

`service.get_db()` เป็น generator dependency: เปิด `Session` ใหม่ทุก request แล้วปิดให้เสมอผ่าน `try/finally` แม้ endpoint จะ error กลางทาง กัน connection leak

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Route ทุกตัวประกาศเป็น **sync `def`** (ไม่ใช่ `async def`) เพราะ `psycopg2` (driver ที่ SQLAlchemy engine ใช้อยู่) เป็น library sync/blocking ล้วน ไม่มี native async — FastAPI จะรัน sync `def` path operation ในเธรดพูลให้อัตโนมัติ ทำให้ query ที่บล็อกไม่ไปอุด event loop หลัก โดยไม่ต้องเขียน `run_in_threadpool` เอง

## Error mapping

`service.py` ดัก exception ของ SQLAlchemy แล้วแปลงเป็น `HTTPException` ให้ router แค่ propagate ต่อ (FastAPI จับ `HTTPException` แล้วแปลงเป็น JSON response ให้เอง):

| Exception จาก SQLAlchemy | HTTP status | เมื่อไหร่ |
|---|---|---|
| object ไม่พบ (`Session.get()` คืน `None`) | 404 | `get_student` เรียก id ที่ไม่มีในตาราง |
| `IntegrityError` | 409 | เขียนข้อมูลที่ผิด constraint (เช่น unique/foreign key) |
| `SQLAlchemyError` อื่นๆ | 500 | ปัญหาจากฝั่ง database ที่ไม่ใช่ business error |

## Endpoints

| Method | Path | คำอธิบาย |
|---|---|---|
| POST | `/students` | สร้างนักศึกษาใหม่ |
| GET | `/students` | ดึงรายชื่อนักศึกษาทั้งหมด |
| GET | `/students/{id}` | ดึงข้อมูลนักศึกษาตาม id (404 ถ้าไม่พบ) |
| PATCH | `/students/{id}` | แก้ไขข้อมูลบางส่วน (404 ถ้าไม่พบ, 409 ถ้าผิด constraint) |
| DELETE | `/students/{id}` | ลบนักศึกษา (404 ถ้าไม่พบ) |

Response schema ของแต่ละ endpoint มาจาก **return type annotation** ของฟังก์ชันใน `router.py` (เช่น `-> StudentOut`) — FastAPI ใช้ type hint นี้เป็น `response_model` ให้อัตโนมัติ ไม่ต้องเขียน `response_model=` ซ้ำ ส่วน error response (404/409) ต้องประกาศเองผ่าน `responses={...}` เพราะ FastAPI ไม่เดาให้
