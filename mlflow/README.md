# mlflow — Model tracking & registry

MLflow server ใช้เป็น model registry กลางของระบบ — Trainer Worker log โมเดล/metric เข้ามาที่นี่แทนที่จะอัปโหลด MinIO ตรงๆ แบบ assignment ก่อนหน้า, Inference Worker โหลดโมเดลที่ผ่านการ register แล้วกลับออกไปใช้งาน

## ใช้ infrastructure เดิม ไม่เปิด storage ใหม่

- **Backend store** (metadata: run, metric, param, model version) → database `mlflow` ใน PostgreSQL container เดิม (คนละ database กับ `ai_ecosystem` แต่อยู่ instance เดียวกัน)
- **Artifact store** (ตัวไฟล์โมเดลจริง) → bucket `ai-ecosystem` ใน MinIO เดิม ภายใต้ prefix `mlflow/` (ผ่าน S3 API ที่ MinIO รองรับอยู่แล้ว)

## Database `mlflow` ต้องมีก่อน MLflow server จะ start ได้

`postgres-init/001-create-mlflow-db.sql` จะรันให้อัตโนมัติ **เฉพาะตอน postgres container init ครั้งแรก** (data dir ว่างเปล่า) ถ้า volume `postgresql-data` มีข้อมูลเก่าอยู่แล้ว (เช่นเครื่องที่เคยรัน assignment ก่อนหน้ามา) ต้องสร้างเองด้วยมือครั้งเดียว:

```bash
docker exec postgres psql -U postgres -c "CREATE DATABASE mlflow;"
```

## Environment variables ที่ต้องตั้ง (ดูใน `compose.yml`)

| ตัวแปร | ใช้ทำอะไร |
|---|---|
| `MLFLOW_BACKEND_STORE_URI` | connection string ไปยัง database `mlflow` ใน PostgreSQL |
| `MLFLOW_ARTIFACT_ROOT` | `s3://ai-ecosystem/mlflow` — path เก็บ artifact ใน MinIO |
| `MLFLOW_S3_ENDPOINT_URL` (ฝั่ง client) | ชี้ MLflow client ให้อัปโหลด S3 ไปที่ MinIO แทน AWS จริง |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` (ฝั่ง client) | credential ของ MinIO (MLflow ใช้ boto3 มาตรฐาน ชื่อตัวแปรเลยเป็น AWS_* แม้จะไม่ใช่ AWS จริง) |

## ใช้งาน

- UI: http://localhost:5000
- Trainer Worker เรียก `mlflow.transformers.log_model(..., registered_model_name="token-classification-ner")` — MLflow จัดการ version ของโมเดลให้เองผ่าน Model Registry (แทนที่ MinIO bucket versioning ที่ทำไว้ใน assignment ก่อนหน้า)
- Inference Worker โหลดโมเดลกลับผ่าน `mlflow.transformers.load_model("models:/token-classification-ner/latest")`
