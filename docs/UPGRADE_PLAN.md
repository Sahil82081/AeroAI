# TripWeave AI — Engineering Upgrade Plan

> **Target Version**: 2.0.0 (Portfolio-Quality AI/ML Engineering Platform)  
> **Target Role Standard**: Senior AI/ML Engineer / Staff AI Systems Engineer  
> **Branch**: `dev`  
> **Status**: Awaiting User Approval (Stage 0 Audit Completed)

---

## 1. Vision & Architecture Evolution

### 1.1 Current Architecture vs. Proposed Target Architecture

```
CURRENT (Demo Disruption Recovery System):
==================================================
Isolated Silos:
- Disruption Engine (Hardcoded delays, e.g. 240 mins)
- NetworkX Journey Graph (Delhi flight-to-train cascade)
- Google OR-Tools CP-SAT (Rebooking selection)
- 8-Node LangGraph Recovery Agent (Post-disruption only)
- Policy RAG (MD5 hash pseudo-embeddings + string heuristics)
- News RSS Feed (Google News RSS)
- Mock Supplier APIs (In-memory static arrays)

PROPOSED (TripWeave AI - Agentic Flight Intelligence Platform):
==================================================
               User Query / Flight Lookup
                           │
                           ▼
                  TripWeave AI Agent
        (Intelligent Intent & Tool Orchestration)
                           │
      ┌────────────┬───────┴───────┬────────────┐
      ▼            ▼               ▼            ▼
  Flight Tool   Weather Tool   Delay ML Tool  Policy RAG
  (Flight-      (Weather-      (XGBoost /     (Dense Vector
  Provider:     Provider:      SHAP Explai-   Retrieval +
  Mock /        Live /         ner + BTS      Citation
  OpenSky)      Historical)    Trained)       Grounding)
      │            │               │            │
      └────────────┴───────┬───────┴────────────┘
                           ▼
             Evidence-Grounded Synthesizer
       (Strict Separation of ML Prediction, Weather,
        Live Status, Policy Citations, & Recommendations)
                           │
                           ▼
       FastAPI Unified REST & WebSocket Gateway
                           │
                           ▼
      React 18 SaaS Flight Intelligence Dashboard
  (Delay Risk Gauge, SHAP Impact Breakdown, Agent Chat)
```

---

## 2. Core Engineering Principles

1. **Zero Data Fabrication**: All ML models trained on real aviation data (BTS / Kaggle); real numbers reported in evaluations; zero benchmark invention.
2. **Strict Prevention of ML Data Leakage**: Features partitioned rigorously into *Known Before Departure* (scheduled departure hour, day of week, carrier delay history, origin congestion, departure weather) vs. *Known After Departure* (actual departure time, taxi-out time, air time, airborne weather). Pre-flight predictions use only pre-flight features.
3. **Graceful Fallback & Interface Abstraction**: External dependencies (Flight APIs, Weather APIs, LLM APIs) isolated behind abstract provider interfaces (`FlightProvider`, `WeatherProvider`). The system must function completely offline with mock fallbacks.
4. **Deterministic & Reproducible ML**: Explicit seeds, saved artifacts (`joblib`), time-based train/test splits, and deterministic feature pipelines.
5. **Preservation of Existing Functionality**: The existing 17-step Golden Triangle recovery demo, NetworkX journey graph, and OR-Tools optimization engine remain functional and tested.
6. **No Breaking Changes Between Stages**: The platform will remain buildable (`npm run build`) and testable (`pytest`) at every commit.

---

## 3. Phased Implementation Roadmap

### STAGE 1 — Real Flight Delay Data Pipeline
- **Goal**: Acquire, clean, and engineer a real aviation flight dataset for machine learning.
- **Dataset Selection**: US Bureau of Transportation Statistics (BTS) Airline On-Time Performance dataset or high-quality curated Kaggle flight delay dataset (200,000+ records).
- **Target Definition**: Binary classification:
  $$\text{delayed} = 1 \iff \text{Arrival Delay} \ge 15 \text{ minutes, else } 0$$
- **Leakage Prevention Checklist**:
  - *Included (Pre-flight)*: Carrier, Origin, Destination, Scheduled Departure Hour, Scheduled Elapsed Time, Day of Week, Month, Distance, Historical Origin Delay Rate (rolling window, strictly past data).
  - *Excluded (Post-flight)*: Actual Departure Time, Taxi-Out, Taxi-In, Air Time, Diversion, Cancellation Codes.
