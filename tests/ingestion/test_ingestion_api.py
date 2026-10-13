import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.session import Base, get_db
from app.models.models import User, Journey, IngestedEmail, Booking, EmailParsingStatus
from app.core.security import get_password_hash
from app.datasets.sample_emails import SAMPLE_EMAILS
from datetime import datetime, timedelta

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

def test_ingestion_endpoints_flow():
    # 1. Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "traveler@example.com", "password": "password123"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get samples
    samples_res = client.get("/api/v1/ingestion/samples")
    assert samples_res.status_code == 200
    samples = samples_res.json()
    assert len(samples) >= 5

    # 3. Forward a sample flight email
    flight_sample = next(s for s in samples if s["id"] == "flight-indigo-6e")
    forward_res = client.post(
        "/api/v1/ingestion/forward",
        headers=headers,
        json={
            "sender": flight_sample["sender"],
            "subject": flight_sample["subject"],
            "body": flight_sample["body"],
            "force_parser": "heuristic"
        }
    )
    assert forward_res.status_code == 201
    ingested_data = forward_res.json()
    assert ingested_data["parsing_status"] == "PARSED"
    assert ingested_data["booking_type"] == "flight"
    assert ingested_data["confidence_score"] >= 0.8
    assert ingested_data["booking_id"] is not None

    # 4. Verify duplicate detection on forwarding same email
    dup_res = client.post(
        "/api/v1/ingestion/forward",
        headers=headers,
        json={
            "sender": flight_sample["sender"],
            "subject": flight_sample["subject"],
            "body": flight_sample["body"],
            "force_parser": "heuristic"
        }
    )
    assert dup_res.status_code == 201
    dup_data = dup_res.json()
    assert dup_data["parsing_status"] == "DUPLICATE"
    assert "Duplicate booking reference" in dup_data["error_message"]

    # 5. Forward an imperfect email and check uncertainty + clarification
    imperfect_sample = next(s for s in samples if s["id"] == "imperfect-flight-forward")
    imp_res = client.post(
        "/api/v1/ingestion/forward",
        headers=headers,
        json={
            "sender": imperfect_sample["sender"],
            "subject": imperfect_sample["subject"],
            "body": imperfect_sample["body"],
            "force_parser": "heuristic"
        }
    )
    assert imp_res.status_code == 201
    imp_data = imp_res.json()
    assert imp_data["parsing_status"] == "UNCERTAIN"
    assert len(imp_data["missing_fields"]) > 0
    assert imp_data["clarification_prompt"] is not None

    # 6. Check inbox list
    inbox_res = client.get("/api/v1/ingestion/inbox", headers=headers)
    assert inbox_res.status_code == 200
    inbox_items = inbox_res.json()
    assert len(inbox_items) >= 3
