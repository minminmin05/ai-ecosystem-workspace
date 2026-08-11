# core — Shared config & logging

Component นี้ไม่ใช่ domain/resource เหมือน `db/`, `storage/`, `annotations/`, `jobs/` แต่เป็น **infrastructure ที่ทั้ง 4 domain และ `main.py` เรียกใช้ร่วมกัน** จึงแยกไว้ที่ระดับ `backend/core/` แทนที่จะซ้ำโค้ดในแต่ละ domain

## โครงสร้างไฟล์

| ไฟล์ | หน้าที่ |
|---|---|
| `config.py` | Settings กลางของทั้งระบบ อ่านค่าจาก `backend/.env` ผ่าน `pydantic-settings` |
| `logger.py` | Custom logger factory — console handler + `RotatingFileHandler` |

## `config.py` — Settings

`Settings` (subclass ของ `pydantic_settings.BaseSettings`) รวมค่า config ของทุก component ไว้ที่เดียว: app (`host`/`port`/`debug`), MinIO, PostgreSQL, Label Studio, Redis โหลดจาก `backend/.env` อัตโนมัติผ่าน `model_config = SettingsConfigDict(env_file=...)`

ทุก domain import `settings` ตัวเดียวกัน (`from core.config import settings`) แทนที่จะอ่าน env ซ้ำเอง เช่น `db/service.py` ใช้ `settings.database_url` (property ที่ประกอบ connection string จาก `postgres_*` fields ให้), `storage/service.py` ใช้ `settings.minio_*`, `annotations/service.py` ใช้ `settings.labelstudio_*`, `jobs/service.py` ใช้ `settings.redis_*`

ค่า default ที่ตั้งไว้ในโค้ดใช้ได้กับ local dev ผ่าน `docker compose up -d` ทันที ยกเว้น `labelstudio_api_key` ที่ไม่มี default (ต้องใส่เองใน `.env` เพราะเป็น token เฉพาะ account — ดู `annotations/README.md`)

## `logger.py` — Custom logger

`get_logger(name)` คืน `logging.Logger` ที่ผูก 2 handler ไว้แล้ว:

- **Console handler** — พิมพ์ log ออกจอ ระดับ `DEBUG` ถ้า `settings.debug=True` ไม่งั้น `INFO`
- **`RotatingFileHandler`** — เขียนไฟล์ที่ `backend/logs/{name}.log` สลับไฟล์ใหม่เมื่อเกิน 5MB (`maxBytes=5*1024*1024`) เก็บย้อนหลังสูงสุด 3 ไฟล์ (`backupCount=3`) กันไฟล์ log โตไม่สิ้นสุด

มีการกัน handler ซ้ำ (`if logger.handlers: return logger`) เพื่อไม่ให้ log ซ้ำ 2 บรรทัดถ้ามีการเรียก `get_logger` ชื่อเดิมหลายครั้งจากหลายจุดในโค้ด (เช่นถูก import ซ้ำในหลาย module)

## ใครใช้บ้าง

`core/config.py` ถูก import ใน `main.py` และ `service.py` ของทั้ง 4 domain (`db/`, `storage/`, `annotations/`, `jobs/`) — เป็นจุดเดียวที่ค่า config ของระบบไหลผ่าน ไม่มี hardcoded connection string/credential กระจายอยู่ในไฟล์อื่น
