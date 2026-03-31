# Deployment Guide

## Local Development

1. Clone repo dan masuk ke folder `backend/`
2. Install dependencies: `pip install -r requirements.txt`
3. Start MySQL dan Redis (Docker atau lokal):
   ```bash
   docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=password -e MYSQL_DATABASE=testdb mysql:8.0
   docker run -d -p 6379:6379 redis:7-alpine
   ```
4. Copy `.env.example` ke `.env` dan sesuaikan
5. Run migrations: `alembic upgrade head`
6. Seed roles: `python scripts/seed_roles.py`
7. Start server: `uvicorn src.main:app --reload`

## Production with Docker Compose

```bash
cd backend
docker-compose up -d --build
```

Check status:
```bash
docker-compose ps
docker-compose logs -f api
```

Access:
- API: http://localhost:3030
- Swagger UI: http://localhost:3030/docs

## Running Migrations

Auto-migration (dijalankan otomatis oleh service `alembic` saat startup):

```bash
# Start all services + migration
docker-compose up -d
```

Manual:
```bash
docker-compose exec api alembic upgrade head
```

Create new migration:
```bash
docker-compose exec api alembic revision --autogenerate -m "description"
```

## Environment Variables

Semua env vars terletak di file `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `DB_URL` | ✅ | MySQL async URL (app_user) |
| `DB_ADMIN_URL` | ✅ | MySQL async URL (root) |
| `SECRET_KEY` | ✅ | JWT signing secret (min 32 chars) |
| `REDIS_URL` | ✅ | Redis connection URL |

## Health Checks

API exposes `/health` endpoint. Docker Compose healthcheck:
- Retries: 3
- Interval: 30s
- Start period: 40s
- Timeout: 10s

## Scaling

Untuk horizontal scaling API:

1. Pastikan session state stateless (JWT stateless sudah baik)
2. Redis akan mensharing blacklist antar instance
3. Database connection pool (SQLAlchemy) handles concurrent connections
4. Tambah load balancer (nginx, Traefik) di depan API instances

```yaml
# docker-compose.yml - scale api
services:
  api:
    deploy:
      replicas: 3
```

Juga bisa gunakan `docker-compose up --scale api=3` (jika不使用 swarm mode perlu ajustemen).

## Monitoring

- Application logs: `docker-compose logs -f api`
- Database logs: `docker-compose logs -f db`
- Redis logs: `docker-compose logs -f redis`

Untuk production, pertimbangkan:
- ELK stack (Elasticsearch, Logstash, Kibana)
- Loki + Grafana
- Prometheus metrics endpoint (tambahkan di FastAPI)

## Backup & Restore

### MySQL Backup

```bash
docker-compose exec db mysqldump -u root -p testdb > backup_$(date +%F).sql
```

Restore:
```bash
docker-compose exec -T db mysql -u root -p testdb < backup_2025-03-29.sql
```

### Redis Persistence

Redis menggunakan AOF (append-only file) otomatis di volume `redis_data`. Backup volume.

## Security Checklist

- [ ] Ganti `SECRET_KEY` dengan random 64+ chars
- [ ] Gunakan HTTPS (reverse proxy dengan SSL/TLS)
- [ ] Firewall: expose hanya port 443/80 ke public
- [ ] Database: restrict app_user privileges sesuka?
- [ ] Rotate JWT secret secara periodik (invalidate existing tokens)
- [ ] Set `SECURE_PROXY_SSL_HEADER` jika di balik proxy
- [ ] Enable CORS hanya untuk domain frontend tertentu
- [ ] Rate limiting sudah di login, pertimbangkan di endpoint lain
- [ ] Enable MySQL slow query log
- [ ] Monitoring & alerting untuk failed login attempts

## Performance Optimization

1. **Database indexing**: Tambah index di kolom yang sering dicari (email, user_id di refresh_tokens, jti)
2. **Redis connection pooling**: gunakan connection pool (sudah default di redis-py)
3. **API response compression**: enable GZip di nginx atau FastAPI middleware
4. **Async everything**: semua endpoint sudah async, pastikan tidak ada blocking call

## Troubleshooting

### Migration errors
```bash
docker-compose down -v  # HAPUS DATA! hati-hati
docker-compose up --build
```

### Cannot connect to database
Cek apakah MySQL container sudah healthy:
```bash
docker-compose ps db
docker-compose logs db
```

### Redis connection refused
Pastikan Redis container running dan healthcheck passed.

### 401Unauthorized despite valid token
- Cek apakah token expired (access token 30min)
- Cek apakah refresh token masih valid
- Cek audit_log untuk login history
