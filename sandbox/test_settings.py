import sys
from pathlib import Path

# เพิ่ม backend เข้า python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from core.config import settings


def main():
    print("=== Settings Test ===")
    print(f"App Name : {settings.app_name}")
    print(f"Debug    : {settings.debug}")
    print(f"Host     : {settings.host}")
    print(f"Port     : {settings.port}")


if __name__ == "__main__":
    main()