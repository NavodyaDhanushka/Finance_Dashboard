"""
tests/test_api.py
─────────────────
Integration tests using an in-memory SQLite database so MySQL is not required
to run the test suite.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import Base, get_db
from app.core.security import hash_password
from app.core.permissions import UserRole
from app.models.user import User
from app.models.financial_record import FinancialRecord  # noqa

# ── SQLite in-memory engine for tests ────────────────────────────────────────
SQLITE_URL = "sqlite:///./test_finance.db"
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSession()
    yield session
    session.close()


@pytest.fixture
def client():
    return TestClient(app)


def _make_user(db, email="admin@test.com", role=UserRole.ADMIN, password="Secret123!"):
    user = User(
        email=email,
        full_name="Test User",
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(client, email, password="Secret123!"):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── Auth tests ────────────────────────────────────────────────────────────────

class TestAuth:
    def test_login_success(self, client, db):
        _make_user(db)
        resp = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Secret123!"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client, db):
        _make_user(db)
        resp = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_unknown_user(self, client):
        resp = client.post("/api/v1/auth/login", json={"email": "nobody@x.com", "password": "pass"})
        assert resp.status_code == 401

    def test_protected_route_requires_token(self, client):
        resp = client.get("/api/v1/users")
        assert resp.status_code == 403

    def test_inactive_user_cannot_login(self, client, db):
        user = _make_user(db)
        user.is_active = False
        db.commit()
        resp = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Secret123!"})
        assert resp.status_code == 403


# ── User management tests ─────────────────────────────────────────────────────

class TestUsers:
    def test_admin_can_list_users(self, client, db):
        _make_user(db)
        token = _login(client, "admin@test.com")
        resp = client.get("/api/v1/users", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_viewer_cannot_list_users(self, client, db):
        _make_user(db, email="viewer@test.com", role=UserRole.VIEWER)
        token = _login(client, "viewer@test.com")
        resp = client.get("/api/v1/users", headers=_auth(token))
        assert resp.status_code == 403

    def test_admin_can_create_user(self, client, db):
        _make_user(db)
        token = _login(client, "admin@test.com")
        resp = client.post(
            "/api/v1/users",
            json={"email": "new@test.com", "full_name": "New User", "password": "NewPass1!", "role": "viewer"},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        assert resp.json()["email"] == "new@test.com"

    def test_duplicate_email_rejected(self, client, db):
        _make_user(db)
        token = _login(client, "admin@test.com")
        payload = {"email": "admin@test.com", "full_name": "Dup", "password": "Dup12345!"}
        resp = client.post("/api/v1/users", json=payload, headers=_auth(token))
        assert resp.status_code == 409

    def test_get_me(self, client, db):
        _make_user(db)
        token = _login(client, "admin@test.com")
        resp = client.get("/api/v1/users/me", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "admin@test.com"

    def test_admin_cannot_delete_themselves(self, client, db):
        user = _make_user(db)
        token = _login(client, "admin@test.com")
        resp = client.delete(f"/api/v1/users/{user.id}", headers=_auth(token))
        assert resp.status_code == 400


# ── Financial record tests ────────────────────────────────────────────────────

class TestRecords:
    def _create_record(self, client, token):
        return client.post(
            "/api/v1/records",
            json={
                "amount": "1500.00",
                "type": "income",
                "category": "salary",
                "record_date": "2024-03-01",
                "description": "March salary",
            },
            headers=_auth(token),
        )

    def test_admin_can_create_record(self, client, db):
        _make_user(db)
        token = _login(client, "admin@test.com")
        resp = self._create_record(client, token)
        assert resp.status_code == 201
        assert resp.json()["category"] == "salary"

    def test_viewer_cannot_create_record(self, client, db):
        _make_user(db, email="viewer@test.com", role=UserRole.VIEWER)
        token = _login(client, "viewer@test.com")
        resp = self._create_record(client, token)
        assert resp.status_code == 403

    def test_viewer_can_list_records(self, client, db):
        _make_user(db, email="viewer@test.com", role=UserRole.VIEWER)
        token = _login(client, "viewer@test.com")
        resp = client.get("/api/v1/records", headers=_auth(token))
        assert resp.status_code == 200

    def test_filter_by_type(self, client, db):
        _make_user(db)
        token = _login(client, "admin@test.com")
        self._create_record(client, token)
        resp = client.get("/api/v1/records?type=income", headers=_auth(token))
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["type"] == "income"

    def test_update_record(self, client, db):
        _make_user(db)
        token = _login(client, "admin@test.com")
        created = self._create_record(client, token).json()
        resp = client.patch(
            f"/api/v1/records/{created['id']}",
            json={"amount": "2000.00"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert float(resp.json()["amount"]) == 2000.0

    def test_soft_delete(self, client, db):
        _make_user(db)
        token = _login(client, "admin@test.com")
        created = self._create_record(client, token).json()
        del_resp = client.delete(f"/api/v1/records/{created['id']}", headers=_auth(token))
        assert del_resp.status_code == 204
        # Record should no longer appear in listings
        list_resp = client.get("/api/v1/records", headers=_auth(token))
        ids = [r["id"] for r in list_resp.json()["items"]]
        assert created["id"] not in ids

    def test_negative_amount_rejected(self, client, db):
        _make_user(db)
        token = _login(client, "admin@test.com")
        resp = client.post(
            "/api/v1/records",
            json={"amount": "-100", "type": "income", "category": "x", "record_date": "2024-01-01"},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_invalid_type_rejected(self, client, db):
        _make_user(db)
        token = _login(client, "admin@test.com")
        resp = client.post(
            "/api/v1/records",
            json={"amount": "100", "type": "donation", "category": "x", "record_date": "2024-01-01"},
            headers=_auth(token),
        )
        assert resp.status_code == 422


# ── Dashboard tests ───────────────────────────────────────────────────────────

class TestDashboard:
    def test_summary_accessible_by_viewer(self, client, db):
        _make_user(db, email="viewer@test.com", role=UserRole.VIEWER)
        token = _login(client, "viewer@test.com")
        resp = client.get("/api/v1/dashboard/summary", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "net_balance" in data

    def test_summary_reflects_records(self, client, db):
        _make_user(db)
        token = _login(client, "admin@test.com")
        client.post(
            "/api/v1/records",
            json={"amount": "5000", "type": "income", "category": "salary", "record_date": "2024-03-01"},
            headers=_auth(token),
        )
        client.post(
            "/api/v1/records",
            json={"amount": "1200", "type": "expense", "category": "rent", "record_date": "2024-03-05"},
            headers=_auth(token),
        )
        resp = client.get("/api/v1/dashboard/summary", headers=_auth(token))
        data = resp.json()
        assert float(data["total_income"]) == 5000.0
        assert float(data["total_expenses"]) == 1200.0
        assert float(data["net_balance"]) == 3800.0
