"""
Kiểm tra kết nối PostgreSQL qua SQLAlchemy (cùng engine với FastAPI).

Chạy từ thư mục gốc project:
  python scripts/verify_db.py

Kết quả mong đợi sau init_database.py: public_table_count: 24
"""

from __future__ import annotations  # Hỗ trợ type hint hiện đại

import sys  # Để thêm repo root vào sys.path
from pathlib import Path  # Xác định đường dẫn tương đối tới gốc project

# Thư mục football-ai-app (một cấp trên scripts/)
_REPO_ROOT = Path(__file__).resolve().parents[1]
# Bắt buộc: khi chạy `python scripts/verify_db.py`, Python mặc định không thấy package `app`
sys.path.insert(0, str(_REPO_ROOT))

from sqlalchemy import text  # Viết câu SQL thô an toàn qua SQLAlchemy

from app.db.session import engine  # Engine đã gọi get_database_url() + load .env qua config

def main() -> None:
    """Mở một kết nối, đếm bảng public, in ra console."""
    with engine.connect() as conn:  # Lấy connection từ pool (giống cách app dùng DB)
        n = conn.execute(
            # Đếm bảng trong schema `public` — xác nhận schema đã được apply
            text("SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public'")
        ).scalar()  # Lấy một giá trị số duy nhất từ kết quả
        print("public_table_count:", n)  # ~24 nếu 001_core_schema.sql chạy đủ


if __name__ == "__main__":
    main()  # Entry point khi chạy script trực tiếp
