# Thiết lập Database: Schema + SQLAlchemy + Alembic + `.env` + Kết nối DB

Tài liệu này mô tả **các file cần thiết**, **chức năng từng file**, và **thứ tự thực hiện** để hoàn thành bước dựng nền PostgreSQL cho project Football AI.

---

## 1. Mục tiêu bước này

Sau khi hoàn thành, bạn có:

- Database PostgreSQL tên **`football_ai`** với đầy đủ bảng (leagues, matches, predictions, …).
- **SQLAlchemy ORM** map Python ↔ bảng PostgreSQL.
- **Alembic** theo dõi phiên bản schema (migration) cho các thay đổi sau này.
- File **`.env`** chứa mật khẩu / host (không commit lên git).
- **FastAPI** (và script) kết nối DB qua cùng một URL.

---

## 2. Sơ đồ luồng

```text
.env  ──►  app/core/config.py (load_dotenv + get_database_url)
                    │
                    ├──► app/db/session.py (engine, get_db)
                    │         └──► FastAPI routes (Depends(get_db))  [bước sau]
                    │
                    ├──► alembic/env.py (migration cùng URL)
                    │
                    └──► scripts/verify_db.py (kiểm tra kết nối)

db/schema/001_core_schema.sql  ──►  scripts/init_database.py  ──►  PostgreSQL
app/db/models.py               ──►  mirror bảng cho ORM + Alembic metadata
```

---

## 3. Danh sách file và chức năng

### 3.1 Cấu hình & bí mật

| File | Bắt buộc | Chức năng |
|------|----------|-----------|
| **`.env`** | Có (local) | Lưu `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`. Không đưa lên git. |
| **`.env.example`** | Khuyến nghị | Mẫu biến môi trường (password giả) cho người mới clone repo. |
| **`.gitignore`** | Có | Ghi `.env` để tránh lộ mật khẩu. |

### 3.2 Schema SQL (cấu trúc bảng)

| File | Bắt buộc | Chức năng |
|------|----------|-----------|
| **`db/schema/001_core_schema.sql`** | Có | Script SQL tạo ENUM, bảng, ràng buộc, index. Là **nguồn sự thật** cho schema v1. |

### 3.3 Script vận hành (setup / kiểm tra)

| File | Bắt buộc | Chức năng |
|------|----------|-----------|
| **`scripts/init_database.py`** | Có (lần đầu) | Tạo DB `football_ai` nếu chưa có; chạy `001_core_schema.sql`. Dùng **psycopg2** trực tiếp. |
| **`scripts/verify_db.py`** | Khuyến nghị | Kiểm tra kết nối qua **SQLAlchemy engine** (giống FastAPI). In số bảng `public`. |

Chi tiết từng dòng code: xem comment trong hai file script trên.

### 3.4 Lớp ứng dụng Python (SQLAlchemy)

| File | Bắt buộc | Chức năng |
|------|----------|-----------|
| **`app/core/config.py`** | Có | `load_dotenv()` đọc `.env`; `get_database_url()` build URL `postgresql+psycopg2://...`. |
| **`app/db/base.py`** | Có | Lớp `Base` (DeclarativeBase) — gốc cho mọi model ORM. |
| **`app/db/models.py`** | Có | Class Python tương ứng từng bảng (`League`, `Match`, `Prediction`, …). |
| **`app/db/session.py`** | Có | `engine` (pool kết nối), `SessionLocal`, `get_db()` cho FastAPI. |
| **`app/db/__init__.py`** | Tùy chọn | Re-export `Base`, `engine`, `get_db` để import gọn: `from app.db import get_db`. |
| **`app/main.py`** | Có | Import `app.core.config` **trước** để `.env` được nạp khi khởi động API. |

### 3.5 Alembic (migration)

