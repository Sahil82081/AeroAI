# System Architecture (`docs/architecture.md`)

## 1. High-Level System Overview

The **Autonomous Disruption Recovery Agent** is an event-driven, multi-agent travel intelligence platform that transforms disconnected travel bookings into a connected **NetworkX Directed Acyclic Journey Graph**, detects downstream cascading disruptions in real time, computes mathematically optimal recovery plans using **Google OR-Tools CP-SAT**, orchestrates autonomous decision-making via an **8-node LangGraph workflow**, executes idempotent supplier actions across a decoupled **Adapter Layer**, and streams live recovery milestones over **Apache Kafka & WebSockets**.

```mermaid
flowchart TD
    subgraph Frontend["React 18 + Vite + Tailwind SaaS Dashboard (11 Views)"]
        UI_Dash["Executive Dashboard & Disruption Center"]
        UI_Graph["Interactive Journey Graph & Details"]
        UI_Rec["OR-Tools & LangGraph Recovery Plan"]
        UI_Audit["Action History, Kafka Stream & Notification Inbox"]
    end

    subgraph API["FastAPI REST & WebSocket Gateway (/api/v1)"]
        Auth["JWT Authentication & RBAC"]
        Ingest["Email Ingestion & LLM/Regex Parser"]
        GraphAPI["NetworkX Journey Graph Service"]
        DisruptAPI["Disruption Simulator & Impact Engine"]
        OptAPI["Google OR-Tools CP-SAT Optimizer"]
        LangGraphAPI["8-Node LangGraph Recovery Agent"]
        ExecAPI["Idempotent Action Executor & Audit Store"]
        NotifAPI["Fact-Grounded Notification Agent"]
    end

    subgraph EventBus["Apache Kafka Event-Driven Backbone (KRaft)"]
        Topics["10 Domain Topics + Dead-Letter Queue (recovery.dlq)"]
        CG1["impact-agent-group"]
        CG2["recovery-agent-group"]
        CG3["action-agent-group"]
        CG4["notification-agent-group"]
    end

    subgraph Adapters["Decoupled Supplier Integration Layer"]
        BaseAdapter["BaseSupplierAdapter (Retry, Latency, Fault Injection)"]
        FlightAdapter["FlightSupplierAdapter"]
        TrainAdapter["TrainSupplierAdapter"]
        BusAdapter["BusSupplierAdapter"]
        HotelAdapter["HotelSupplierAdapter"]
    end

    subgraph MockSuppliers["Mock Supplier Ecosystem (SIMULATED)"]
        MockFlight["Mock Airline API (/flights)"]
        MockTrain["Mock Railway API (/trains)"]
        MockBus["Mock Bus API (/buses)"]
        MockHotel["Mock Hotel API (/hotels)"]
    end

    Frontend <-->|"REST + WebSocket (/api/v1/events/ws)"| API
    DisruptAPI --> Topics
    Topics --> CG1 & CG2 & CG3 & CG4
    ExecAPI --> BaseAdapter
    BaseAdapter --> FlightAdapter & TrainAdapter & BusAdapter & HotelAdapter
    FlightAdapter --> MockFlight
    TrainAdapter --> MockTrain
    BusAdapter --> MockBus
    HotelAdapter --> MockHotel
```

---

## 2. Explicit Distinction: REAL vs. SIMULATED Subsystems

To maintain architectural clarity, the platform explicitly separates **REAL** algorithmic, graph, optimization, and agentic subsystems from **SIMULATED** third-party travel supplier integrations:

| Subsystem | Classification | Implementation Details |
| :--- | :---: | :--- |
| **Email Parsing & Booking Extraction** | **REAL** | Hybrid Gemini Structured Output + deterministic regex parser (`EmailParserService`) |
| **Journey Graph & Risk Engine** | **REAL** | `networkx.DiGraph` modeling chronological, transfer, and connection edges (`SAFE`, `TIGHT`, `IMPOSSIBLE`) |
| **Disruption Cascade & Impact Analysis** | **REAL** | Graph traversal computing revised arrival times, buffer erosion, and natural-language explanations |
| **Mathematical Recovery Optimization** | **REAL** | Google OR-Tools `cp_model.CpModel` & `CpSolver` with hard constraints and configurable 6-weight objective |
| **Autonomous 8-Node Agent Workflow** | **REAL** | LangGraph `StateGraph` with confidence scoring, validation gates, and human approval escalation |
| **Kafka Event Backbone & WebSockets** | **REAL** | 10 domain topics + `recovery.dlq`, correlation IDs, idempotent consumers, retries, and live WebSocket push |
| **Anti-Hallucination Notification Validator** | **REAL** | `FactGroundingValidator` verifying zero invented booking refs, prices, dates/times, or policy numbers |
| **Idempotency & Compensating Rollback** | **REAL** | Deterministic SHA-256 idempotency keys, timeout budgets, retries, and compensating state reinstatement |
| **Airline / Train / Bus / Hotel APIs** | **SIMULATED** | In-process FastAPI Mock Supplier Ecosystem with realistic Indian Golden Triangle datasets & fault injection |
| **Email Delivery Inbox** | **SIMULATED** | Simulated SMTP/Inbox store exposing generated messages, validation badges, and metadata in the UI |

---

## 3. Core Backend Modules (`backend/app/modules/`)

- `auth/`: JWT token generation, password hashing, and user session management.
- `ingestion/`: Raw travel confirmation email ingestion, classification, and structured booking creation.
- `journeys/`: NetworkX `JourneyGraphEngine` constructing nodes (`FLIGHT`, `TRAIN`, `BUS`, `HOTEL`, `ACTIVITY`, `LOCATION`) and edges (`CONNECTION`, `TRANSFER`, `CHRONOLOGICAL`, `DEPENDENCY`).
- `disruptions/`: `DisruptionSimulatorEngine` and `ImpactAnalysisAgent` propagating delays/cancellations across downstream graph edges.
- `suppliers/`: Mock supplier datasets (`FLIGHTS_DB`, `TRAINS_DB`, `BUSES_DB`, `HOTELS_DB`), REST endpoints, and decoupled `FlightSupplierAdapter`, `TrainSupplierAdapter`, `BusSupplierAdapter`, and `HotelSupplierAdapter`.
- `optimization/`: `ORToolsRecoveryOptimizer` formulating 0-1 integer linear programs solved via Google OR-Tools CP-SAT.
- `ai_agents/`: 8-node LangGraph `StateGraph` (`DisruptionAnalysisNode` → `JourneyImpactNode` → `AlternativeSearchNode` → `ConstraintOptimizationNode` → `RecoveryDecisionNode` → `ActionExecutionNode` → `VerificationNode` → `NotificationNode`).
- `recovery/`: `RecoveryActionExecutor` and `IdempotencyAndAuditStore` executing 6 action types with retries, timeouts, partial recovery, and compensating rollback.
- `events/`: `KafkaEventBroker`, `EventDrivenRecoveryPipeline`, and `WebSocketConnectionManager`.
- `notifications/`: `NotificationAgentService` and `FactGroundingValidator` generating 6 stakeholder communications.
- `demo/`: `EndToEndDemoOrchestrator` running and verifying the 17-step Golden Triangle scenario.
