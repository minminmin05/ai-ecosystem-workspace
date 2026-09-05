FROM python:3.11-slim

# psycopg2-binary = ต่อ PostgreSQL (backend store), boto3 = ต่อ MinIO ผ่าน S3 API (artifact store)
RUN pip install --no-cache-dir mlflow psycopg2-binary boto3

EXPOSE 5000

# client (Trainer/Inference Worker) อัปโหลด artifact เข้า MinIO ตรงๆ ด้วย credential ของตัวเอง
# (ผ่าน AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY/MLFLOW_S3_ENDPOINT_URL) ไม่ผ่าน proxy ของ server
# server ตัวนี้จึงแค่เก็บ backend store (metadata) + บอก path ที่ควรอัปโหลดไปเท่านั้น
# backend-store-uri / default-artifact-root ตั้งผ่าน environment variable ใน compose.yml
#
# --allowed-hosts: mlflow >=3.x เปิด DNS-rebinding protection มาให้โดย default (block ทุก
# Host header ที่ไม่ใช่ localhost/private IP ตรงเป๊ะ) client ตัวอื่นเรียกผ่านชื่อ service
# "mlflow" (compose network) โดน block ไปด้วย (403 "Invalid Host header") ต้องเปิดชื่อนี้เอง
CMD mlflow server \
    --host 0.0.0.0 \
    --port 5000 \
    --backend-store-uri "$MLFLOW_BACKEND_STORE_URI" \
    --default-artifact-root "$MLFLOW_ARTIFACT_ROOT" \
    --allowed-hosts "mlflow,mlflow:5000,localhost,localhost:5000,127.0.0.1,127.0.0.1:5000"
