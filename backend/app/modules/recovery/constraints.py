"""
Recovery Constraints Engine.
Interprets human review rejection feedback into mathematical optimization constraints
and preserves historical constraints across revision cycles.

Workflow:
PLAN -> HUMAN REVIEW
  -> APPROVE -> EXECUTE
  OR
  -> REJECT -> FEEDBACK -> CONSTRAINTS -> REPLAN -> HUMAN REVIEW
"""
import re
from typing import Dict, Any, List, Optional


class RecoveryConstraintEngine:
    """
    Parses human rejection feedback (reasons + custom text) into formal constraints,
    merges them with prior constraints (preserving past decisions), and formats
    human-readable constraint descriptions.
    """

    KNOWN_AIRLINES = [
        "Airline A", "Airline B", "Airline C", "Airline D",
        "IndiGo", "IndiGo Airlines", "Air India", "Vistara",
        "SpiceJet", "Akasa Air", "Air India Express"
    ]

    @classmethod
    def interpret_rejection(
        cls,
        reasons: Optional[List[str]] = None,
        feedback_text: Optional[str] = None,
        current_plan: Optional[Dict[str, Any]] = None,
        previous_constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Converts human feedback into a structured constraints dictionary,
        merging with any previous constraints to ensure nothing is lost.
        """
        reasons = reasons or []
        text = (feedback_text or "").strip()
        current_plan = current_plan or {}
        prev = previous_constraints or {}

        new_excluded_providers: List[str] = []
        new_excluded_transport_ids: List[str] = []
        new_excluded_modes: List[str] = []
        new_max_budget: Optional[float] = None
        new_min_departure: Optional[str] = None
        new_max_arrival: Optional[str] = None

        # Current plan details
        selected_option = current_plan.get("selected_option") or {}
        current_provider = selected_option.get("provider") or ""
        current_name = selected_option.get("name") or ""
        current_transport_id = selected_option.get("transport_id") or ""
        current_mode = (selected_option.get("supplier_type") or "").lower()
        current_price = float(selected_option.get("price") or current_plan.get("estimated_additional_cost") or 0.0)

        # ----------------------------------------------------
        # 1. Parse Provider / Airline Exclusions
        # ----------------------------------------------------
        # Direct check for "Airline X" or known airline names in text
        airline_match = re.search(r"\b(Airline\s+[A-Za-z0-9]+)\b", text, re.IGNORECASE)
        if airline_match:
            new_excluded_providers.append(airline_match.group(1).title())

        for known in cls.KNOWN_AIRLINES:
            if re.search(rf"\b{re.escape(known)}\b", text, re.IGNORECASE):
                if known.title() not in [p.title() for p in new_excluded_providers]:
                    new_excluded_providers.append(known)

        # Catch-all: "don't want X", "exclude X", "no X"
        exclusion_patterns = [
            r"(?:don'?t\s+want|do\s+not\s+want|exclude|avoid|remove|skip)\s+([A-Za-z0-9\s]+?)(?:[.,;]|\band\b|$)",
            r"(?:no|not)\s+([A-Za-z0-9\s]+?)(?:[.,;]|\band\b|$)",
        ]
        for pat in exclusion_patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                phrase = match.group(1).strip()
                # Ignore common words
                if phrase.lower() not in ("to", "this", "that", "any", "more", "a", "an", "the", "pay", "change", "it"):
                    if not any(phrase.lower() in p.lower() for p in new_excluded_providers):
                        # If phrase is like "Airline A"
                        if "airline" in phrase.lower() or "railways" in phrase.lower() or "express" in phrase.lower():
                            new_excluded_providers.append(phrase.title())

        # If user checked "I don't want this airline" and no airline was specified in text
        if any("airline" in r.lower() for r in reasons):
            if not new_excluded_providers:
                if current_provider:
                    new_excluded_providers.append(current_provider)
                elif "airline" in current_name.lower():
                    new_excluded_providers.append(current_name)

        # ----------------------------------------------------
        # 2. Parse Budget Constraints
        # ----------------------------------------------------
        # Look for explicit budget phrases
        curr_sym = r"(?:[₹$]|INR|Rs\.?|Rupees)?"
        budget_patterns = [
            rf"(?:max(?:imum)?\s*(?:budget)?(?:\s*(?:is|of|:))?|under|less\s+than|below|no\s+more\s+than|cap\s*(?:at)?)\s*{curr_sym}\s*([\d,]+(?:\.\d+)?)",
            rf"(?:[₹$]|INR|Rs\.?|Rupees)\s*([\d,]+(?:\.\d+)?)",
            rf"\b(?:budget\s*(?:of|is)?\s*)\s*{curr_sym}\s*([\d,]+(?:\.\d+)?)",
            r"(?:max(?:imum)?|budget|cap)\s*[:=]?\s*([\d,]+(?:\.\d+)?)",
        ]
        for pat in budget_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                raw_num = m.group(1).replace(",", "")
                try:
                    val = float(raw_num)
                    if val > 0:
                        new_max_budget = val
                        break
                except ValueError:
                    pass

        # If user selected "Too expensive" and gave no number in text
        if any("expensive" in r.lower() for r in reasons) and new_max_budget is None:
            if current_price > 0:
                new_max_budget = round(current_price * 0.85, 2)

        # ----------------------------------------------------
        # 3. Parse Mode Preferences
        # ----------------------------------------------------
        if any("another transport" in r.lower() for r in reasons):
            if current_mode:
                new_excluded_modes.append(current_mode)

        if re.search(r"\b(?:train\s+only|only\s+train)\b", text, re.IGNORECASE):
            new_excluded_modes.extend(["flight", "bus"])
        elif re.search(r"\b(?:flight\s+only|only\s+flight)\b", text, re.IGNORECASE):
            new_excluded_modes.extend(["train", "bus"])
        elif re.search(r"\b(?:no\s+bus|exclude\s+bus)\b", text, re.IGNORECASE):
            new_excluded_modes.append("bus")

        # ----------------------------------------------------
        # 4. Preserve Previous Constraints (Strict Retention)
        # ----------------------------------------------------
        # Providers
        all_excluded_providers = list(prev.get("excluded_providers", []))
        for p in new_excluded_providers:
            if not any(p.lower() == existing.lower() for existing in all_excluded_providers):
                all_excluded_providers.append(p)

        # Transport IDs
        all_excluded_transport_ids = list(prev.get("excluded_transport_ids", []))
        for tid in new_excluded_transport_ids:
            if tid not in all_excluded_transport_ids:
                all_excluded_transport_ids.append(tid)

        # Modes
        all_excluded_modes = list(prev.get("excluded_modes", []))
        for m in new_excluded_modes:
            if m.lower() not in [em.lower() for em in all_excluded_modes]:
                all_excluded_modes.append(m.lower())

        # Budget: Take the stricter (minimum) if multiple specified
        prev_budget = prev.get("max_budget")
        if prev_budget is not None and new_max_budget is not None:
            effective_budget = min(float(prev_budget), float(new_max_budget))
        elif new_max_budget is not None:
            effective_budget = float(new_max_budget)
        elif prev_budget is not None:
            effective_budget = float(prev_budget)
        else:
            effective_budget = None

        # Build clean user-facing descriptions
        descriptions: List[str] = []
        for p in all_excluded_providers:
            descriptions.append(f"Exclude {p}")
        for tid in all_excluded_transport_ids:
            descriptions.append(f"Exclude transport {tid}")
        for m in all_excluded_modes:
            descriptions.append(f"Exclude {m.capitalize()}")
        if effective_budget is not None:
            descriptions.append(f"Maximum budget ₹{int(effective_budget):,}" if effective_budget.is_integer() else f"Maximum budget ₹{effective_budget:,.2f}")

        return {
            "excluded_providers": all_excluded_providers,
            "excluded_transport_ids": all_excluded_transport_ids,
            "excluded_modes": all_excluded_modes,
            "max_budget": effective_budget,
            "min_departure_time": new_min_departure or prev.get("min_departure_time"),
            "max_arrival_time": new_max_arrival or prev.get("max_arrival_time"),
            "descriptions": descriptions,
        }

    @classmethod
    def filter_candidates(
        cls,
        candidates: List[Any],
        active_constraints: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """
        Applies active rejection constraints to candidate alternatives list
        BEFORE passing to OR-Tools CP-SAT optimizer, ensuring excluded providers
        and transport options are strictly pruned while preserving OR-Tools logic.
        """
        if not active_constraints:
            return list(candidates)

        excluded_providers = [p.lower() for p in active_constraints.get("excluded_providers", [])]
        excluded_tids = active_constraints.get("excluded_transport_ids", [])
        excluded_modes = [m.lower() for m in active_constraints.get("excluded_modes", [])]
        max_budget = active_constraints.get("max_budget")

        filtered = []
        for cand in candidates:
            # Handle CandidateAlternativeInput or dict
            provider = (getattr(cand, "provider", None) or (cand.get("provider") if isinstance(cand, dict) else "") or "").lower()
            name = (getattr(cand, "name", None) or (cand.get("name") if isinstance(cand, dict) else "") or "").lower()
            tid = getattr(cand, "transport_id", None) or (cand.get("transport_id") if isinstance(cand, dict) else "") or ""
            mode = (getattr(cand, "supplier_type", None) or (cand.get("supplier_type") if isinstance(cand, dict) else "") or "").lower()
            price = float(getattr(cand, "price", None) or (cand.get("price") if isinstance(cand, dict) else 0.0) or 0.0)

            # Check transport ID exclusion
            if tid in excluded_tids:
                continue

            # Check provider / airline exclusion
            if any(ex in provider or ex in name or ex in tid.lower() for ex in excluded_providers):
                continue

            # Check mode exclusion
            if mode in excluded_modes:
                continue

            # Check budget limit
            if max_budget is not None and price > max_budget:
                continue

            filtered.append(cand)

        return filtered


constraint_engine = RecoveryConstraintEngine()
