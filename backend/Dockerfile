FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# ติดตั้ง dependency ก่อน copy โค้อดที่เหลือ เพื่อให้ Docker cache layer นี้ไว้
# (โค้ดเปลี่ยนบ่อยกว่า dependency มาก rebuild แล้วไม่ต้องโหลด package ใหม่ทุกครั้ง)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "python", "main.py"]
