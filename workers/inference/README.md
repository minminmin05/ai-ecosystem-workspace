# Inference Worker

รับงานทำนาย (token classification / NER) จากคิว Redis ชื่อ `inference_queue` โดยโหลดโมเดลที่ Trainer Worker log ไว้ใน MLflow Model Registry มาใช้

## โหลดโมเดลครั้งเดียวตอน worker เริ่มทำงาน ไม่ใช่ทุก request

`predict.py` เรียก `mlflow.transformers.load_model("models:/token-classification-ner/latest")` ที่ **module level** (ตอน import ครั้งแรก ก่อน worker เริ่มรับงานจริง) แล้วเก็บ pipeline ไว้ใน memory ตลอดอายุ process — ตรงกับที่โจทย์ต้องการ "รอรับการสั่งใช้งาน" คือมีโมเดลพร้อมอยู่แล้วตลอดเวลา ไม่ใช่โหลดใหม่ทุกครั้งที่มี request เข้ามา (ซึ่งช้ากว่ามาก เพราะต้องโหลด weight จาก MinIO ผ่าน MLflow ทุกรอบ)

## ทำไมไม่ใช้ GPU (ต่างจาก Trainer Worker)

โมเดล `distilbert-base-uncased` ขนาดเล็ก inference ทีละ 1 ข้อความบน CPU เร็วพอ (< 1 วินาที) ไม่คุ้มที่จะแย่ง GPU ตัวเดียวในเครื่องจาก Trainer Worker เพราะเทรนกับ inference อาจมาชนกันได้ถ้าใช้ GPU เดียวกันพร้อมกัน — Dockerfile ใช้ `torch` เวอร์ชัน CPU-only (`--index-url https://download.pytorch.org/whl/cpu`) ทำให้ image เล็กกว่าด้วย

## ทำไม route/function เป็น `async def` แต่ offload งานจริงไปอีก thread

เหมือนเหตุผลใน Trainer Worker — `pipeline(text)` ของ transformers เป็น synchronous call ล้วน เรียกตรงใน `async def` จะบล็อก event loop ของ ARQ worker จึงใช้ `loop.run_in_executor()` ห่อไว้

## Endpoints ที่เกี่ยวข้อง (ฝั่ง FastAPI)

ดู `backend/inference/README.md` — ยิงงานเข้าคิวผ่าน `POST /inference/predict` แล้วเช็คผลผ่าน `GET /jobs/{job_id}?queue_name=inference_queue` (endpoint เดิมจาก `jobs/` domain ไม่ได้สร้างใหม่)
