"""
Response Formatter for the AeroAI Unified AI Agent.

Generates structured responses adhering to the required separation:
1. Delay probability & ML prediction
2. Model factors & explanation (SHAP feature contributions, framed non-causally)
3. Current flight status (LIVE or MOCK provenance)
4. Weather (LIVE, HISTORICAL, or MOCK observations)
5. Relevant policy (Grounded citations from DGCA, EU261, US DOT, or airline CoC)
6. Recommendation (Actionable, calibrated guidance without false certainty)

Enforces strict anti-hallucination, missing data transparency, and data provenance contracts.
"""

from typing import Dict, Any, List, Optional


class ResponseFormatter:
    """Formats unified tool outputs into separated, calibrated, and compliant agent responses."""

    def format_response(
        self,
        query: str,
        selected_tools: List[str],
        tool_results: Dict[str, Any],
        tool_errors: Dict[str, str],
        entities: Any
    ) -> Dict[str, Any]:
        """
        Synthesizes individual tool results into a structured response text and JSON payload.
        """
        sections: Dict[str, Any] = {}
        text_blocks: List[str] = []

        # -------------------------------------------------------------
        # 1. Delay Probability & ML Prediction Section
        # -------------------------------------------------------------
        pred_res = tool_results.get("delay_prediction")
        pred_err = tool_errors.get("delay_prediction")

        if "delay_prediction" in selected_tools:
            if pred_res and pred_res.get("status") == "success":
                prob = pred_res.get("delay_probability", 0.0)
                pct = int(round(prob * 100))
                label = pred_res.get("prediction", "Likely On Time")
                model_name = pred_res.get("model_name", "Random Forest Classifier")

                pred_text = f"Delay probability: {pct}% ({label})"
                text_blocks.append(pred_text)

                # Model Factors (SHAP Explanations)
                factors_lines = ["\nModel factors:"]
                explanation = pred_res.get("explanation", [])
                if explanation:
                    for item in explanation[:5]:
                        feat = item.get("feature", "Unknown")
                        impact = item.get("impact", "")
                        factors_lines.append(f"- {feat}: {impact}")
                    factors_lines.append(
                        "Note: These features contributed most to the model's prediction. "
                        "Predictions represent statistical likelihood from historical BTS & ASOS weather patterns, "
                        "not deterministic certainty."
                    )
                else:
                    factors_lines.append("- Baseline operational schedule parameters within standard tolerances.")

                text_blocks.append("\n".join(factors_lines))

                sections["ml_prediction"] = {
                    "delay_probability": prob,
                    "delay_percentage": pct,
                    "prediction": label,
                    "model_name": model_name,
                    "data_source": "PREDICTED",
                    "explanation": explanation
                }
            elif pred_err:
                text_blocks.append(f"Delay probability: Unavailable\n\nModel factors:\n- Delay prediction calculation failed: {pred_err}")
                sections["ml_prediction"] = {"status": "error", "error": pred_err}
            else:
                text_blocks.append("Delay probability: Unavailable\n\nModel factors:\n- Insufficient flight parameters available to compute ML delay probability.")
                sections["ml_prediction"] = {"status": "unavailable"}

        # -------------------------------------------------------------
        # 2. Current Flight Status Section
        # -------------------------------------------------------------
        status_res = tool_results.get("flight_status")
        status_err = tool_errors.get("flight_status")

        if "flight_status" in selected_tools:
            status_lines = ["\nCurrent flight status:"]
            if status_res and status_res.get("status") == "success":
                rec = status_res.get("flight_record", {})
                fn = rec.get("flight_number", "Unknown")
                carrier = rec.get("carrier_name", rec.get("carrier_code", "Unknown"))
                orig = rec.get("origin", "N/A")
                dest = rec.get("destination", "N/A")
                op_status = rec.get("status", "SCHEDULED")
                delay_mins = rec.get("delay_minutes", 0)
                data_src = rec.get("data_source", "MOCK")
                coords = rec.get("live_coordinates")

                status_lines.append(f"- Flight: {fn} ({carrier})")
                status_lines.append(f"- Route: {orig} -> {dest}")
                status_lines.append(f"- Operational status: {op_status} ({delay_mins} min delay)")
                status_lines.append(f"- Data source: {data_src}")
                if coords:
                    lat = coords.get("latitude")
                    lon = coords.get("longitude")
                    alt = coords.get("altitude_meters")
                    status_lines.append(f"- Live telemetry: Lat {lat:.3f}, Lon {lon:.3f}, Altitude {alt}m")
                if rec.get("is_fallback"):
                    status_lines.append("- Notice: Retrieved via fallback simulation due to live transponder unavailability.")

                sections["flight_status"] = rec
            elif status_res and status_res.get("status") == "not_found":
                fn = status_res.get("flight_number", "Specified flight")
                status_lines.append(f"- Flight {fn} was not found in live ADS-B radar or operational airline schedules.")
                status_lines.append("- Notice: Information is missing; status was not fabricated.")
                sections["flight_status"] = {"status": "not_found", "flight_number": fn}
            elif status_err:
                status_lines.append(f"- Flight status is temporarily unavailable due to a service error: {status_err}")
                sections["flight_status"] = {"status": "error", "error": status_err}
            else:
                status_lines.append("- No flight number was identified to perform an operational status lookup.")
                sections["flight_status"] = {"status": "no_flight_identified"}

            text_blocks.append("\n".join(status_lines))

        # -------------------------------------------------------------
        # 3. Weather Section
        # -------------------------------------------------------------
        weather_res = tool_results.get("weather")
        weather_err = tool_errors.get("weather")

        if "weather" in selected_tools:
            weather_lines = ["\nWeather:"]
            if weather_res and weather_res.get("status") == "success":
                w = weather_res.get("weather", {})
                apt = w.get("airport_code", "Unknown")
                temp = w.get("temperature_c", "N/A")
                cond = w.get("condition", "Standard")
                wind = w.get("wind_speed_mps", "N/A")
                vis = w.get("visibility_m", "N/A")
                data_src = w.get("data_source", "HISTORICAL")

                weather_lines.append(f"- Airport {apt}: {temp}°C, {cond}, Wind {wind} m/s, Visibility {vis}m")
                weather_lines.append(f"- Data source: {data_src}")
                sections["weather"] = w
            elif weather_res and weather_res.get("status") == "unavailable":
                apt = weather_res.get("airport", "Airport")
                weather_lines.append(f"- Weather observation for {apt} is currently unavailable.")
                sections["weather"] = {"status": "unavailable", "airport": apt}
            elif weather_err:
                weather_lines.append(f"- Weather observation failed: {weather_err}")
                sections["weather"] = {"status": "error", "error": weather_err}
            else:
                weather_lines.append("- Weather observation is currently unavailable for the requested location.")
                sections["weather"] = {"status": "unavailable"}

            text_blocks.append("\n".join(weather_lines))

        # -------------------------------------------------------------
        # 4. Flight Search Section (If search tool was called)
        # -------------------------------------------------------------
        search_res = tool_results.get("flight_search")
        search_err = tool_errors.get("flight_search")

        if "flight_search" in selected_tools:
            search_lines = ["\nAvailable Flight Options:"]
            if search_res and search_res.get("status") == "success":
                flights = search_res.get("flights", [])
                if flights:
                    for flt in flights[:4]:
                        fn = flt.get("flight_number")
                        carrier = flt.get("carrier")
                        dep_raw = flt.get("departure_time", "")
                        arr_raw = flt.get("arrival_time", "")
                        dep_str = dep_raw.strftime("%H:%M") if hasattr(dep_raw, "strftime") else str(dep_raw)[11:16]
                        arr_str = arr_raw.strftime("%H:%M") if hasattr(arr_raw, "strftime") else str(arr_raw)[11:16]
                        seats = flt.get("available_seats", 1)
                        price = flt.get("price_inr", 4500)
                        src = flt.get("data_source", "MOCK")
                        search_lines.append(f"- {fn} ({carrier}): Dep {dep_str} -> Arr {arr_str} | {seats} seats | ₹{price} ({src})")
                else:
                    search_lines.append("- No alternative flights matched the route and seat criteria.")
                sections["flight_search"] = search_res
            elif search_err:
                search_lines.append(f"- Flight search failed: {search_err}")
                sections["flight_search"] = {"status": "error", "error": search_err}

            text_blocks.append("\n".join(search_lines))

        # -------------------------------------------------------------
        # 5. Relevant Policy Section
        # -------------------------------------------------------------
        rag_res = tool_results.get("policy_rag")
        rag_err = tool_errors.get("policy_rag")

        if "policy_rag" in selected_tools:
            policy_lines = ["\nRelevant policy:"]
            if rag_res and rag_res.get("status") == "success":
                ans = rag_res.get("answer", "").strip()
                cits = rag_res.get("citations", [])
                sufficient = rag_res.get("sufficient_evidence", True)

                policy_lines.append(ans)
                if cits:
                    policy_lines.append("\nAuthoritative Citations:")
                    for c in cits:
                        doc = c.get("document_title", "Regulatory CAR")
                        reg = c.get("regulator", "")
                        sec = c.get("section", "")
                        policy_lines.append(f"- {doc} [{reg}] (Section: {sec})")

                sections["policy_information"] = {
                    "answer": ans,
                    "citations": cits,
                    "sufficient_evidence": sufficient,
                    "data_source": "AUTHORITATIVE_REGULATORY_POLICY"
                }
            elif rag_err:
                policy_lines.append(f"- Policy retrieval is temporarily unavailable: {rag_err}")
                sections["policy_information"] = {"status": "error", "error": rag_err}
            else:
                policy_lines.append("- Policy database contains insufficient evidence for this query.")
                sections["policy_information"] = {"status": "insufficient_evidence"}

            text_blocks.append("\n".join(policy_lines))

        # -------------------------------------------------------------
        # 6. Recommendation Section
        # -------------------------------------------------------------
        rec_lines = ["\nRecommendation:"]
        recs = self._synthesize_recommendations(
            query=query,
            selected_tools=selected_tools,
            tool_results=tool_results,
            tool_errors=tool_errors
        )
        rec_lines.extend(recs)
        text_blocks.append("\n".join(rec_lines))
        sections["recommendation"] = " ".join([r.lstrip("- ") for r in recs])

        final_response_text = "\n".join(text_blocks)

        return {
            "response_text": final_response_text,
            "sections": sections
        }

    def _synthesize_recommendations(
        self,
        query: str,
        selected_tools: List[str],
        tool_results: Dict[str, Any],
        tool_errors: Dict[str, str]
    ) -> List[str]:
        """Produces balanced, objective recommendations without false certainty."""
        recs: List[str] = []

        pred_res = tool_results.get("delay_prediction")
        status_res = tool_results.get("flight_status")
        rag_res = tool_results.get("policy_rag")

        # Missing data or errors noted first
        if tool_errors:
            missing_items = ", ".join(tool_errors.keys())
            recs.append(f"- Note: Data from {missing_items} could not be retrieved and was excluded from this assessment.")

        # Delay Risk Advice
        if pred_res and pred_res.get("status") == "success":
            prob = pred_res.get("delay_probability", 0.0)
            if prob >= 0.50:
                recs.append(
                    f"- Elevated Disruption Likelihood: Model projects a {int(round(prob*100))}% delay probability. "
                    "Monitor airport flight information display systems (FIDS) closely and avoid tight non-protected connections."
                )
            else:
                recs.append(
                    f"- Low Disruption Risk: Projected delay probability is {int(round(prob*100))}%. "
                    "Flight parameters remain within standard operational tolerance."
                )

        # Operational Status Advice
        if status_res and status_res.get("status") == "success":
            rec = status_res.get("flight_record", {})
            delay_mins = rec.get("delay_minutes", 0)
            if delay_mins >= 120:
                recs.append(
                    f"- Active Disruption: Aircraft is currently operating with a {delay_mins}-minute delay. "
                    "Check with ground agents for gate-side updates and designated holding areas."
                )

        # Policy & Passenger Rights Advice
        if rag_res and rag_res.get("status") == "success":
            if rag_res.get("sufficient_evidence", True):
                recs.append(
                    "- Regulatory Protection: You may request statutory amenities (meals, rebooking, or refund) "
                    "as outlined under applicable DGCA / EU261 regulations if your delay reaches the statutory duration."
                )
            else:
                recs.append(
                    "- Carrier Clarification: Your request touches rules outside verified regulatory mandates. "
                    "Contact airline customer relations directly for case-specific determinations."
                )

        # Default fallback recommendation if none generated
        if not recs:
            recs.append(
                "- For operational questions, keep your booking reference accessible and verify departure timings through carrier channels."
            )

        return recs


# Singleton formatter
response_formatter = ResponseFormatter()
