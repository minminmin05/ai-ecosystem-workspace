# training — Dataset ingestion + Train queue

Component นี้เป็นประตูสั่งงาน "เตรียม dataset" และ "สั่งเทรนโมเดล" ไม่ได้เทรนโมเดลเองในนี้ — งานเทรนจริงเกิดที่ **Trainer Worker** (`workers/trainer/`) ซึ่งเป็นคนละ container/process แยกจาก FastAPI

## `POST /training/datasets/import` — ดึง dataset จาก Hugging Face เข้า MinIO

ใช้ HF `datasets` library โหลด dataset token classification (CoNLL-2003 NER) จาก Hugging Face Hub แล้วเขียนตรงเข้า MinIO ผ่าน **s3fs** (S3-compatible filesystem interface ที่ `datasets.save_to_disk()` รองรับ URI แบบ `s3://bucket/prefix` โดยตรง):

```python
dataset = load_dataset("lhoestq/conll2003")
dataset.save_to_disk(
    f"s3://{settings.minio_bucket}/datasets/conll2003",
    storage_options={
        "key": settings.minio_access_key,
        "secret": settings.minio_secret_key,
        "client_kwargs": {"endpoint_url": f"http://{settings.minio_endpoint}"},
    },
)
```

ข้อดีของวิธีนี้: ไม่ต้อง save ลง disk ก่อนแล้วค่อยวน loop upload ทีละไฟล์เอง — `datasets` เขียนตรงผ่าน fsspec ให้ทั้งหมด (Arrow shard files + metadata) เป็น route เดียวจบ

**หมายเหตุการเลือก dataset:** ตั้งใจจะใช้ `conll2003` (repo ต้นฉบับ) ตอนแรก แต่ทดสอบแล้วพบว่า `datasets` library เวอร์ชันปัจจุบันเลิกรองรับ dataset ที่ใช้ loading script แบบเก่าแล้ว (error: `Dataset scripts are no longer supported, but found conll2003.py`) แม้จะลองใส่ `trust_remote_code=True` ก็ไม่ช่วย เพราะ argument นี้ถูกถอดออกไปแล้วเช่นกัน จึงเปลี่ยนไปใช้ **`lhoestq/conll2003`** ซึ่งเป็น mirror ที่แปลงเป็น Parquet แล้ว (ดูแลโดยหนึ่งใน maintainer ของ `datasets` library เอง) — schema และจำนวนแถวต่อ split (train 14,041 / validation 3,250 / test 3,453) ตรงกับ conll2003 ต้นฉบับทุกประการ

ข้อแตกต่างเล็กน้อย: mirror นี้เก็บคอลัมน์ `ner_tags` เป็น `int64` ธรรมดา ไม่มี `ClassLabel` metadataติดมา (repo ต้นฉบับมี) ฝั่ง Trainer Worker เลย hardcode รายชื่อ label เอง (`["O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-LOC", "I-LOC", "B-MISC", "I-MISC"]` — เรียงลำดับมาตรฐานของ conll2003) แทนการอ่านจาก dataset features

Route นี้เป็น sync `def` เพราะ `datasets`/`s3fs` เป็น library แบบ blocking (เหตุผลเดียวกับ `db/`/`storage/`)

## `POST /training/queue` — เข้าคิวสั่งเทรน

ไม่ได้สร้างกลไก queue ใหม่ — เรียกใช้ `jobs.service.enqueue_job()` ตัวเดิม (ที่ `jobs/` ขยายให้รองรับ `start_at`/`queue_name` แล้ว) โดยกำหนดค่าคงที่ 2 ตัวเฉพาะของ training:

- **`function="train_token_classification"`** — ต้องตรงกับชื่อฟังก์ชันที่ลงทะเบียนไว้ใน `workers/trainer/worker_settings.py`
- **`queue_name="training_queue"`** — แยกจากคิวงานทั่วไป (`worker_settings.py` ของ `backend/`) เพื่อไม่ให้งานเทรน (หนัก/นาน/ใช้ GPU) ไปติดคิวรวมกับงานเบาอื่น และให้ Trainer Worker (คนละ container, มี GPU) เป็นคนเดียวที่ดึงงานจากคิวนี้ไปทำ

`start_at` (ถ้าระบุ) ส่งต่อเป็น ARQ's `_defer_until` ตรงๆ — Trainer Worker จะไม่เริ่มงานจนกว่าจะถึงเวลานั้น

เช็คสถานะ/ผลลัพธ์ของ job ที่ได้ (`job_id`) ผ่าน endpoint เดิม **`GET /jobs/{job_id}?queue_name=training_queue`** (ต้องใส่ `queue_name` ให้ตรงกับตอน enqueue ไม่งั้นจะหา job ไม่เจอ)

## Endpoints

| Method | Path | คำอธิบาย |
|---|---|---|
| POST | `/training/datasets/import` | ดึง `conll2003` จาก Hugging Face เข้า MinIO |
| POST | `/training/queue` | เข้าคิวสั่งเทรน รับ `epochs` + `start_at` (optional) |
