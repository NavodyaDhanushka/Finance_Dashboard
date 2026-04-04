# Finance Dashboard API

A backend REST API for a finance dashboard system built with **FastAPI** and **MySQL**.  
Supports role-based access control, financial record management, and dashboard analytics.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Framework | FastAPI | Modern Python web framework with automatic docs |
| Database | MySQL 8+ | Relational database for structured financial data |
| ORM | SQLAlchemy 2 | Database interaction and model definitions |
| Migrations | Alembic | Version-controlled schema changes |
| Auth | JWT (python-jose) | Stateless token-based authentication |
| Passwords | bcrypt (passlib) | Secure password hashing |
| Validation | Pydantic v2 | Request/response validation and serialization |

---

## Project Structure

```
finance-dashboard/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── auth.py          # Login endpoint
│   │           ├── users.py         # User management endpoints
│   │           ├── records.py       # Financial record endpoints
│   │           └── dashboard.py     # Dashboard summary endpoint
│   ├── core/
│   │   ├── config.py                # App settings loaded from .env
│   │   ├── security.py              # JWT and password hashing utilities
│   │   └── permissions.py           # Role to permission mapping
│   ├── db/
│   │   └── session.py               # Database engine and session setup
│   ├── middleware/
│   │   └── auth.py                  # Auth dependencies and permission checks
│   ├── models/
│   │   ├── user.py                  # User database model
│   │   └── financial_record.py      # Financial record database model
│   ├── schemas/
│   │   ├── user.py                  # User request/response schemas
│   │   ├── financial_record.py      # Record request/response schemas
│   │   └── dashboard.py             # Dashboard response schemas
│   ├── services/
│   │   ├── user_service.py          # User business logic
│   │   ├── record_service.py        # Record business logic
│   │   └── dashboard_service.py     # Dashboard aggregation logic
│   └── main.py                      # App factory and startup
├── alembic/                         # Database migration scripts
├── scripts/
│   └── init_db.py                   # One-time database setup and seeding
├── .env.example                     # Environment variable template
├── requirements.txt                 # Python dependencies
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- MySQL 8+

### 1. Clone the repository

```bash
git clone <repo-url>
cd finance-dashboard
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> If you get a bcrypt version error, run: `pip install bcrypt==4.0.1`

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your MySQL credentials:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=finance_dashboard
SECRET_KEY=your-long-random-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 5. Initialize the database

```bash
python scripts/init_db.py
```

This will create the database, all tables, and seed three demo users:

| Email | Password | Role |
|---|---|---|
| admin@example.com | Admin1234! | Admin |
| analyst@example.com | Analyst123! | Analyst |
| viewer@example.com | Viewer123! | Viewer |

### 6. Start the server

```bash
python -m uvicorn app.main:app --reload
```

The API is now running at **http://localhost:8000**

| URL | Description |
|---|---|
| http://localhost:8000/docs | Swagger UI — interactive API docs |
| http://localhost:8000/redoc | ReDoc — clean API reference |
| http://localhost:8000/health | Health check |

---

## Roles and Permissions

The system has three roles with different levels of access.

### Role Overview

| Role | Description |
|---|---|
| **Admin** | Full access — manages records and users |
| **Analyst** | Read access to records and advanced insights |
| **Viewer** | Read-only access to records and basic dashboard |

### Permission Table

| Action | Viewer | Analyst | Admin |
|---|:---:|:---:|:---:|
| View records | ✅ | ✅ | ✅ |
| Create records | ❌ | ❌ | ✅ |
| Edit records | ❌ | ❌ | ✅ |
| Delete records | ❌ | ❌ | ✅ |
| View dashboard | ✅ | ✅ | ✅ |
| View insights | ❌ | ✅ | ✅ |
| View users | ❌ | ❌ | ✅ |
| Create users | ❌ | ❌ | ✅ |
| Edit users | ❌ | ❌ | ✅ |
| Delete users | ❌ | ❌ | ✅ |

Permissions are enforced on every route using the `require_permission()` dependency in `middleware/auth.py`. Business logic in the service layer has no knowledge of auth concerns.

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | Login with email and password, returns JWT token |

**Request body:**
```json
{
  "email": "admin@example.com",
  "password": "Admin1234!"
}
```

---