- **Deliverables**:
  - `data/README.md`: Documenting source, schema, time period, target definition, license, and preprocessing logic.
  - `backend/app/ml/data_loader.py`: Reproducible extraction, cleaning, and time-sorting pipeline.
  - `backend/app/ml/feature_engineering.py`: Strict pre-flight feature transformations with fitted encoders saved to disk.

---

### STAGE 2 — Weather Feature Integration
- **Goal**: Ingest meteorological parameters into the feature pipeline.
- **Features**: Temperature, precipitation, wind speed, visibility, weather condition, pressure, and severe convective storm indicators.
- **Interface Abstraction**:
  ```python
  class WeatherProvider(ABC):
      @abstractmethod
      def get_weather(self, airport_code: str, timestamp: datetime) -> WeatherObservation:
          pass
  ```
- **Implementations**:
  - `HistoricalWeatherProvider`: Reads local tabular weather data aligned with the training dataset timestamps/stations.
  - `LiveWeatherProvider`: Fetches real-time METAR/open-meteo data for live inference (with caching & timeout protection).
  - `MockWeatherProvider`: Deterministic fallback if API/network is offline.
- **Deliverables**:
  - `backend/app/modules/weather/interfaces.py`
  - `backend/app/modules/weather/providers.py`
  - `backend/app/modules/weather/service.py`

---

### STAGE 3 — Model Training & Time-Based Evaluation
- **Goal**: Train and rigorously compare multiple classifiers using a chronological split.
- **Evaluation Split**:
  - Time-based: e.g., 80% earlier chronologically for training, 20% later chronologically for test/validation.
  - Avoid random K-fold shuffling that causes future-to-past data leakage.
- **Models to Train**:
  1. **Baseline**: Majority-class classifier or Logistic Regression with standardized features.
  2. **Random Forest Classifier**: Non-linear tree ensemble baseline with balanced class weights.
  3. **XGBoost Classifier**: Gradient boosted decision trees optimized for class imbalance (`scale_pos_weight`, early stopping).
- **Evaluation Metrics**:
  - ROC-AUC, PR-AUC (Average Precision), Precision, Recall, F1-Score, Balanced Accuracy, Brier Score / Calibration.
  - Confusion Matrix and class distribution analysis.
- **Deliverables**:
  - `backend/app/ml/train.py`: Reproducible CLI training script.
  - `backend/app/ml/artifacts/`: Serialized model (`best_model.joblib`), pipeline (`preprocessor.joblib`), metadata (`metadata.json`).
  - `reports/model_evaluation.md`: Comparative metrics table with genuine measured values.

---

### STAGE 4 — Model Explainability (SHAP)
- **Goal**: Provide transparent, feature-level attribution for individual flight delay predictions.
- **Implementation**:
  - `TreeExplainer` for XGBoost / Random Forest models.
  - Compute base value (expected delay probability) and SHAP values for top contributing features.
  - Translation into human-readable statements:
    - Example: *Scheduled departure at 18:00 contributed +14% risk due to evening departure bank congestion; Wind speed (28 knots) contributed +9% risk.*
  - Explicit disclaimer: Explainability reflects statistical feature contribution to model score, NOT physical causality.
- **API Response Schema**:
  ```json
  {
    "delay_probability": 0.72,
    "risk_level": "HIGH",
    "prediction": "Likely Delayed (>= 15 mins)",
    "base_probability": 0.21,
    "top_factors": [
      {"feature": "origin_delay_history", "impact": "+0.24", "description": "High departure airport congestion"},
      {"feature": "departure_hour", "impact": "+0.15", "description": "Peak evening departure window (18:00)"},
      {"feature": "wind_speed_knots", "impact": "+0.12", "description": "Adverse crosswinds (28 kts)"}
    ],
    "explanation_type": "SHAP (Kernel/Tree Explainer - Statistical Attribution)"
  }
  ```
- **Deliverables**:
  - `backend/app/ml/explainer.py`
  - Integration into delay prediction service.

---

