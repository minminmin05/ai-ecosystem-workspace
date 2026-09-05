-- รันอัตโนมัติเฉพาะตอน postgres container init ครั้งแรก (data dir ว่างเปล่า)
-- ถ้า volume มีข้อมูลอยู่ก่อนแล้ว ต้องสร้าง database นี้เองด้วยมือ (ดู mlflow/README.md)
CREATE DATABASE mlflow;
