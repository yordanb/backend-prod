# MTE Full Stack Backend

Production-ready IoT backend dengan FastAPI + MySQL + Redis + Alembic migrations.

## Features

- ✅ Async FastAPI dengan SQLAlchemy (aiomysql)
- ✅ JWT authentication (access + refresh token) dengan bcrypt
- ✅ RBAC: role-based access control (admin, user)
- ✅ Refresh token rotation dan revoke
- ✅ Audit logging untuk semua aksi penting
- ✅ Rate limiting pada login (5 attempts per menit)
- ✅ Redis untuk caching, token blacklist, dan broker worker
- ✅ Alembic migrations (WAJIB)
- ✅ Dual DB user: app_user (terbatas) + root/admin
- ✅ Docker & Docker Compose konfigurasi production
- ✅ Health check endpoint
- ✅ Structured logging (tambahan sesuai kebutuhan)

## Struktur Folder

```
backend/
├── alembic/                 # Alembic migration files
│   ├── versions/            # Migration scripts (auto-generated)
│   ├── env.py
│   └── script.py.mako
├── src/
│   ├── api/
│   │   └── main_router.py   # Aggregator router
│   ├── core/
│   │   ├── config.py        # Pydantic settings (DB, SECRET_KEY, REDIS)
│   │   ├── database.py      # Async engine & session factory
│   │   ├── limiter.py       # Rate limiting (slowapi)
│   │   ├── redis.py         # Redis client setup
│   │   └── security.py      # JWT, bcrypt utilities
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── router.py    # /auth/login, /auth/refresh, /auth/logout
│   │   │   └── service.py   # Auth business logic
│   │   ├── user/
│   │   │   ├── model.py     # User, RefreshToken, AuditLog models
│   │   │   ├── repository.py# DB operations
│   │   │   ├── router.py    # CRUD endpoints (admin only)
│   │   │   └── schemas.py   # Pydantic schemas
│   │   └── role/
│   │       ├── model.py
│   │       ├── repository.py
│   │       ├── router.py
│   │       └── schemas.py
│   ├── deps.py              # FastAPI dependencies (auth, RBAC)
│   └── main.py              # FastAPI app & lifespan
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── alembic.ini
└── init-db.sql              # MySQL init script (create app_user)
```

## Setup & Run

### 1. Environment Variables

Copy `.env.example` ke `.env` di folder `backend/`:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` sesuai environment Anda. Minimal:

```env
DB_URL=mysql+aiomysql://app_user:app_password@db:3306/testdb
DB_ADMIN_URL=mysql+aiomysql://root:password@db:3306/testdb
SECRET_KEY=your-super-secret-jwt-key-min-32-chars
REDIS_URL=redis://redis:6379/0
```

**Catatan keamanan:**
- Ganti `SECRET_KEY` dengan random string yang kuat (minimal 32 karakter)
- Di production, gunakan secret management (Docker secrets, Vault, dll)

### 2. Docker Compose (Recommended)

```bash
cd backend
docker-compose up --build -d
```

Services:
- API: http://localhost:3030
- API Docs (Swagger): http://localhost:3030/docs
- MySQL: localhost:3306
- Redis: localhost:6379

### 3. Database Migrations

Migrations dijalankan otomatis oleh service `alembic` (profil `migrations`).

```bash
# Run migrations only
docker-compose --profile migrations up
```

Atau manual di dalam container:

```bash
docker-compose exec api alembic upgrade head
```

Create initial migration (jika ada perubahan model):

```bash
docker-compose exec api alembic revision --autogenerate -m "descriptive message"
```

### 4. Initial Data: Roles

System memerlukan role `admin` dan `user`. Buat via API atau DB seed:

```sql
INSERT INTO roles (id, name, description) VALUES
(1, 'admin', 'Administrator with full access'),
(2, 'user', 'Regular user');
```

### 5. Testing API

1. Buka http://localhost:3030/docs
2. Login dengan user yang sudah ada (jika belum ada, buat via DB seed atau POST /users/)
3. Akses protected endpoints dengan header `Authorization: Bearer <access_token>`

## API Endpoints

### Authentication
- `POST /auth/login` - Login (rate limited: 5/menit per IP)
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Revoke single refresh token
- `POST /auth/logout-all` - Revoke all refresh tokens (admin only)

### Users (admin only)
- `POST /users/` - Create user
- `GET /users/` - List all users
- `GET /users/{id}` - Get user by ID (users can access self)
- `PATCH /users/{id}` - Update user
- `DELETE /users/{id}` - Soft delete (deactivate)

### Roles (admin only)
- `POST /roles/` - Create role
- `GET /roles/` - List all roles
- `PATCH /roles/{id}` - Update role

### Health
- `GET /health` - Health check

## Architecture Notes

### Dual DB User
- `root`: untuk migrations dan admin tasks (DB_ADMIN_URL)
- `app_user`: untuk aplikasi sehari-hari (DB_URL) dengan privileges terbatas

### Token Management
- Access token: 30 menit
- Refresh token: 7 hari
- Refresh token rotation: setiap refresh, token lama di-revoke
- Token revoke disimpan di DB (hashed) dan Redis blacklist
- Redis blacklist: expiry 1 jam (cukup untuk mencegah reuse)

### Rate Limiting
- Login: 5 attempts per minute per IP address
- Dapat diatur per endpoint via `@limiter.limit("...")`

### Audit Log
- dicatat di tabel `audit_logs`
- mencakup: user_id, action, resource_type, resource_id, ip_address, user_agent, details

### Redis Usage
- Cache umum (future)
- Token blacklist (fast lookup untuk invalidated refresh tokens)
- Message broker untuk worker (future Celery integration)

### Workers
Container `worker` siap untuk background tasks (Celery, custom worker).
Gunakan profile `worker` untuk aktifkan:
```bash
docker-compose --profile worker up
```

## Production Considerations

1. **SECRET_KEY**: Gunakan secret management, bukan hardcoded
2. **Database**: Gunakan managed MySQL atau replicated setup
3. **Redis**: Gunakan Redis Cluster / Sentinel untuk HA
4. **HTTPS**: Letakkan di balik reverse proxy (nginx, Traefik)
5. **Monitoring**: Tambahkan logging aggregator (ELK, Loki)
6. **Metrics**: Prometheus + Grafana endpoint (bisa tambah di main.py)
7. **CORS**: Sesuaikan `allow_origins` di main.py jika butuh
8. **Backup**: Database backup schedule (volume snapshot atau mysqldump)

## License

MIT