### Users *(Admin only)*

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/users` | List all users (paginated) |
| POST | `/api/v1/users` | Create a new user |
| GET | `/api/v1/users/me` | Get current logged-in user |
| GET | `/api/v1/users/{id}` | Get a user by ID |
| PATCH | `/api/v1/users/{id}` | Update a user |
| DELETE | `/api/v1/users/{id}` | Delete a user |

---

### Financial Records

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/v1/records` | Viewer+ | List records with optional filters |
| POST | `/api/v1/records` | Admin | Create a new record |
| GET | `/api/v1/records/{id}` | Viewer+ | Get a single record by ID |
| PATCH | `/api/v1/records/{id}` | Admin | Update a record |
| DELETE | `/api/v1/records/{id}` | Admin | Soft delete a record |

**Available filters for `GET /api/v1/records`:**

| Parameter | Type | Example |
|---|---|---|
| `type` | `income` or `expense` | `?type=expense` |
| `category` | string | `?category=rent` |
| `date_from` | YYYY-MM-DD | `?date_from=2024-01-01` |
| `date_to` | YYYY-MM-DD | `?date_to=2024-03-31` |
| `page` | integer | `?page=2` |
| `page_size` | integer (max 100) | `?page_size=50` |

---

### Dashboard

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/v1/dashboard/summary` | Viewer+ | Aggregated financial summary |

**Optional date range:** `?date_from=2024-01-01&date_to=2024-12-31`

**Response includes:**
- Total income, total expenses, net balance
- Income breakdown by category
- Expense breakdown by category
- Monthly trends (income vs expenses per month)
- Recent activity (last 10 records)

---

## How Authentication Works

1. Call `POST /api/v1/auth/login` with your email and password
2. The API returns a JWT access token
3. Include the token in the `Authorization` header for every request:
   ```
   Authorization: Bearer <your_token>
   ```
4. Tokens expire after 24 hours (configurable in `.env`)

**Testing in Swagger UI:**
1. Login via `POST /api/v1/auth/login`
2. Copy the `access_token` from the response
3. Click the **Authorize** 🔒 button at the top right of the Swagger page
4. Enter `Bearer <your_token>` and click Authorize
5. All subsequent requests in Swagger will include your token automatically

---

## Database Schema

### `users` table

| Column | Type | Description |
|---|---|---|
| id | INT | Primary key |
| email | VARCHAR | Unique email address |
| full_name | VARCHAR | Display name |
| hashed_password | VARCHAR | bcrypt hashed password |
| role | ENUM | viewer, analyst, or admin |
| is_active | BOOLEAN | Account active status |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

### `financial_records` table

| Column | Type | Description |
|---|---|---|
| id | INT | Primary key |
| amount | DECIMAL | Record amount (must be positive) |
| type | ENUM | income or expense |
| category | VARCHAR | Category name (stored lowercase) |
| record_date | DATE | Date of the transaction |
| description | TEXT | Optional notes |
| is_deleted | BOOLEAN | Soft delete flag |
| created_by | INT | Foreign key to users.id |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

> Composite indexes on `(type, record_date)` and `(category, record_date)` are applied for dashboard query performance.

---

## Running Tests

Tests use an in-memory SQLite database — no MySQL required.

```bash
pytest -v
```

The test suite covers authentication, role-based access control, record CRUD operations, filtering, soft delete, input validation, and dashboard aggregation.

---

## Database Migrations

After making any changes to a model, generate and apply a migration:

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

---

## Design Decisions

**Soft Deletes** — Records are never physically removed from the database. The `is_deleted` flag is set to `True` instead. This preserves the full audit history and allows data recovery if needed.

**Flat Permission Map** — Permissions are defined as a static dictionary in `core/permissions.py` rather than a database-driven table. This keeps the implementation simple and easy to understand while being straightforward to extend later.

**Category Normalisation** — Categories are automatically converted to lowercase and trimmed of whitespace when saved. This prevents duplicate entries like `Rent` and `rent` from appearing as separate categories in analytics.

**Admin Self-Protection** — An admin cannot deactivate, demote, or delete their own account. This prevents accidental lockouts.

**Stateless JWT Auth** — No session storage or refresh tokens are used. Each token is self-contained and expires after 24 hours. This makes the API stateless and easy to scale.

---

## License

This project was built as a backend engineering assessment. Free to use and modify.