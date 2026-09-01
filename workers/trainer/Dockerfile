# ใช้ image ของ pytorch เองแทน python:slim + uv เหมือนตัวอื่นในโปรเจกต์
# เพราะ image นี้ build torch มาพร้อม CUDA runtime ที่ match กันแล้ว
# ถ้าใช้ uv/pip install "torch" ซ้ำจะเสี่ยงได้ wheel ผิดตัว (เช่น CPU-only)
# ทับของเดิมที่ตั้งใจให้ตรงกับ CUDA ของ image นี้อยู่แล้ว
FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "arq", "worker_settings.WorkerSettings"]
