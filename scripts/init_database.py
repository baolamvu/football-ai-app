"""
Tạo database `football_ai` (nếu chưa có) và áp dụng db/schema/001_core_schema.sql.

Chạy từ thư mục gốc project:
  python scripts/init_database.py

Đọc mật khẩu / host từ file .env (load_dotenv).
"""

from __future__ import annotations  # Cho phép dùng kiểu gợi ý (dict[str, str]) mà không cần quote

import os  # Đọc biến môi trường POSTGRES_* sau khi load .env
import sys  # Thêm thư mục gốc project vào sys.path (nếu sau này import app.*)
from pathlib import Path  # Làm việc với đường dẫn file schema / .env an toàn trên Windows

# REPO_ROOT = thư mục football-ai-app (cha của scripts/)
REPO_ROOT = Path(__file__).resolve().parents[1]
# Cho Python tìm được package `app` khi chạy: python scripts/init_database.py
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # Thư viện đọc file .env vào os.environ

# Nạp .env từ gốc project trước khi đọc POSTGRES_PASSWORD, v.v.
load_dotenv(REPO_ROOT / ".env")

import psycopg2  # Driver PostgreSQL thuần (không qua SQLAlchemy)
from psycopg2 import sql  # Tạo câu SQL an toàn (tránh SQL injection khi tên DB động)
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT  # CREATE DATABASE không chạy trong transaction

# File SQL chứa CREATE TABLE, ENUM, INDEX
SCHEMA_PATH = REPO_ROOT / "db" / "schema" / "001_core_schema.sql"
# Tên database ứng dụng (mặc định football_ai, có thể đổi trong .env)
DB_NAME = os.getenv("POSTGRES_DB", "football_ai")


def _admin_conninfo() -> dict[str, str]:
    """
    Trả về tham số kết nối psycopg2 (host, port, user, password, dbname).
    Lần đầu kết nối vào database `postgres` để có quyền CREATE DATABASE.
    """
    admin_url = os.getenv("ADMIN_DATABASE_URL")
    if admin_url:
        # Nếu user cung cấp URL đầy đủ thay vì từng biến POSTGRES_*
        from urllib.parse import urlparse

        u = urlparse(admin_url)
        return {
            "host": u.hostname or "localhost",
            "port": str(u.port or 5432),
            "user": u.username or "postgres",
            "password": u.password or "",
            "dbname": u.path.lstrip("/") or "postgres",  # Thường là database `postgres`
        }
    # Cách mặc định: đọc từng biến trong .env
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "user": os.getenv("POSTGRES_USER", "lamvb"),
        "password": os.getenv("POSTGRES_PASSWORD", "lam123"),
        "dbname": os.getenv("POSTGRES_ADMIN_DB", "postgres"),  # DB hệ thống để tạo DB mới
    }


def main() -> None:
    """Luồng chính: tạo DB (nếu cần) → chạy file schema SQL."""
    if not SCHEMA_PATH.is_file():
        raise SystemExit(f"Schema file not found: {SCHEMA_PATH}")

    admin = _admin_conninfo()
    # Bước 1: kết nối database `postgres` (hoặc dbname trong ADMIN_DATABASE_URL)
    conn = psycopg2.connect(**admin)
    # CREATE DATABASE phải AUTOCOMMIT; không bọc trong transaction thường
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            # Kiểm tra football_ai đã tồn tại chưa
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (DB_NAME,),
            )
            exists = cur.fetchone() is not None
            if not exists:
                # Tạo database an toàn: sql.Identifier escape tên DB
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
                print(f"Created database {DB_NAME!r}.")
            else:
                print(f"Database {DB_NAME!r} already exists.")
    finally:
        conn.close()  # Đóng kết nối admin

    # Bước 2: kết nối trực tiếp vào football_ai để tạo bảng
    app_params = {**_admin_conninfo(), "dbname": DB_NAME}
    conn = psycopg2.connect(**app_params)
    try:
        sql_text = SCHEMA_PATH.read_text(encoding="utf-8")  # Đọc toàn bộ 001_core_schema.sql
        with conn.cursor() as cur:
            cur.execute(sql_text)  # Chạy CREATE TYPE, CREATE TABLE, CREATE INDEX, ...
        conn.commit()  # Ghi các thay đổi schema (transaction bình thường)
        print(f"Applied schema from {SCHEMA_PATH}.")
    finally:
        conn.close()


if __name__ == "__main__":
    # Chỉ chạy main() khi gọi trực tiếp: python scripts/init_database.py
    main()
