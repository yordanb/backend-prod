# API Reference

Base URL: `http://localhost:3030`

## Versioned API

All business endpoints are under `/api/v1`.

---

## 🔐 Authentication (`/api/v1/auth`)

### POST `/auth/id-cek`

Authenticate device using Android ID (device-based auth).

**Request:**
```json
{
  "androidID": "device-android-id-here"
}
```

**Response:**
```json
{
  "status": "already_registered",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "nrp": "12345",
    "nama": "John Doe",
    "email": "john@example.com",
    "role": { ... }
  }
}
```

**Notes:**
- Returns 404 if device not registered.
- Updates `last_used` timestamp on device.

---

### POST `/auth/login`

Authenticate user with email/NRP and password. Optionally accepts `androidId` for device pairing.

**Request:**
```json
{
  "identifier": "user@example.com",
  "password": "password123",
  "androidId": "optional-android-id"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "nrp": "12345",
    "nama": "John Doe",
    "email": "john@example.com",
    "role": { ... }
  }
}
```

**Rate Limit:** 5 requests per minute per IP.

---

### POST `/auth/refresh`

Exchange refresh token for new access + refresh token (rotation).

**Request:**
```json
{
  "refresh_token": "refresh-token-here"
}
```

**Response:**
```json
{
  "access_token": "new-access-token",
  "refresh_token": "new-refresh-token",
  "token_type": "bearer"
}
```

---

### POST `/auth/logout`

Revoke a specific refresh token (logout from one device).

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "refresh_token": "token-to-revoke"
}
```

**Response:** `{"message": "Logged out successfully"}`

---

### POST `/auth/logout-all`

Revoke all refresh tokens for a user (admin only).

**Headers:** `Authorization: Bearer <admin-access-token>`

**Request:**
```json
{
  "user_id": 123
}
```

**Response:**
```json
{
  "message": "Revoked X refresh tokens",
  "user_id": 123
}
```

---

## 👥 Users (`/api/v1/users`) — Admin Only (except self-access)

### POST `/users/`

Create new user.

**Headers:** `Authorization: Bearer <admin-token>`

**Request:**
```json
{
  "email": "newuser@example.com",
  "nrp": "67890",
  "nama": "New User",
  "password": "plaintext-or-hashed?",
  "role_id": 2
}
```

**Response:** Full user object (without password).

**Rate Limit:** 10/minute.

---

### GET `/users/`

List all users with pagination.

**Headers:** `Authorization: Bearer <admin-token>`

**Query Params:**
- `skip` (int): Offset, default 0
- `limit` (int): Max results, default 100

**Response:** Array of user objects.

---

### GET `/users/{user_id}`

Get user by ID.

**Headers:** `Authorization: Bearer <access-token>`

**Access Control:**
- Admin: can access any user.
- Regular user: can only access their own data.

**Response:** User object.

---

### PATCH `/users/{user_id}`

Update user fields.

**Headers:** `Authorization: Bearer <admin-token>`

**Request (all optional):**
```json
{
  "nama": "Updated Name",
  "role_id": 3,
  "is_active": true
}
```

**Response:** Updated user object.

---

### DELETE `/users/{user_id}`

Soft delete user (sets `is_active = false`).

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** `{"message": "User deactivated"}`

---

## 🛡️ Roles (`/api/v1/roles`) — Admin Only

### POST `/roles/`

Create new role.

**Headers:** `Authorization: Bearer <admin-token>`

**Request:**
```json
{
  "name": "supervisor",
  "description": "Can view and edit reports"
}
```

**Response:** Role object.

---

### GET `/roles/`

List all roles.

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** Array of role objects.

---

### PATCH `/roles/{role_id}`

Update role.

**Headers:** `Authorization: Bearer <admin-token>`

**Request (all optional):**
```json
{
  "name": "new-role-name",
  "description": "Updated description"
}
```

**Response:** Updated role object.

---

## 👷 Manpower (`/api/v1/manpower`) — Employee CRUD

### GET `/manpower/`

List employees with optional filters.

**Headers:** `Authorization: Bearer <access-token>`

**Access Control:**
- Admin: can see all employees.
- User: can only see employees they created.

**Query Params:**
- `skip` (int): Offset, default 0
- `limit` (int): Max results, default 100
- `section` (string, optional): Filter by section
- `crew` (string, optional): Filter by crew
- `is_active` (bool): Filter active status, default `true`

**Response:** Array of employee objects.

---

### GET `/manpower/{employee_id}`

Get employee by ID.

**Headers:** `Authorization: Bearer <access-token>`

**Access Control:**
- Admin: can access any employee.
- User: can only access employees they created.

**Response:** Employee object.

---

### POST `/manpower/`

Create new employee.

**Headers:** `Authorization: Bearer <admin-token>`

**Request:**
```json
{
  "nrp": "11111",
  "nama": "Employee Name",
  "section": "A",
  "crew": "1",
  "posisi": "Operator",
  "target_ss": 100,
  "status": "Aktif",
  "jabatan": "Staff",
  "last_update": "2025-04-07",
  "email": "employee@example.com", // optional
  "phone": "08123456789" // optional
}
```

**Response:** Created employee object.

**Validation:**
- NRP must be unique.
- Email must be unique if provided.

---

### PATCH `/manpower/{employee_id}`

Update employee.

**Headers:** `Authorization: Bearer <admin-token>`

**Request:** Same fields as POST, all optional.

**Response:** Updated employee object.

---

### DELETE `/manpower/{employee_id}`

Soft delete employee (set `is_active = false`).

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** `{"message": "Employee deactivated successfully"}`

---

### POST `/manpower/import`

Import employees from CSV file.

**Headers:** `Authorization: Bearer <admin-token>`

**Content-Type:** `multipart/form-data`

**Form Field:** `file` (CSV)

**Expected CSV Columns** (case-sensitive):
- `NRP`
- `Nama`
- `Section`
- `Crew`
- `Posisi`
- `TargetSS`
- `Status`
- `Jabatan`
- `LastUpdate`

**Response:**
```json
{
  "total": 100,
  "success": 95,
  "failed": 5,
  "errors": [
    {"row": 10, "error": "NRP already exists"},
    ...
  ]
}
```

---

## ⚙️ Admin (`/api/v1/admin`) — Admin Only

### User Management

#### GET `/admin/users`

List users with pagination and search.

**Headers:** `Authorization: Bearer <admin-token>`

**Query Params:**
- `page` (int): Page number, default 1
- `limit` (int): Items per page, default 20, max 100
- `search` (string, optional): Search by NRP or email

**Response:**
```json
{
  "data": [ ... ],
  "total": 150,
  "page": 1,
  "limit": 20,
  "totalPages": 8
}
```

---

#### POST `/admin/users`

Create user (query parameters version).

**Headers:** `Authorization: Bearer <admin-token>`

**Query Params:**
- `nrp` (string, required)
- `nama` (string, required)
- `email` (string, required)
- `password` (string, required)
- `role_id` (int, optional, default 2)

**Response:** User object.

---

#### GET `/admin/users/{id}`

Get user by ID.

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** User object.

---

#### PUT `/admin/users/{id}`

Update user (all via query parameters).

**Headers:** `Authorization: Bearer <admin-token>`

**Query Params** (all optional):
- `nrp`
- `nama`
- `email`
- `role_id`
- `is_active`

**Response:** Updated user object.

---

#### POST `/admin/users/{id}/reset-password`

Reset user password to random string.

**Headers:** `Authorization: Bearer <admin-token>`

**Response:**
```json
{
  "password": "XyZ789!abc"
}
```

**Note:** Password is returned in plaintext (only once). All refresh tokens for user are revoked.

---

#### DELETE `/admin/users/{id}`

Deactivate user (soft delete) and revoke all tokens.

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** `{"message": "User deactivated"}`

---

### Device Management

#### GET `/admin/devices`

List all device pairings with user info.

**Headers:** `Authorization: Bearer <admin-token>`

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "android_id": "device-abc123",
      "user_id": 5,
      "user": {
        "id": 5,
        "nrp": "12345",
        "nama": "John Doe",
        "email": "john@example.com",
        "role_name": "user"
      },
      "created_at": "2025-04-07T03:00:00Z",
      "last_used_at": "2025-04-07T06:30:00Z"
    }
  ],
  "total": 1
}
```

