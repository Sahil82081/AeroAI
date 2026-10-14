import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.session import Base, get_db
from app.models.models import User, Journey, Booking, BookingType, BookingStatus
from app.core.security import get_password_hash
from datetime import datetime, timedelta

# In-memory test sqlite DB with StaticPool so all connections share the same in-memory database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

# Seed user in test database
with TestingSessionLocal() as db:
    test_user = User(
        email="traveler@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Sarah Connor",
        is_active=True,
        is_superuser=True
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    journey = Journey(
        user_id=test_user.id,
        title="SF to Tokyo Tech Summit",
        description="Test Journey",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=5),
        status="ACTIVE"
    )
    db.add(journey)
    db.commit()

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Autonomous Disruption Recovery" in data["app_name"]

def test_auth_registration_and_login():
    reg_response = client.post(
        "/api/v1/auth/register",
        json={"email": "pilot@example.com", "password": "securepassword", "full_name": "Test Pilot"}
    )
    assert reg_response.status_code == 201
    user_data = reg_response.json()
    assert user_data["email"] == "pilot@example.com"

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "pilot@example.com", "password": "securepassword"}
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Access current user
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "pilot@example.com"

def test_create_journey_and_booking():
    # Login as seeded user
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "traveler@example.com", "password": "password123"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch journeys
    j_res = client.get("/api/v1/journeys/", headers=headers)
    assert j_res.status_code == 200
    journeys = j_res.json()
    assert len(journeys) >= 1
    assert journeys[0]["title"] == "SF to Tokyo Tech Summit"

def test_faiss_semantic_search_endpoint():
    response = client.post(
        "/api/v1/chat/semantic-search",
        json={"query": "delay compensation rules", "top_k": 3}
    )
    assert response.status_code == 200
    data = response.json()
    assert "FAISS" in data["search_engine"]
    assert data["results_count"] > 0
    assert len(data["results"]) <= 3
    assert "document_title" in data["results"][0]

