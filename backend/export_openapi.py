"""
สร้าง "Snapshot" ของ API ทั้งหมดในระบบ โดยดึง OpenAPI schema จากตัว FastAPI app
โดยตรง (ไม่ต้องมี server รันอยู่จริง) แล้วแปลงเป็นตาราง Excel/CSV

หลักการ:
1. import `app` จาก main.py แล้วเรียก app.openapi() -> ได้ dict ของ OpenAPI spec
2. วน paths -> methods (operation) ทีละตัว ดึง summary/tags/request/response ออกมา
3. request/response ส่วนใหญ่อ้างอิงผ่าน "$ref": "#/components/schemas/XXX" ไม่ใช่
   schema แบบ inline ต้อง resolve เอาแค่ "ชื่อ schema" ที่ถูกอ้างอิงออกมาโชว์
   (ไม่ expand ลึกถึงระดับ field เพราะโจทย์ต้องการแค่ snapshot รายการ API)
4. บาง endpoint (เช่น upload ไฟล์) อาจไม่ใช่ content-type "application/json"
   (เช่น "multipart/form-data") ต้อง loop content type แบบ generic ไม่ hardcode
"""

from pathlib import Path

import pandas as pd

from main import app


OUTPUT_DIR = Path(__file__).parent
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def resolve_schema_name(schema: dict) -> str:
    """คืนชื่อ schema แบบสั้น ไม่ expand field ย่อย (พอสำหรับ snapshot ระดับ endpoint)"""
    if not schema:
        return ""
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if schema.get("type") == "array":
        return f"array[{resolve_schema_name(schema.get('items', {}))}]"
    if "anyOf" in schema:
        return " | ".join(resolve_schema_name(s) for s in schema["anyOf"])
    return schema.get("type", "object")


def describe_content(content: dict) -> str:
    """content = {"application/json": {"schema": {...}}, "multipart/form-data": {...}, ...}
    loop แบบ generic ไม่ hardcode media type เดียว เพราะ endpoint upload ไฟล์จะไม่ใช่ JSON"""
    parts = []
    for media_type, media_obj in content.items():
        schema_name = resolve_schema_name(media_obj.get("schema", {}))
        parts.append(f"{media_type}: {schema_name}" if schema_name else media_type)
    return "; ".join(parts)


def describe_responses(responses: dict) -> str:
    parts = []
    for status_code, response in responses.items():
        content = response.get("content", {})
        if not content:
            parts.append(status_code)
            continue
        parts.append(f"{status_code} ({describe_content(content)})")
    return "; ".join(parts)


def build_rows(spec: dict) -> list[dict]:
    rows = []
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS:
                continue
            request_body = operation.get("requestBody", {}).get("content", {})
            rows.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "tags": ", ".join(operation.get("tags", [])),
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "request_body": describe_content(request_body),
                    "responses": describe_responses(operation.get("responses", {})),
                    "deprecated": operation.get("deprecated", False),
                }
            )
    return rows


def main():
    spec = app.openapi()
    rows = build_rows(spec)
    df = pd.DataFrame(rows)

    xlsx_path = OUTPUT_DIR / "openapi_snapshot.xlsx"
    csv_path = OUTPUT_DIR / "openapi_snapshot.csv"

    df.to_excel(xlsx_path, index=False)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"API version: {spec.get('info', {}).get('version')}")
    print(f"Total endpoints: {len(df)}")
    print(f"Saved: {xlsx_path}")
    print(f"Saved: {csv_path}")


if __name__ == "__main__":
    main()
