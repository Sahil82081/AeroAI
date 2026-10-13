"""
Google OR-Tools CP-SAT Recovery Optimization Engine.
Performs mathematical constraint programming and multi-objective optimization
to select the optimal travel recovery alternative after a disruption.

IMPORTANT:
All constraint satisfaction and objective minimization is performed mathematically
by Google OR-Tools (ortools.sat.python.cp_model), NOT by an LLM.
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from ortools.sat.python import cp_model

from app.schemas.optimization_schemas import (
    OptimizationRequest,
    OptimizationResponse,
    CandidateAlternativeInput,
    OptimizationConstraints,
    TravelerPreferences
)
from app.modules.suppliers.service import supplier_service


def parse_time_to_minutes(time_str: str, reference_date: Optional[datetime] = None) -> Tuple[int, Optional[datetime]]:
    """
    Parses ISO-8601 ('2026-10-20T17:30:00'), 24h ('17:30'), or 12h ('5:30 PM')
    time strings into integer minutes for OR-Tools CP-SAT linear constraints.
    """
    s = time_str.strip()

    # 1. Try ISO-8601 datetime
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        ref = reference_date or datetime(dt.year, dt.month, dt.day, 0, 0, 0)
        delta_minutes = int(round((dt.replace(tzinfo=None) - ref.replace(tzinfo=None)).total_seconds() / 60.0))
        return delta_minutes, dt.replace(tzinfo=None)
    except ValueError:
        pass

    # 2. Try 12-hour AM/PM format (e.g. "5:00 PM", "10:30 PM", "12:15 AM")
    am_pm_match = re.match(r"^(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)$", s)
    if am_pm_match:
        hour = int(am_pm_match.group(1))
        minute = int(am_pm_match.group(2))
        meridiem = am_pm_match.group(3).upper()
        if meridiem == "PM" and hour != 12:
            hour += 12
        elif meridiem == "AM" and hour == 12:
            hour = 0
        return hour * 60 + minute, reference_date

    # 3. Try 24-hour HH:MM or HH:MM:SS format
    hm_match = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2})?$", s)
    if hm_match:
        hour = int(hm_match.group(1))
        minute = int(hm_match.group(2))
        return hour * 60 + minute, reference_date

    raise ValueError(f"Unsupported time format for OR-Tools optimizer: '{time_str}'")


def format_minutes_as_clock(total_minutes: int) -> str:
    """Formats minutes from midnight into HH:MM (and +1d if overnight)."""
    day_offset = total_minutes // 1440
    rem = total_minutes % 1440
    hh = rem // 60
    mm = rem % 60
    suffix = f" (+{day_offset}d)" if day_offset > 0 else ""
    return f"{hh:02d}:{mm:02d}{suffix}"


class ORToolsRecoveryOptimizer:
    """
    Mathematical Recovery Optimizer powered by Google OR-Tools CP-SAT Solver.
    Formulates recovery selection as a Constrained Integer Linear Program (0-1 IP).
    """

    DEFAULT_RELIABILITY_BY_MODE = {
        "train": 0.94,
        "flight": 0.89,
        "bus": 0.85
    }

    def optimize(self, request: OptimizationRequest) -> OptimizationResponse:
        # 1. Gather candidate alternatives (either provided directly or fetched from Mock Suppliers)
        candidates: List[CandidateAlternativeInput] = list(request.available_alternatives or [])
        if not candidates and request.auto_fetch_from_suppliers:
            multimodal = supplier_service.search_multimodal_alternatives(
                origin=request.origin,
                destination=request.destination,
                min_seats=1
            )
            for item in multimodal.get("alternatives", []):
                mode = item.get("supplier_type", "train").lower()
                candidates.append(
                    CandidateAlternativeInput(
                        transport_id=item["transport_id"],
                        name=f"{item['provider']} ({item.get('vehicle_number', item['transport_id'])})",
                        supplier_type=mode,
                        provider=item["provider"],
                        vehicle_number=item.get("vehicle_number", item["transport_id"]),
                        origin=item["origin"],
                        destination=item["destination"],
                        departure=item["departure"],
                        arrival=item["arrival"],
                        price=float(item["price"]),
                        currency=item.get("currency", "INR"),
                        available_seats=int(item.get("available_seats", 10)),
                        number_of_changes=0,
                        reliability=self.DEFAULT_RELIABILITY_BY_MODE.get(mode, 0.90),
                        duration_minutes=item.get("duration_minutes")
                    )
                )

        if not candidates:
            return OptimizationResponse(
                selected_option=None,
                alternatives=[],
                objective_score=0.0,
                constraints_satisfied=False,
                explanation="No candidate recovery alternatives were provided or found for optimization.",
                solver_metadata={"solver": "Google OR-Tools CP-SAT", "status": "NO_CANDIDATES"}
            )

        constraints: OptimizationConstraints = request.constraints
        prefs: TravelerPreferences = request.traveler_preferences
        weights = prefs.weights

        # Establish reference date if ISO timestamps are used
        ref_date: Optional[datetime] = None
        for c in candidates:
            try:
                _, dt = parse_time_to_minutes(c.departure)
                if dt is not None:
                    ref_date = datetime(dt.year, dt.month, dt.day, 0, 0, 0)
                    break
            except ValueError:
                pass

        current_arr_min, _ = parse_time_to_minutes(constraints.current_arrival, ref_date)
        hotel_checkin_min: Optional[int] = None
        if constraints.hotel_latest_checkin:
            hotel_checkin_min, _ = parse_time_to_minutes(constraints.hotel_latest_checkin, ref_date)

        # 2. Pre-process candidate metrics & evaluate individual constraint diagnostics
        parsed_candidates: List[Dict[str, Any]] = []
        for idx, cand in enumerate(candidates):
            dep_min, _ = parse_time_to_minutes(cand.departure, ref_date)
            arr_min, _ = parse_time_to_minutes(cand.arrival, ref_date)
            # Handle overnight arrival in clock-only format (e.g. dep 22:00, arr 01:30)
            if arr_min < dep_min:
                arr_min += 1440

            travel_min = cand.duration_minutes if cand.duration_minutes is not None else max(1, arr_min - dep_min)
            wait_min = dep_min - current_arr_min

            # Evaluate the 5 core constraints for diagnostics and CP-SAT domain pruning
            c_dep_after_arr = dep_min >= current_arr_min
            c_conn_feasible = (wait_min >= constraints.min_connection_minutes) and (
                constraints.max_waiting_minutes is None or wait_min <= constraints.max_waiting_minutes
            )
            c_before_hotel = True if hotel_checkin_min is None else (arr_min <= hotel_checkin_min)
            c_has_seats = cand.available_seats >= constraints.required_seats

            # Passenger preferences check
            pref_violations: List[str] = []
            if prefs.max_budget is not None and cand.price > prefs.max_budget:
                pref_violations.append(f"Price {cand.price} exceeds max budget {prefs.max_budget}")
            if prefs.allowed_modes is not None:
                allowed_lower = [m.lower() for m in prefs.allowed_modes]
                if cand.supplier_type.lower() not in allowed_lower:
                    pref_violations.append(f"Mode '{cand.supplier_type}' not in allowed modes {prefs.allowed_modes}")
            if prefs.excluded_modes:
                excluded_lower = [m.lower() for m in prefs.excluded_modes]
                if cand.supplier_type.lower() in excluded_lower:
                    pref_violations.append(f"Mode '{cand.supplier_type}' is excluded by passenger preference")
            if prefs.max_changes is not None and cand.number_of_changes > prefs.max_changes:
                pref_violations.append(f"Changes ({cand.number_of_changes}) exceed max_changes ({prefs.max_changes})")
            if prefs.min_reliability is not None and cand.reliability < prefs.min_reliability:
                pref_violations.append(f"Reliability ({cand.reliability}) below min_reliability ({prefs.min_reliability})")

            c_prefs_ok = len(pref_violations) == 0

            violations: List[str] = []
            if not c_dep_after_arr:
                violations.append(
                    f"Departure ({format_minutes_as_clock(dep_min)}) is before current arrival ({format_minutes_as_clock(current_arr_min)})"
                )
            elif not c_conn_feasible:
                if wait_min < constraints.min_connection_minutes:
                    violations.append(
                        f"Connection buffer ({wait_min}m) is less than minimum required ({constraints.min_connection_minutes}m)"
                    )
                else:
                    violations.append(
                        f"Waiting time ({wait_min}m) exceeds maximum allowed ({constraints.max_waiting_minutes}m)"
                    )
            if not c_before_hotel and hotel_checkin_min is not None:
                violations.append(
                    f"Arrival ({format_minutes_as_clock(arr_min)}) is after hotel latest check-in ({format_minutes_as_clock(hotel_checkin_min)})"
                )
            if not c_has_seats:
                violations.append(
                    f"Available seats ({cand.available_seats}) less than required ({constraints.required_seats})"
                )
            violations.extend(pref_violations)

            is_feasible = c_dep_after_arr and c_conn_feasible and c_before_hotel and c_has_seats and c_prefs_ok

            parsed_candidates.append({
                "index": idx,
                "raw": cand,
                "dep_min": dep_min,
                "arr_min": arr_min,
                "travel_min": travel_min,
                "wait_min": wait_min,
                "is_feasible": is_feasible,
                "constraint_checks": {
                    "departure_after_arrival": c_dep_after_arr,
                    "connection_time_feasible": c_conn_feasible,
                    "arrival_before_hotel_checkin": c_before_hotel,
                    "transport_has_availability": c_has_seats,
                    "passenger_preferences_respected": c_prefs_ok
                },
                "violation_reasons": violations
            })

        # 3. Compute normalized multi-criteria objective terms across candidates
        max_price = max((c["raw"].price for c in parsed_candidates), default=1.0) or 1.0
        max_travel = max((c["travel_min"] for c in parsed_candidates), default=1) or 1
        max_wait = max((max(0, c["wait_min"]) for c in parsed_candidates), default=1) or 1
        max_changes_val = max((c["raw"].number_of_changes for c in parsed_candidates), default=1) or 1
        min_arr = min((c["arr_min"] for c in parsed_candidates), default=0)
        max_arr = max((c["arr_min"] for c in parsed_candidates), default=1)
        arr_span = max(1, max_arr - min_arr)

        for item in parsed_candidates:
            cand = item["raw"]
            norm_price = (cand.price / max_price) * 100.0
            norm_travel = (item["travel_min"] / max_travel) * 100.0
            norm_wait = (max(0, item["wait_min"]) / max_wait) * 100.0
            norm_changes = (cand.number_of_changes / max_changes_val) * 100.0 if cand.number_of_changes > 0 else 0.0
            norm_arrival = ((item["arr_min"] - min_arr) / arr_span) * 100.0
            norm_unreliability = (1.0 - cand.reliability) * 100.0

            weighted_penalty = (
                weights.price * norm_price
                + weights.travel_time * norm_travel
                + weights.waiting_time * norm_wait
                + weights.number_of_changes * norm_changes
                + weights.arrival_time * norm_arrival
                + weights.reliability * norm_unreliability
            )
            item["objective_breakdown"] = {
                "price_component": round(weights.price * norm_price, 2),
                "travel_time_component": round(weights.travel_time * norm_travel, 2),
                "waiting_time_component": round(weights.waiting_time * norm_wait, 2),
                "changes_component": round(weights.number_of_changes * norm_changes, 2),
                "arrival_time_component": round(weights.arrival_time * norm_arrival, 2),
                "reliability_component": round(weights.reliability * norm_unreliability, 2),
                "total_weighted_penalty": round(weighted_penalty, 2)
            }
            # Integer-scaled objective coefficient for OR-Tools CP-SAT
            item["cp_sat_coeff"] = int(round(weighted_penalty * 100))

        # 4. Formulate and solve with Google OR-Tools CP-SAT
        model = cp_model.CpModel()
        n = len(parsed_candidates)
        x = [model.NewBoolVar(f"select_opt_{i}") for i in range(n)]

        # Exactly one recovery option must be chosen
        model.AddExactlyOne(x)

        # Linear expressions for the selected option's parameters
        selected_dep = sum(parsed_candidates[i]["dep_min"] * x[i] for i in range(n))
        selected_arr = sum(parsed_candidates[i]["arr_min"] * x[i] for i in range(n))
        selected_wait = sum(parsed_candidates[i]["wait_min"] * x[i] for i in range(n))
        selected_seats = sum(parsed_candidates[i]["raw"].available_seats * x[i] for i in range(n))
        selected_price_cents = sum(int(round(parsed_candidates[i]["raw"].price * 100)) * x[i] for i in range(n))
        selected_changes = sum(parsed_candidates[i]["raw"].number_of_changes * x[i] for i in range(n))
        selected_rel_millis = sum(int(round(parsed_candidates[i]["raw"].reliability * 1000)) * x[i] for i in range(n))

        # Constraint 1: Departure must be after current arrival
        model.Add(selected_dep >= current_arr_min)

        # Constraint 2: Connection time must be feasible
        model.Add(selected_wait >= constraints.min_connection_minutes)
        if constraints.max_waiting_minutes is not None:
            model.Add(selected_wait <= constraints.max_waiting_minutes)

        # Constraint 3: Arrival must be before hotel latest check-in
        if hotel_checkin_min is not None:
            model.Add(selected_arr <= hotel_checkin_min)

        # Constraint 4: Transport must have availability
        model.Add(selected_seats >= constraints.required_seats)

        # Constraint 5: Passenger preferences must be respected
        if prefs.max_budget is not None:
            model.Add(selected_price_cents <= int(round(prefs.max_budget * 100)))
        if prefs.max_changes is not None:
            model.Add(selected_changes <= prefs.max_changes)
        if prefs.min_reliability is not None:
            model.Add(selected_rel_millis >= int(round(prefs.min_reliability * 1000)))

        # Mode & individual feasibility constraints
        for i, item in enumerate(parsed_candidates):
            if not item["is_feasible"]:
                model.Add(x[i] == 0)

        # Objective: Minimize weighted multi-criteria penalty
        model.Minimize(sum(parsed_candidates[i]["cp_sat_coeff"] * x[i] for i in range(n)))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 5.0
        status = solver.Solve(model)
        status_name = solver.StatusName(status)

        selected_option_dict: Optional[Dict[str, Any]] = None
        alternatives_output: List[Dict[str, Any]] = []
        objective_score = 0.0
        constraints_satisfied = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

        for i, item in enumerate(parsed_candidates):
            cand = item["raw"]
            is_selected = bool(constraints_satisfied and solver.Value(x[i]) == 1)
            opt_payload = {
                "transport_id": cand.transport_id,
                "name": cand.name or f"{cand.provider} ({cand.transport_id})",
                "supplier_type": cand.supplier_type,
                "provider": cand.provider,
                "vehicle_number": cand.vehicle_number or cand.transport_id,
                "origin": cand.origin,
                "destination": cand.destination,
                "departure": cand.departure,
                "arrival": cand.arrival,
                "departure_clock": format_minutes_as_clock(item["dep_min"]),
                "arrival_clock": format_minutes_as_clock(item["arr_min"]),
                "travel_time_minutes": item["travel_min"],
                "waiting_time_minutes": item["wait_min"],
                "price": cand.price,
                "currency": cand.currency,
                "available_seats": cand.available_seats,
                "number_of_changes": cand.number_of_changes,
                "reliability": cand.reliability,
                "feasible": item["is_feasible"],
                "selected": is_selected,
                "objective_score": item["objective_breakdown"]["total_weighted_penalty"],
                "objective_breakdown": item["objective_breakdown"],
                "constraint_checks": item["constraint_checks"],
                "violation_reasons": item["violation_reasons"]
            }
            alternatives_output.append(opt_payload)
            if is_selected:
                selected_option_dict = opt_payload
                objective_score = round(solver.ObjectiveValue() / 100.0, 2)

        # Sort alternatives so feasible options appear ranked by objective_score first, followed by infeasible options
        alternatives_output.sort(key=lambda a: (not a["feasible"], a["objective_score"]))

        explanation = self._build_explanation(
            selected=selected_option_dict,
            alternatives=alternatives_output,
            constraints=constraints,
            objective_score=objective_score,
            status_name=status_name
        )

        return OptimizationResponse(
            selected_option=selected_option_dict,
            alternatives=alternatives_output,
            objective_score=objective_score,
            constraints_satisfied=constraints_satisfied,
            explanation=explanation,
            solver_metadata={
                "solver": "Google OR-Tools CP-SAT",
                "status": status_name,
                "wall_time_ms": round(solver.WallTime() * 1000.0, 3),
                "num_candidates": n,
                "num_feasible": sum(1 for a in alternatives_output if a["feasible"]),
                "num_infeasible": sum(1 for a in alternatives_output if not a["feasible"])
            }
        )

    @staticmethod
    def _build_explanation(
        selected: Optional[Dict[str, Any]],
        alternatives: List[Dict[str, Any]],
        constraints: OptimizationConstraints,
        objective_score: float,
        status_name: str
    ) -> str:
        if not selected:
            reasons = []
            for alt in alternatives:
                if alt["violation_reasons"]:
                    reasons.append(f"{alt['name']} ({alt['transport_id']}): {'; '.join(alt['violation_reasons'])}")
            reason_summary = " | ".join(reasons) if reasons else "No feasible options available."
            return (
                f"Google OR-Tools CP-SAT determined the problem is {status_name}. "
                f"No candidate satisfied all hard constraints. Rejections: {reason_summary}"
            )

        rejected_notes = []
        for alt in alternatives:
            if alt["transport_id"] == selected["transport_id"]:
                continue
            if not alt["feasible"]:
                rejected_notes.append(
                    f"{alt['name']} ({alt['transport_id']}) pruned due to constraint violation ({', '.join(alt['violation_reasons'])})"
                )
            else:
                rejected_notes.append(
                    f"{alt['name']} ({alt['transport_id']}) feasible but had higher weighted penalty ({alt['objective_score']} vs {objective_score})"
                )

        rejected_str = f" Alternatives evaluated: {'; '.join(rejected_notes)}." if rejected_notes else ""
        return (
            f"Google OR-Tools CP-SAT solver ({status_name}) selected {selected['name']} ({selected['transport_id']}) "
            f"departing {selected['departure_clock']} and arriving {selected['arrival_clock']} "
            f"at {selected['currency']} {selected['price']} with optimal weighted objective score {objective_score} "
            f"(connection wait {selected['waiting_time_minutes']}m >= {constraints.min_connection_minutes}m min buffer, "
            f"arriving before hotel check-in cutoff {constraints.hotel_latest_checkin}).{rejected_str}"
        )


ortools_recovery_optimizer = ORToolsRecoveryOptimizer()
