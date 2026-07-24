import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from core.config import settings


LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    # กัน handler ซ้ำถ้ามีการเรียก get_logger ชื่อเดิมหลายครั้ง
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # RotatingFileHandler: กันไฟล์ log โตไม่สิ้นสุด สลับไฟล์ใหม่เมื่อเกิน maxBytes
    file_handler = RotatingFileHandler(
        LOG_DIR / f"{name}.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
