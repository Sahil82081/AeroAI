# Setup & Operations Guide (`docs/setup.md`)

## 1. Prerequisites

- **Python**: `3.11+` (tested with Python `3.11` – `3.13`)
- **Node.js**: `18+` and `npm`
- **Docker & Docker Compose** (optional, for containerized PostgreSQL, Redis, and Apache Kafka KRaft cluster)

---

## 2. Environment Variables

Copy `.env.example` to `.env` in the project root (or inside `backend/`):

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `PROJECT_NAME` | `"Autonomous Disruption Recovery Agent"` | Service title |
| `DATABASE_URL` | `"sqlite:///./travel_recovery.db"` | SQLAlchemy database URL (supports SQLite locally or PostgreSQL in Docker) |
| `SECRET_KEY` | `"super-secret-development-jwt-key-change-in-prod"` | JWT signing secret |
| `GEMINI_API_KEY` | `""` (Optional) | Google Gemini API key for live LLM parsing/explanations (falls back to deterministic engine when omitted) |
| `KAFKA_BOOTSTRAP_SERVERS` | `"localhost:9092"` | Apache Kafka bootstrap address |

---

## 3. Local Development Quickstart

### Step 1: Start the FastAPI Backend (`http://127.0.0.1:8000`)

```powershell
# From the repository root:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt

$env:PYTHONPATH="$PWD\backend"
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **Health Check**: `http://127.0.0.1:8000/api/v1/health`

### Step 2: Start the React + Vite SaaS Frontend (`http://127.0.0.1:5173`)

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

### Step 3: Run the Automated Pytest Integration Suite

```powershell
$env:PYTHONPATH="$PWD\backend"
.\.venv\Scripts\python -m pytest tests/backend/ -v -W ignore
```

---

## 4. Running with Docker Compose (PostgreSQL + Redis + Apache Kafka KRaft)

```bash
docker compose up --build -d
```

- **Frontend Dashboard**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
- **Kafka UI**: `http://localhost:8080`
