# End-to-End Golden Triangle Demo Scenario (`docs/demo-scenario.md`)

## 1. Scenario Specification

A traveler (**Aarav Sharma**) books a 4-leg Indian Golden Triangle itinerary:

1. **Flight (`AI-202`)**: Mumbai → Delhi, `10:00 AM → 12:00 PM` (`₹5,400`)
2. **Train (`12015-SHT` / `TRN123`)**: Delhi → Jaipur, `1:30 PM → 5:30 PM` (`₹800`)
3. **Hotel (`HTL-JAI-101`)**: Rambagh Heritage Palace Jaipur, Check-in `6:00 PM` (Latest check-in cutoff `10:00 PM`)
4. **Tour (`TOUR-JAI-01`)**: Amber Fort & Pink City Guided Tour, Next day `9:00 AM → 1:00 PM`

### Triggered Disruption
- **Flight `AI-202` delayed by 4 hours (`240 minutes`)** → Revised Delhi arrival: **`4:00 PM (16:00)`**.

---

## 2. Step-by-Step Verification Checklist (17 Steps)

You can execute and verify all 17 steps with a single API call (`POST /api/v1/recovery/demo/golden-triangle`) or via the **Executive Dashboard** in the frontend UI:

| Step | Expected Behavior | Subsystem Involved | Real vs. Simulated |
| :---: | :--- | :--- | :---: |
| **1** | **Disruption detected**: Flight `AI-202` marked `DELAYED` (`+240m`, arrival `16:00`), severity `CRITICAL`. | `DisruptionSimulatorEngine` | **REAL** |
| **2** | **Kafka event generated**: `booking.updated` and `disruption.detected` published with correlation ID. | `KafkaEventBroker` | **REAL** |
| **3** | **Journey recalculated**: NetworkX graph recomputes Delhi Flight→Train edge gap from `+90m` (`SAFE`) to `-150m` (`IMPOSSIBLE`). | `JourneyGraphEngine` | **REAL** |
| **4** | **Train identified as missed**: `12015-SHT` (`13:30` departure) flagged as `MISSED_CONNECTION`. | `ImpactAnalysisAgent` | **REAL** |
| **5** | **Hotel identified as potentially affected**: `HTL-JAI-101` (`18:00` check-in) flagged as `SCHEDULE_THREATENED`. | `ImpactAnalysisAgent` | **REAL** |
| **6** | **Tour identified as unaffected**: Next-day `09:00 AM` `TOUR-JAI-01` preserved in `unaffected_bookings`. | `ImpactAnalysisAgent` | **REAL** |
| **7** | **Alternative trains searched**: Decoupled `TrainSupplierAdapter` & `BusSupplierAdapter` query candidate replacements. | `SupplierIntegrationService` | **SIMULATED** |
| **8** | **OR-Tools selects best feasible alternative**: CP-SAT solver prunes `TRN126` (`22:30` > `22:00` hotel cutoff) and selects **`TRN124` (`17:30 → 21:00`, ₹700)**. | `ORToolsRecoveryOptimizer` | **REAL** |
| **9** | **Recovery plan generated**: 8-node LangGraph workflow validates confidence (`0.94`) and approves autonomous execution. | `LangGraph StateGraph` | **REAL** |
| **10** | **User informed**: 6 fact-grounded notifications generated and validated with zero hallucinations. | `NotificationAgentService` | **REAL** |
| **11** | **Mock train booking cancelled**: `12015-SHT` cancelled via `TrainSupplierAdapter`. | `RecoveryActionExecutor` | **SIMULATED** |
| **12** | **Alternative train booked**: `TRN124` (`17:30 → 21:00`) booked with idempotency protection. | `RecoveryActionExecutor` | **SIMULATED** |
| **13** | **Refund request created**: Eligible refund (`₹600`) requested for `12015-SHT`. | `RecoveryActionExecutor` | **SIMULATED** |
| **14** | **Hotel arrival updated**: `HTL-JAI-101` check-in updated from `18:00` to `21:30` (within `22:00` cutoff). | `RecoveryActionExecutor` | **SIMULATED** |
| **15** | **Tour remains unchanged**: `TOUR-JAI-01` remains `CONFIRMED` for next day `09:00 AM`. | Database & Graph Engine | **REAL** |
| **16** | **Final journey graph updated**: All connections restored to `SAFE` (`0` impossible connections). | `JourneyGraphEngine` | **REAL** |
| **17** | **Complete audit trail displayed**: Structured audit records stored in `IdempotencyAndAuditStore`. | `IdempotencyAndAuditStore` | **REAL** |
