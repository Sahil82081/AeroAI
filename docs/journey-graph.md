# Journey Graph Engine (`docs/journey-graph.md`)

## 1. Overview

Implemented in `backend/app/modules/journeys/graph_builder.py`, the **Journey Graph Engine** uses **NetworkX (`nx.DiGraph`)** to transform individual, disconnected travel bookings into a connected, time-aware directed acyclic graph (DAG).

### Canonical Example: Golden Triangle Journey

```
Flight AI-202 (Mumbai → Delhi, 10:00 → 12:00)
  ↓  [Connection Edge: 90m layover in Delhi — SAFE]
Train 12015-SHT (Delhi → Jaipur, 13:30 → 17:30)
  ↓  [Transfer Edge: 30m station-to-hotel transfer in Jaipur — SAFE]
Hotel HTL-JAI-101 (Jaipur Check-in 18:00)
  ↓  [Chronological Edge: Overnight stay until 09:00 next day — SAFE]
Tour TOUR-JAI-01 (Jaipur Amber Fort Tour, Next Day 09:00 → 13:00)
```

---

## 2. Graph Nodes & Edges

### Node Types
- `FLIGHT`: Commercial air segments with origin airport, destination airport, departure, and arrival timestamps.
- `TRAIN`: Intercity rail segments with origin station, destination station, departure, and arrival timestamps.
- `BUS`: Intercity coach segments.
- `HOTEL`: Accommodation check-in and check-out windows.
- `ACTIVITY`: Guided tours and scheduled destination activities.
- `LOCATION`: Physical transit hubs (airports, railway stations, city centers) linking consecutive bookings.

### Edge Types
- `CONNECTION`: Transit connection between two consecutive transport modes (e.g., Flight arrival at Delhi → Train departure from Delhi).
- `TRANSFER`: Arrival at destination transit hub → Hotel check-in or activity start.
- `DEPENDENCY`: Downstream causal dependency indicating that a delay in node $u$ propagates to node $v$.
- `CHRONOLOGICAL`: Sequential ordering across multi-day itinerary items.

---

## 3. Connection Risk Classification Rules

For every consecutive pair of bookings $(u, v)$, the engine calculates:
$$\text{Available Time Gap (minutes)} = \frac{t_{\text{start}}(v) - t_{\text{end}}(u)}{60}$$

| Connection Type | Minimum Required Buffer | Tight Threshold | Classification Criteria |
| :--- | :---: | :---: | :--- |
| **Flight → Flight / Train** | `60 min` | `90 min` | `< 0m` or `< 45m`: `IMPOSSIBLE` (`HIGH_RISK`)<br>`45m – 89m`: `TIGHT` (`AT_RISK`)<br>`≥ 90m`: `SAFE` |
| **Train / Bus → Hotel** | `15 min` | `30 min` | `< 0m` (or after hotel cutoff): `IMPOSSIBLE`<br>`0m – 29m`: `TIGHT`<br>`≥ 30m`: `SAFE` |
| **Location Mismatch** | N/A | N/A | If $\text{destination}(u) \neq \text{origin}(v)$: `IMPOSSIBLE` (`LOCATION_MISMATCH`) |

---

## 4. Persistence & API Endpoints

- **Database Sync**: `JourneyGraphEngine.sync_to_database(db, journey)` persists computed `ConnectionEdge` records and serialized graph JSON into SQLite/PostgreSQL.
- **REST Endpoints**:
  - `GET /api/v1/journeys/{journey_id}/graph`: Builds and returns the full NetworkX node/edge topology, connection risk classifications, and summary counters (`safe_connections`, `tight_connections`, `impossible_connections`, `overall_status`).