### STAGE 5 — Upgraded Policy RAG System
- **Goal**: Replace pseudo-vector MD5 hashing with genuine dense vector embeddings and strict hallucination prevention.
- **Architecture**:
  - Document parser & semantic chunker: Maintain existing regulatory coverage (DGCA, EU261, US DOT 14 CFR 260, Air India, IndiGo).
  - Embedding Engine: Use sentence-transformers (e.g. `all-MiniLM-L6-v2`) or Gemini embeddings.
  - Vector Store: FAISS `IndexFlatIP` with normalized vectors.
  - Hybrid Search: Reciprocal Rank Fusion (RRF) combining dense FAISS cosine similarity and BM25 token relevance.
  - Source Attribution: Every answer must cite exact document, section, and page.
  - Refusal Rule: If top retrieval similarity < confidence threshold (e.g. 0.40), return:
    *"I couldn't find sufficient evidence in the available policy documents."*
- **Deliverables**:
  - Refactored `backend/app/modules/policies/policy_rag_service.py`
  - Updated `scripts/ingest_policies.py`

---

### STAGE 6 — Comprehensive RAG Evaluation Benchmark
- **Goal**: Implement a reproducible 30+ question ground-truth benchmark suite.
- **Evaluation Dataset**: `evaluation/rag_questions.json` containing:
  - 30+ diverse questions across: Simple lookup, Eligibility thresholds, Baggage rules, Cancellations, Full refunds, Overnight delays, Multi-hop cascades, Ambiguous queries, Out-of-scope queries.
  - Expected key facts, required document citations, and difficulty tags.
- **Metrics Evaluated**:
  - Retrieval Recall@K (did top-K chunks contain the ground-truth document?)
  - Answer Correctness (semantic overlap with ground-truth facts)
  - Groundedness / Faithfulness (percentage of statements verifiable in context)
  - Citation Accuracy (valid document and section citation)
  - Refusal Rate on out-of-scope questions
- **Deliverables**:
  - `evaluation/rag_questions.json`
  - `scripts/evaluate_rag.py`
  - `reports/rag_evaluation.md`

---

### STAGE 7 — Real Flight Data Provider Abstraction
- **Goal**: Abstract flight status and inventory lookup so live APIs and mock data interchange transparently.
- **Provider Architecture**:
  ```
  FlightProvider (ABC)
       ├── MockFlightProvider (Golden Triangle & simulated routes)
       └── OpenSkyFlightProvider / LiveAviationProvider (Live ADS-B flight status)
  ```
- **Environment Toggle**: `FLIGHT_PROVIDER=mock` vs `FLIGHT_PROVIDER=opensky`
- **Deliverables**:
  - `backend/app/modules/flight_data/interfaces.py`
  - `backend/app/modules/flight_data/mock_provider.py`
  - `backend/app/modules/flight_data/opensky_provider.py`
  - `backend/app/modules/flight_data/factory.py`

---

### STAGE 8 — Unified TripWeave AI Agent
- **Goal**: Implement a multi-tool coordinator that understands conversational intent and invokes only relevant tools.
- **Available Agent Tools**:
  1. `flight_search_tool`: Queries flight inventory and schedules.
  2. `flight_status_tool`: Retrieves real-time status, delays, and departure gates.
  3. `delay_prediction_tool`: Executes ML model + SHAP attribution for scheduled flights.
  4. `weather_tool`: Queries current/forecast weather at origin and destination.
  5. `policy_rag_tool`: Searches statutory rights and airline carriage policies with citations.
- **Dynamic Routing Examples**:
  - *"Will flight 6E-2142 be delayed tomorrow?"* $\to$ Flight Status + Weather + Delay Prediction.
  - *"What are my refund rights if delayed by 5 hours?"* $\to$ Policy RAG Tool.
  - *"My flight from Mumbai to Delhi tomorrow has a high chance of delay. What should I do?"* $\to$ Flight Tool + Weather Tool + Delay Prediction Tool + Policy RAG Tool + Synthesizer.
- **Deliverables**:
  - `backend/app/modules/agent/tripweave_agent.py`
  - `backend/app/modules/agent/tools.py`
  - `backend/app/modules/agent/schemas.py`

---

