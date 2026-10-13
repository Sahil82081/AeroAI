# Mock Supplier API Ecosystem & Adapter Layer (`docs/supplier-api.md`)

> [!IMPORTANT]
> **SIMULATED SUBSYSTEM DISCLAIMER**: All supplier endpoints (`/flights/*`, `/trains/*`, `/buses/*`, `/hotels/*`, `/bookings/*`, `/hotel/*`) are **MOCK APIs** built for realistic testing and demonstration. Every response includes `"is_mock_api": true` and `"simulated": true`.

## 1. Decoupled Adapter Architecture

Agents **never** call supplier HTTP endpoints or datasets directly. All interactions flow through the decoupled adapter hierarchy in `backend/app/modules/suppliers/`:

```
Autonomous Agent / Action Executor
        ↓
SupplierIntegrationService (backend/app/modules/suppliers/service.py)
        ↓
BaseSupplierAdapter (backend/app/modules/suppliers/adapters.py)
  ├── FlightSupplierAdapter
  ├── TrainSupplierAdapter
  ├── BusSupplierAdapter
  └── HotelSupplierAdapter
        ↓
Mock Supplier Ecosystem (backend/app/modules/suppliers/mock_datasets.py)
```

---

## 2. REST API Endpoints

### Discovery & Search Endpoints
- `GET /flights/search?origin=Mumbai&destination=Delhi`
- `GET /trains/search?origin=Delhi&destination=Jaipur`
- `GET /buses/search?origin=Delhi&destination=Jaipur`
- `GET /hotels/search?city=Jaipur`

### Transactional Booking & Modification Endpoints
- `POST /bookings/rebook`: Reserves seats on a replacement flight, train, or bus, decrements live seat inventory, and issues a confirmation reference (`PNR-*`).
- `POST /bookings/cancel`: Cancels an existing booking, restores seat inventory, and computes cancellation penalties based on supplier fare rules.
- `POST /bookings/refund`: Evaluates refund eligibility (`FULL_REFUND`, `PARTIAL_REFUND`, `NON_REFUNDABLE`) and issues a simulated refund transaction ID (`RFND-*`).
- `POST /hotel/modify`: Updates hotel check-in arrival time and enforces property latest check-in cutoff policies (e.g., `22:00` at Rambagh Heritage Palace Jaipur).

---

## 3. Realistic Indian Golden Triangle Datasets

### Train Supplier (`TRAINS_DB`)
| `transport_id` | Service Name | Origin → Destination | Departure → Arrival | Price (₹) | Available Seats | Refund Policy |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `TRN123` | Ajmer Shatabdi 12015 | Delhi → Jaipur | `13:30 → 17:30` | ₹800 | 15 | 75% refundable |
| `TRN124` | Ashram Express 12916 | Delhi → Jaipur | `17:30 → 21:00` | ₹700 | 22 | 80% refundable |
| `TRN125` | Double Decker 12986 | Delhi → Jaipur | `18:00 → 21:45` | ₹650 | 8 | 75% refundable |
| `TRN126` | Chetak Express 20473 | Delhi → Jaipur | `19:00 → 22:30` | ₹400 | 34 | Non-refundable |

### Fault Injection & Latency Simulation
Every transactional endpoint supports optional fault-injection parameters for resilience testing:
- `simulate_latency_ms`: Injects artificial network delay (`0 – 5000ms`) to test timeout budgets.
- `simulate_failure`: Injects deterministic supplier faults (`timeout`, `service_unavailable`, `no_availability`, `payment_declined`, `policy_violation`).
