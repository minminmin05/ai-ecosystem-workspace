from core.logger import get_logger


logger = get_logger("logger_test")


def main():
    logger.debug("Debug message - ข้อมูล debug ละเอียด ใช้ตอนไล่ bug")
    logger.info("Info message - สถานะการทำงานปกติของระบบ")
    logger.warning("Warning message - มีบางอย่างผิดปกติ แต่ยังทำงานต่อได้")
    logger.error("Error message - เกิด error ขึ้นระหว่างทำงาน")
    logger.critical("Critical message - ระบบอาจใช้งานต่อไม่ได้")


if __name__ == "__main__":
    main()