| File | Bắt buộc | Chức năng |
|------|----------|-----------|
| **`alembic.ini`** | Có | Cấu hình Alembic (đường dẫn `alembic/`, URL mặc định — thực tế URL lấy từ `config.py`). |
| **`alembic/env.py`** | Có | Kết nối migration: import `Base.metadata`, `get_database_url()`, chạy upgrade/downgrade. |
| **`alembic/script.py.mako`** | Có | Template sinh file revision mới. |
| **`alembic/versions/0001_baseline_existing_sql.py`** | Có | Revision **baseline**: `upgrade()` rỗng vì schema đã apply bằng SQL; dùng `alembic stamp head`. |

### 3.6 Dependencies

| File | Bắt buộc | Gói liên quan DB |
|------|----------|------------------|
| **`requirements.txt`** | Có | `SQLAlchemy`, `psycopg2-binary`, `alembic`, `python-dotenv` |

---

## 4. Thứ tự chạy (checklist)

Làm **một lần** trên máy dev mới (hoặc DB trống):

1. Cài PostgreSQL, nhớ user/password.
2. Copy `.env.example` → `.env`, điền `POSTGRES_PASSWORD`, …
3. `pip install -r requirements.txt`
4. `python scripts/init_database.py` → tạo DB + bảng
5. `alembic stamp head` → đánh dấu Alembic đã ở revision baseline
6. `python scripts/verify_db.py` → mong đợi `public_table_count: 24` (hoặc gần đó)
7. `uvicorn app.main:app --reload` → API chạy (route đọc DB là bước tiếp theo)

---

## 5. Giải thích hai script (tóm tắt)

### `scripts/init_database.py`

| Phần | Mục đích |
|------|----------|
| `load_dotenv` | Đọc `.env` trước khi lấy password. |
| `_admin_conninfo()` | Tham số kết nối tới DB `postgres` (quyền tạo database). |
| `CREATE DATABASE` | Tạo `football_ai` nếu chưa có. |
| `cur.execute(sql_text)` | Chạy toàn bộ `001_core_schema.sql` trong DB `football_ai`. |

**Không** dùng trong mỗi request HTTP — chỉ setup.

### `scripts/verify_db.py`

| Phần | Mục đích |
|------|----------|
| `from app.db.session import engine` | Dùng **cùng** cấu hình với FastAPI (`get_database_url` + `.env`). |
| `SELECT COUNT(*) FROM pg_tables` | Xác nhận schema `public` có bảng (schema đã apply). |

**Không** tạo bảng — chỉ kiểm tra kết nối.

---

## 6. Alembic vs file SQL lớn

- **Lần đầu:** `001_core_schema.sql` + `init_database.py` tạo toàn bộ schema nhanh, dễ đọc.
- **Sau này:** mỗi thay đổi cột/bảng → `alembic revision` + `alembic upgrade head`.
- Revision `0001_baseline` ghi nhận: “DB hiện tại đã khớp SQL v1”, tránh Alembic tạo lại bảng trùng.

---

## 7. Kết nối FastAPI (đã có sẵn, chưa dùng trong route)

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db import get_db

@router.get("/leagues")
def list_leagues(db: Session = Depends(get_db)):
    ...
```

`get_db()` mở session mỗi request và **đóng** trong `finally` — tránh rò connection.

---

## 8. Bước tiếp theo (ngoài phạm vi “setup DB”)

1. `scripts/seed_sample.py` — chèn league/team/match mẫu.
2. Route `GET /leagues`, `GET /matches` đọc DB qua `Depends(get_db)`.
3. `GET /health/db` — health check cho deploy.

---

## 9. Tài liệu liên quan

- `docs/BEGINNER_AI_ML_PROJECT_GUIDE.md` — thuật ngữ ML & workflow tổng quan.
- `general_doc.txt` — kiến trúc feature / schema (tiếng Anh, chi tiết ML).

---

*Tài liệu này mô tả trạng thái project sau khi hoàn thành: schema + SQLAlchemy + Alembic + `.env` + kết nối DB.*