### STAGE 9 — Evidence-Grounded Structured Response
- **Goal**: Synthesize multi-source agent outputs into an unambiguous, evidence-grounded response.
- **Response Schema**:
  ```json
  {
    "query": "My flight from Mumbai to Delhi tomorrow has a high chance of delay. What should I do?",
    "prediction": {
      "delay_probability": 0.72,
      "risk_level": "HIGH",
      "model": "XGBoost Classifier v1.0",
      "primary_factors": ["Evening congestion at BOM", "Surface winds 26 kts"]
    },
    "current_status": {
      "flight": "AI-202 (BOM -> DEL)",
      "scheduled_departure": "10:00 AM",
      "status": "ON_SCHEDULE (Pre-departure)",
      "provider": "MockFlightProvider (Simulated)"
    },
    "weather": {
      "origin": {"airport": "BOM", "condition": "Overcast", "wind_kts": 24, "visibility_km": 6},
      "destination": {"airport": "DEL", "condition": "Clear", "wind_kts": 8, "visibility_km": 10}
    },
    "policy_entitlements": {
      "governing_regulation": "DGCA CAR Section 3 Series M Part IV",
      "provisions": [
        "Delays >= 2 hours: Free meals and refreshments",
        "Delays >= 5 hours: Right to full 100% refund without cancellation fee",
        "Overnight delays: Free hotel accommodation with airport transfers"
      ],
      "citations": [
        {"document": "DGCA CAR Section 3 Series M Part IV", "section": "Section 3.2", "page": 2}
      ]
    },
    "recommended_actions": [
      "Monitor flight status 3 hours prior to departure",
      "Request complimentary refreshments at departure gate if delay exceeds 2 hours",
      "Review alternate flights departing BOM before peak congestion"
    ],
    "disclaimer": "Predictions reflect statistical probabilities and do not guarantee flight delays. Statutory rights are governed by applicable civil aviation authorities."
  }
  ```

---

### STAGE 10 — Clean REST & WebSocket API Design
- **Goal**: Organize backend routers with strict validation, schema typing, error handling, and timeouts.
- **Endpoints**:
  - `POST /api/v1/predict/delay`: ML flight delay probability and SHAP attribution.
  - `GET  /api/v1/weather/{airport_code}`: Airport weather observations.
  - `GET  /api/v1/flights/search` & `GET /api/v1/flights/status/{flight_id}`: Real/mock flight data.
  - `POST /api/v1/policies/ask`: Upgraded policy RAG with citations.
  - `POST /api/v1/agent/chat`: Unified TripWeave Agent query coordination.
  - Maintain backward compatibility for `/api/chat` and `/api/v1/recovery/*`.
- **Deliverables**:
  - `backend/app/api/v1/endpoints/prediction.py`
  - `backend/app/api/v1/endpoints/weather.py`
  - `backend/app/api/v1/endpoints/agent.py`

---

### STAGE 11 — Frontend Enhancement (TripWeave Intelligence Console)
- **Goal**: Elevate the UI into a flight intelligence console.
- **Features**:
  1. **Flight Search & Status Banner**: View real or simulated flight schedules and live operational status.
  2. **Delay Probability & Risk Gauge**: Visual circular gauge displaying risk level (Low, Moderate, High) with calibrated probability percentage.
  3. **SHAP Factor Breakdown Card**: Waterfall / bar chart showing top positive and negative contributing features.
  4. **Weather Widget**: Origin and destination meteorological conditions with severity badges.
  5. **Agent Chat Console**: Conversational interface with tool execution pill badges (e.g. *[Tool: Weather]*, *[Tool: ML Predictor]*), expandable citation source cards, and action buttons.
  6. **Resilience & State Handling**: Clear loading skeletons, error toasts, and fallback banners.
- **Deliverables**:
  - Upgraded `frontend/src/components/DashboardShell.jsx`
  - New `frontend/src/components/TripWeaveAgentConsole.jsx`
  - New `frontend/src/components/DelayPredictionView.jsx`

---

### STAGE 12 — Automated Test Suite
- **Goal**: Add unit and integration tests across ML, RAG, and Agent layers.
- **Unit Tests**:
  - Preprocessing pipeline (missing value handling, encoding consistency, scaler fit).
  - Pre-flight feature isolation (ensuring post-departure columns are excluded).
  - Prediction engine & SHAP output schema validation.
  - Weather and Flight provider interfaces and fallback behavior.
  - RAG document chunking, BM25 indexing, and vector similarity calculation.
- **Integration Tests**:
  - End-to-end delay prediction API endpoint (`/api/v1/predict/delay`).
  - End-to-end policy RAG API endpoint (`/api/v1/policies/ask`).
  - Multi-tool Agent execution and tool selection validation.
  - Provider failure resilience (app does not crash when weather API or LLM fails).
