# API Reference

Base URL: `http://localhost:3030`

## Authentication Endpoints

### POST /auth/login

Authenticate user and receive JWT tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

Rate limit: 5 requests per minute per IP.

### POST /auth/refresh

Get new access token using refresh token.

**Request:**
```json
{
  "refresh_token": "your-refresh-token"
}
```

**Response:**
```json
{
  "access_token": "new-access-token"
}
```

### POST /auth/logout

Revoke a refresh token (logout from device).

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "refresh_token": "token-to-revoke"
}
```

### POST /auth/logout-all

Revoke all refresh tokens for a user (admin only).

**Headers:** `Authorization: Bearer <admin-token>`

**Request:**
```json
{
  "user_id": 123
}
```

## User Endpoints (Admin Only)

All user endpoints require `Authorization: Bearer <admin-token>`.

### POST /users/

Create new user.

### GET /users/

List users with pagination?query params: `skip`, `limit`.

### GET /users/{user_id}

Get user by ID. Users can only access their own data unless admin.

### PATCH /users/{user_id}

Update user fields: `nama`, `role_id`, `is_active`.

### DELETE /users/{user_id}

Soft delete user (sets `is_active = false`).

## Role Endpoints (Admin Only)

### POST /roles/

Create new role.

### GET /roles/

List all roles.

### PATCH /roles/{role_id}

Update role name/description.

## Health Check

### GET /health

Returns: `{"status": "healthy", "service": "mte-full-stack"}`