---

#### DELETE `/admin/devices/{android_id}`

Unpair device (remove from `device_pairing`).

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** `{"message": "Device unpaired"}`

---

### Audit Logs

#### GET `/admin/audit-logs`

List audit logs with filters.

**Headers:** `Authorization: Bearer <admin-token>`

**Query Params:**
- `page` (int): default 1
- `limit` (int): default 20, max 100
- `action` (string, optional): Filter by action type
- `user_id` (int, optional): Filter by user ID
- `start_date` (string, YYYY-MM-DD, optional)
- `end_date` (string, YYYY-MM-DD, optional)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "user_id": 5,
      "action": "user.login",
      "ip_address": "192.168.1.100",
      "details": "{\"android_id\": \"abc123\"}",
      "created_at": "2025-04-07T03:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 20,
  "totalPages": 3
}
```

---

## ❤️ Health Check

### GET `/health`

Public health check (unversioned, accessible without auth).

**Response:**
```json
{
  "status": "healthy",
  "service": "mte-full-stack"
}
```

---

### GET `/api/v1/health`

Versioned health check (same response, plus version).

**Response:**
```json
{
  "status": "healthy",
  "service": "mte-full-stack",
  "version": "v1"
}
```

---

## 📊 OpenAPI / Swagger

- **Swagger UI (Interactive):** `http://localhost:3030/docs`
- **ReDoc:** `http://localhost:3030/redoc`
- **OpenAPI JSON:** `http://localhost:3030/openapi.json`

---

## 🔒 Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/auth/login` | 5/minute per IP |
| `/users/` (create) | 10/minute per user |
| Others | Default (configurable in `src/core/limiter.py`) |

---

## 🔑 Authentication Scheme

All protected endpoints use **Bearer token**:

```
Authorization: Bearer <access_token>
```

Access tokens are short-lived (typically 15-30 minutes). Use `/auth/refresh` to obtain new tokens.

---

## 🏷️ Tags (Swagger)

- `auth` — Authentication endpoints
- `users` — User management
- `roles` — Role management
- `manpower` — Employee (manpower) CRUD
- `admin` — Admin utilities (users, devices, audit logs)

---

**Last Updated:** 2025-04-07 (based on source code review)