- **Deliverables**:
  - `tests/ml/test_preprocessing.py`
  - `tests/ml/test_prediction.py`
  - `tests/rag/test_rag_pipeline.py`
  - `tests/agent/test_tripweave_agent.py`
  - `pytest.ini` ensuring automatic `PYTHONPATH` resolution.

---

### STAGE 13 — Production Documentation (README.md Rewrite)
- **Goal**: Rewrite the root README to present TripWeave AI as a portfolio-standard AI/ML engineering platform.
- **Positioning**: *"TripWeave AI is an agentic flight intelligence platform that combines flight-delay prediction, weather information, live flight data, and policy-aware RAG to help travelers make better decisions."*
- **Sections**: Overview, Architecture Diagram, Agentic Multi-Tool Workflow, ML Pipeline & Feature Engineering, Time-Based Model Evaluation, RAG Ingestion & Evaluation Benchmark, Flight & Weather Providers (Real vs. Mock), Tech Stack, API Specification, Local Setup & Docker, Limitations & Disclaimers.
- **Deliverables**:
  - Completely rewritten `README.md`

---

### STAGE 14 — Architecture & Design Decisions
- **Goal**: Document the technical rationale behind key engineering decisions.
- **Key Decisions to Document**:
  - Why chronological / time-based data splits instead of random k-fold shuffling?
  - Why Random Forest vs. XGBoost vs. Logistic Regression?
  - Why SHAP for explainability, and why distinguish statistical attribution from physical causality?
  - Why hybrid BM25 + dense FAISS search for regulatory policy documents?
  - Why abstract external dependencies behind Provider interfaces (`FlightProvider`, `WeatherProvider`)?
  - How data leakage is prevented across the machine learning lifecycle.
- **Deliverables**:
  - `docs/DESIGN_DECISIONS.md`

---

### STAGE 15 — Security, Secrets & Environment Hardening
- **Goal**: Eliminate hardcoded credentials and secure runtime configurations.
- **Audit Actions**:
  - Remove all default fallback JWT secret strings from code.
  - Ensure `.env` is excluded in `.gitignore`.
  - Provide a complete `.env.example` with clear comments for every variable.
  - Constrain CORS to explicit dev origins (`http://localhost:5173`, etc.).
  - Add input sanitization and Pydantic validation across all newly created endpoints.
- **Deliverables**:
  - Updated `.env.example`
  - Cleaned `backend/app/core/config.py`

---

### STAGE 16 — GitHub Repository Quality & Recommended Commits
- **Goal**: Prepare clean git history and repository metadata for portfolio presentation.
- **Cleanups**:
  - Remove unused boilerplate (`frontend/src/main.ts`, `frontend/src/counter.ts`, `frontend/src/style.css`, `backend/app/modules/ai_agents/agent_stub.py`).
  - Consolidate duplicate databases and datasets.
- **Recommended Git Commit Sequence**:
  1. `chore(audit): complete stage 0 repository audit and architecture documentation`
  2. `feat(data): add real flight delay dataset and preprocessing pipeline`
  3. `feat(weather): implement WeatherProvider abstraction and meteorological features`
  4. `feat(ml): train and evaluate baseline, random forest, and xgboost models`
  5. `feat(explainability): integrate SHAP feature attribution for delay predictions`
  6. `feat(rag): upgrade policy RAG to dense embeddings and add 30-question benchmark`
  7. `feat(flights): implement FlightProvider abstraction with mock and real providers`
  8. `feat(agent): implement unified TripWeave AI agent with tool orchestration`
  9. `feat(api): add clean typed endpoints for prediction, weather, policies, and agent`
  10. `feat(frontend): add TripWeave intelligence console, risk gauge, and agent chat`
  11. `test: add comprehensive test suite for ML, RAG, providers, and agent`
  12. `docs: rewrite production README and design decisions documentation`
  13. `chore: security hardening, secrets cleanup, and environment configuration`

---

## 4. Current Status & Next Action

- **Stage 0 (Repository Audit)**: **COMPLETED**
- **Artifacts Created**:
  - `docs/CURRENT_ARCHITECTURE.md`
  - `docs/UPGRADE_PLAN.md`
  - Git branch `dev` pushed to `origin/dev`.
- **Checkpoint**: Execution is stopped as required. Awaiting explicit user approval before proceeding to Stage 1.
