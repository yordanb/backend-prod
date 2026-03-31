# Architecture Overview

## Stack & Design Principles

- **Framework**: FastAPI (async, modern, OpenAPI auto-generation)
- **Database**: MySQL 8.0 dengan SQLAlchemy ORM (async via aiomysql)
- **Cache/Broker**: Redis 7 (async client)
- **Migrations**: Alembic
- **Auth**: JWT (access + refresh) dengan bcrypt
- **Containerization**: Docker + Docker Compose
- **Architecture**: Modular hexagonal-ish, separation of concerns

## High-Level Flow

```
Client Request
    ↓
FastAPI Router
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (DB Operations)
    ↓
SQLAlchemy Async Engine → MySQL
                ↓
            (Optional) Redis Cache/Blacklist
```

## Module Structure

```
src/
├── core/           # Shared infrastructure
│   ├── config.py      # Pydantic settings
│   ├── database.py    # Engine, Session, Base
│   ├── redis.py       # Redis client
│   ├── security.py    # JWT, bcrypt
│   └── limiter.py     # Rate limiting
├── modules/        # Feature modules
│   ├── auth/          # Authentication service
│   ├── user/          # User CRUD, models, schemas
│   └── role/          # Role management
├── api/            # API layer
│   └── main_router.py # Router aggregator
├── deps.py         # FastAPI dependencies (auth, RBAC)
└── main.py         # App factory
```

## Database Schema

### `roles`
- `id` (PK)
- `name` (unique) - admin, user
- `description`
- `created_at`

### `users`
- `id` (PK)
- `nama`
- `email` (unique, indexed)
- `password` (hashed bcrypt)
- `role_id` (FK → roles.id)
- `is_active` (soft delete)
- `created_at`, `updated_at`

### `refresh_tokens`
- `id` (PK)
- `user_id` (FK → users.id)
- `jti` (unique UUID)
- `token_hash` (hashed refresh token)
- `revoked` (bool)
- `expires_at`
- `created_at`

### `audit_logs`
- `id` (PK)
- `user_id` (FK → users.id, nullable for system)
- `action` (string) - login.success, user.create, token.revoke, etc.
- `resource_type` (optional)
- `resource_id` (optional)
- `ip_address`
- `user_agent`
- `details` (JSON string)
- `created_at`

## Authentication Flow

### Login
1. Client POST `/auth/login` with credentials
2. Rate limit check (5/menit per IP)
3. Verify password (bcrypt)
4. Generate:
   - Access token (30min, contains `sub=user_id`, `role`)
   - Refresh token (7 hari, contains `jti=uuid`)
5. Hash refresh token dan store ke `refresh_tokens` table
6. Return both tokens
7. Log audit: `login.success`

### Access Protected Endpoint
1. Client includes `Authorization: Bearer <access_token>`
2. `get_current_user()` dependency decodes & validates token
3. `require_roles([...])` checks user role (RBAC)
4. Proceed to handler

### Refresh Access Token
1. Client POST `/auth/refresh` dengan refresh token
2. Verify token signature & expiry
3. Check `jti` in DB (exists, not revoked)
4. Verify token hash (defense-in-depth)
5. **Revoke old token** (set revoked=1, add to Redis blacklist)
6. Generate new access token
7. Log audit: `token.refresh`
8. Return new access token

### Logout (single device)
1. Client POST `/auth/logout` dengan refresh token
2. Revoke that token in DB dan Redis
3. Log audit: `token.revoke`

## Redis Usage

- **Token Blacklist**: `blacklist:{jti}` → "1" dengan expiry 3600s (1 jam)
  Cek before accepting refresh token
- **Cache** (future): session data, rate limit counters (sudah pakai slowapi default memory)
- **Message Broker** (future): Celery atau async task queue

## Rate Limiting

- Implementasi: `slowapi` (bucket-based)
- Middleware: `SlowAPIMiddleware` di app
- Endpoint `/auth/login`: 5 requests per minute per IP
- Dapat diatur per endpoint
- Disimpan di memory (single instance) atau Redis untuk multi-instance

## RBAC

- Roles stored in `roles` table
- User memiliki `role_id` FK ke roles
- Dependency `require_roles(['admin', 'user'])` inject payload user
- Implementasi: simple string comparison
- Future: bisa tambah permission system (many-to-many roles ↔ permissions)

## Audit Logging

Setiap aksi penting tercatat di `audit_logs`:
- login success/failure
- user CRUD
- token revoke
- role changes
- IP address & user agent dicatat untuk forensic

## Dual DB User

### `root` (DB_ADMIN_URL)
- Privileges penuh
- Digunakan untuk:
  - Alembic migrations (create/alter tables)
  - Backup/restore operations

### `app_user` (DB_URL)
- Privileges terbatas: SELECT, INSERT, UPDATE, DELETE pada semua tabel
- Tidak bisa CREATE/ALTER/DROP (only admin)
- Digunakan oleh aplikasi sehari-hari (API)
- Dposta via `init-db.sql` saat MySQL container start

## Error Handling

HTTPExceptions:
- 400: Bad request (missing fields, validation)
- 401: Unauthorized (invalid credentials, invalid token)
- 403: Forbidden (insufficient role)
- 404: Not found (user/role tidak ada)
- 429: Too many requests (rate limit)
- 500: Server error (generic)

Custom exception handler untuk `RateLimitExceeded` -> 429

## Testing Strategy (Not implemented yet)

- Unit tests: service layer (mocked DB)
- Integration tests: test API endpoints dengan test database
- Load testing: Locust atau k6 untuk rate limiting & concurrency

## Future Extensions

1. **MQTT Integration** (IoT backend): separate module di `src/modules/mqtt/`
2. **Celery Worker**: background tasks (email, notifications)
3. **Device Management**: `src/modules/device/` untuk ESP32 provisioning
4. **Telemetry**: time-series data (InfluxDB atau TimescaleDB)
5. **API Versioning**: `/api/v1/`
6. **Multi-tenancy**: if needed
7. **OpenID Connect**: SSO integration (optional)

## Security Considerations

- Tokens: JWT signed dengan HS256 (SECRET_KEY)
- Password: bcrypt (adaptive hashing)
- SQL Injection: prevented by SQLAlchemy ORM
- XSS: tidak relevan (API only)
- CSRF: tidak berlaku untuk stateless JWT API
- Rate limiting: mencegah brute force
- Refresh token rotation: mencegah token theft
- Token blacklist: mencegah reuse setelah logout

## Performance

- Async all the things: FastAPI async endpoints, aiomysql driver
- Connection pooling: SQLAlchemy engine pool
- Redis: fast lookup untuk blacklist (O(1))
- No N+1 queries: eager loading dengan `selectinload` di repository
- Response times目标是 <100ms untuk大多数 endpoints (pada normal load)

---

Kesimpulan: Arsitektur ini siap untuk production IoT backend dengan skalabilitas, keamanan, dan maintainability.
