# Recovery Optimization Using Google OR-Tools (`docs/optimization.md`)

## 1. Problem Formulation

Implemented in `backend/app/modules/optimization/ortools_optimizer.py`, the **Recovery Optimization Engine** uses **Google OR-Tools CP-SAT (`ortools.sat.python.cp_model`)** to select the mathematically optimal recovery transport option after a travel disruption.

### Canonical Scenario
After Flight `AI-202` (Mumbai → Delhi) is delayed by 4 hours (`10:00 → 16:00`), the traveler misses Train `12015-SHT` (`13:30`). Several candidate replacements exist from Delhi to Jaipur while the Jaipur hotel (`HTL-JAI-101`) enforces a **latest check-in cutoff of 10:00 PM (`22:00`)**:

| Candidate ID | Mode | Departure | Arrival | Price (₹) | Seats | Feasibility vs. Constraints |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `TRN123` (Shatabdi) | Train | `13:30` | `17:30` | ₹800 | 15 | **Infeasible**: Departs before `16:00` flight arrival (`-150m` gap) |
| `TRN124` (Ashram Exp) | Train | `17:30` | `21:00` | ₹700 | 22 | **Feasible & Optimal**: `90m` buffer after `16:00`, arrives `60m` before `22:00` hotel cutoff |
| `TRN125` (Double Decker) | Train | `18:00` | `21:45` | ₹650 | 8 | **Feasible (Rank #2)**: Longer wait (`120m`) and tighter arrival (`21:45`) |
| `TRN126` (Night Mail) | Train | `19:00` | `22:30` | ₹400 | 34 | **Infeasible**: Arrives at `22:30`, violating the `22:00` hotel latest check-in cutoff |
| `BUS123` (RSRTC Volvo) | Bus | `17:00` | `21:45` | ₹950 | 12 | **Feasible (Rank #3)**: Higher price (₹950) and longer travel duration (`285m`) |

---

## 2. Hard Constraints (CP-SAT Feasibility Filtering & Linear Constraints)

For each candidate option $i \in \{1, \dots, N\}$, a binary decision variable $x_i \in \{0, 1\}$ is created in `CpModel`:

1. **Exact Single Selection Constraint**:
   $$\sum_{i \in \mathcal{F}} x_i = 1$$
2. **Minimum Connection Buffer Constraint**:
   $$\text{departure}(i) \ge \text{current\_arrival} + \text{min\_connection\_minutes}$$
3. **Hotel Latest Check-In Cutoff Constraint**:
   $$\text{arrival}(i) \le \text{hotel\_latest\_checkin}$$
4. **Seat Availability Constraint**:
   $$\text{available\_seats}(i) \ge \text{required\_seats}$$
5. **Budget & Mode Preferences**:
   $$\text{price}(i) \le \text{max\_budget}, \quad \text{type}(i) \notin \text{avoid\_modes}$$

---

## 3. Multi-Objective Cost Function

Each feasible candidate $i$ is scored across 6 normalized dimensions $\in [0, 1]$ weighted by configurable user preferences $(w_1, \dots, w_6)$:

$$\text{Objective}(i) = w_{\text{price}} \cdot \hat{P}_i + w_{\text{travel}} \cdot \hat{T}_i + w_{\text{wait}} \cdot \hat{W}_i + w_{\text{changes}} \cdot \hat{C}_i + w_{\text{arrival}} \cdot \hat{A}_i + w_{\text{reliability}} \cdot (1 - R_i)$$

Where:
- $\hat{P}_i$: Normalized ticket price
- $\hat{T}_i$: Normalized travel duration
- $\hat{W}_i$: Normalized waiting time at origin hub
- $\hat{C}_i$: Normalized number of transfers/changes
- $\hat{A}_i$: Normalized arrival lateness relative to hotel cutoff
- $R_i \in [0, 1]$: Historical supplier reliability score

The CP-SAT solver minimizes the integer-scaled objective $\sum_{i \in \mathcal{F}} \text{round}(10000 \cdot \text{Objective}(i)) \cdot x_i$ and returns the optimal option (`selected_option`), ranked `alternatives`, `objective_score`, and human-readable `explanation`.
