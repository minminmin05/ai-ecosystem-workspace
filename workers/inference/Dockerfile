FROM python:3.11-slim

WORKDIR /app

# torch แบบ CPU-only เท่านั้น (Inference Worker ไม่ต้องใช้ GPU ตามที่คุยกันไว้)
# ใช้ index ของ pytorch เองที่ให้ wheel ตัดส่วน CUDA ออก เล็กกว่า wheel มาตรฐานจาก PyPI มาก
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "arq", "worker_settings.WorkerSettings"]
