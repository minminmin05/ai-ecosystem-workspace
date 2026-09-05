# inference — Predict queue

Component นี้เป็นประตูสั่งงาน "ทำนายด้วยโมเดลที่เทรนไว้" ไม่ได้รัน inference เองในนี้ — งานจริงเกิดที่ **Inference Worker** (`workers/inference/`) ซึ่งเป็นคนละ container/process แยกจาก FastAPI (เหตุผลเดียวกับ `training/`)

## `POST /inference/predict` — เข้าคิวสั่งทำนาย

ไม่ได้สร้างกลไก queue ใหม่ — เรียกใช้ `jobs.service.enqueue_job()` ตัวเดิมซ้ำ (ตัวเดียวกับที่ `training/` ใช้) โดยกำหนดค่าคงที่ 2 ตัวเฉพาะของงาน inference:

- **`function="predict_token_classification"`** — ต้องตรงกับชื่อฟังก์ชันที่ลงทะเบียนไว้ใน `workers/inference/worker_settings.py`
- **`queue_name="inference_queue"`** — แยกจากทั้งคิวงานทั่วไป (`arq:queue`) และคิวงานเทรน (`training_queue`) เพราะ inference ต้องการ **ตอบเร็ว** (< 1 วินาที) ถ้าไปติดคิวรวมกับงานเทรนที่ใช้เวลาเป็นนาที ผู้ใช้จะรอนานโดยไม่จำเป็น

## เช็คผล — ใช้ endpoint เดิมจาก `jobs/`

`GET /jobs/{job_id}?queue_name=inference_queue` (endpoint เดิมที่มีอยู่แล้ว ไม่ได้สร้างใหม่) ตอบกลับ `result.entities` เป็นรายการ entity ที่โมเดลทำนายได้ เมื่อ status เป็น `complete`

## Endpoints

| Method | Path | คำอธิบาย |
|---|---|---|
| POST | `/inference/predict` | ส่ง `{"text": "..."}` เข้าคิวทำนาย ตอบกลับ `job_id` |
