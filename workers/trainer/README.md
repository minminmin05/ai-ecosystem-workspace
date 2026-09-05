# Trainer Worker

รับงานเทรนโมเดล token classification (NER) จากคิว Redis ชื่อ `training_queue` เทรนจริงบน GPU แล้ว log ผลลัพธ์เข้า **MLflow** แทนการอัปโหลด MinIO ตรงๆ

## เปลี่ยนจาก MinIO bucket versioning มาเป็น MLflow Model Registry

เดิม (assignment ก่อนหน้า) อัปโหลดโมเดลเป็น `model.tar.gz` เข้า MinIO ตรงๆ ด้วย object key คงที่ พึ่ง MinIO bucket versioning เก็บประวัติ — พอมี MLflow แล้ว **แทนที่กลไกนั้นทั้งหมด**: ห่อโมเดล+tokenizer เป็น `transformers.pipeline(...)` แล้วเรียก `mlflow.transformers.log_model(..., registered_model_name=...)` ครั้งเดียว MLflow จัดการทั้ง 2 อย่างให้เอง:

- **Backend store** (PostgreSQL) — เก็บ metric/param ของแต่ละรอบเทรน (run) เทียบผลระหว่างรอบได้ผ่าน MLflow UI
- **Artifact store** (MinIO ผ่าน S3 API) — เก็บตัวไฟล์โมเดลจริง โดย MLflow Model Registry เป็นคนดูแล versioning ให้เอง (ไม่ต้องเปิด bucket versioning เองแบบเดิมอีกต่อไป)

```python
inference_pipeline = pipeline(
    "token-classification", model=trainer.model, tokenizer=tokenizer,
    aggregation_strategy="simple",
)
with mlflow.start_run():
    mlflow.log_params({"model_checkpoint": MODEL_CHECKPOINT, "epochs": epochs})
    mlflow.log_metrics({k: v for k, v in eval_result.items() if isinstance(v, (int, float))})
    mlflow.transformers.log_model(
        transformers_model=inference_pipeline,
        name="model",
        registered_model_name=settings.mlflow_model_name,  # "token-classification-ner"
    )
```

ทุกครั้งที่เทรนใหม่แล้วเรียกซ้ำ MLflow จะสร้าง **version ใหม่** ของ registered model ให้เองอัตโนมัติ (v1, v2, ...) — Inference Worker (`workers/inference/`) โหลดกลับผ่าน `models:/token-classification-ner/latest` เสมอได้ตัวล่าสุด

## ส่วนที่เหมือนเดิมจาก assignment ก่อนหน้า

- โหลด dataset จาก MinIO ผ่าน `load_from_disk()`/s3fs เหมือนเดิม (ไม่เกี่ยวกับ MLflow)
- log ความคืบหน้าการเทรนลงไฟล์ `.log` ผ่าน custom logger เหมือนเดิม
- รันเป็น container แยกมี GPU, ฟังเฉพาะคิว `training_queue`, offload งาน train ไป thread executor เพื่อไม่บล็อก event loop ของ ARQ — เหตุผลเดิมทั้งหมด ไม่เปลี่ยน

## Environment variables ที่ต้องตั้งเพิ่ม

| ตัวแปร | ใช้ทำอะไร |
|---|---|
| `MLFLOW_TRACKING_URI` | ที่อยู่ MLflow server (`http://mlflow:5000` ใน compose) |
| `MLFLOW_S3_ENDPOINT_URL` / `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | ให้ MLflow client อัปโหลด artifact ไปที่ MinIO (ผ่าน boto3 มาตรฐาน) |
