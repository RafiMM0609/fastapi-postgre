# PDP Multitenant Auth Service

Layanan backend otentikasi berbasis FastAPI, PostgreSQL, dan Sentry.

## Fitur

- FastAPI sebagai backend utama
- Integrasi PostgreSQL (via SQLAlchemy/asyncpg)
- Redis untuk cache/token
- Sentry untuk error monitoring
- Email (FastAPI-Mail)
- Kafka (aiokafka)
- Supabase
- File storage (Minio/local)
- JWT Authentication

## Requirements

- Python 3.11+
- PostgreSQL
- Redis
- (Opsional) Minio untuk file storage
- (Opsional) Kafka, Supabase

## Instalasi

1. Clone repository ini.
2. Install dependencies menggunakan Poetry:
   ```bash
   poetry install --no-root
   ```
3. Copy file `.env.example` (jika ada) menjadi `.env` dan sesuaikan konfigurasi environment (lihat variabel di `settings.py`).
4. Jalankan migrasi database jika diperlukan.

## Cara Menjalankan

Jalankan server FastAPI menggunakan Uvicorn:

```bash
poetry run uvicorn main:app --reload
```

Server akan berjalan di `http://localhost:8000`.

## Endpoints

- `/auth/*` : Endpoint otentikasi (lihat detail di folder `routes/auth.py`)
- `/docs` : Swagger UI (hanya di mode development)

## Struktur Project

- `main.py` : Entry point aplikasi
- `core/` : Modul utilitas, logging, email, dsb
- `models/` : Model database
- `repository/` : Repository pattern untuk akses data
- `routes/` : Routing FastAPI
- `schemas/` : Skema request/response

---

Silakan sesuaikan bagian konfigurasi environment sesuai kebutuhan project Anda.
