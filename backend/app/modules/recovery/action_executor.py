"""
Stage 8: Autonomous Recovery Action Execution Engine.

Converts a Recovery Plan into executable actions and executes each action
through the decoupled SupplierIntegrationService against our Mock Supplier APIs.

Features:
- 6 Supported Actions:
  1. rebook_transportation
  2. cancel_booking
  3. request_refund
  4. modify_hotel_checkin
  5. notify_traveler
  6. notify_relevant_contact
- Structured Audit Record per action:
  {
    "action_type": "",
    "booking_id": "",
    "status": "",
    "timestamp": "",
    "request": {},
    "response": {},
    "error": null
  }
- Strict Idempotency (prevents duplicate bookings if triggered multiple times)
- Automatic Retries & Timeout Handling
- Failed Action Recovery & Partial Success Handling
- Compensating Rollback when critical rebooking fails after cancellation
- Explicit labeling that all transactions are SIMULATED MOCK SUPPLIER API calls
"""
import hashlib
import json
import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional

from app.modules.suppliers.service import supplier_service
from app.modules.suppliers.interfaces import SupplierAdapterException
from app.modules.events.event_bus import event_bus

MOCK_TRANSACTION_DISCLAIMER = "SIMULATED TRANSACTION AGAINST MOCK SUPPLIER API - NOT A REAL WORLD BOOKING"


class IdempotencyAndAuditStore:
    """
    In-memory store for idempotency keys and immutable action execution audit records.
    Guarantees that re-submitting an action with the same idempotency_key returns
    the cached result without creating duplicate supplier bookings.
    """
    _idempotency_cache: Dict[str, Dict[str, Any]] = {}
    _audit_history: List[Dict[str, Any]] = []

    @classmethod
    def compute_key(cls, plan_id: str, action_type: str, booking_id: str, params: Dict[str, Any]) -> str:
        canonical = json.dumps(
            {
                "plan_id": plan_id,
                "action_type": action_type,
                "booking_id": booking_id,
                "transport_id": params.get("transport_id"),
                "hotel_id": params.get("hotel_id"),
                "new_check_in": params.get("new_check_in"),
                "recipient": params.get("recipient")
            },
            sort_keys=True
        )
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        return f"IDEMP-{plan_id}-{action_type}-{digest}"

    @classmethod
    def get_cached(cls, idempotency_key: str) -> Optional[Dict[str, Any]]:
        return cls._idempotency_cache.get(idempotency_key)

    @classmethod
    def save_successful_action(cls, idempotency_key: str, audit_record: Dict[str, Any]) -> None:
        cls._idempotency_cache[idempotency_key] = audit_record

    @classmethod
    def record_audit(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        cls._audit_history.append(record)
        return record

    @classmethod
    def get_history(cls) -> List[Dict[str, Any]]:
        return list(reversed(cls._audit_history))

    @classmethod
    def clear(cls) -> None:
        cls._idempotency_cache.clear()
        cls._audit_history.clear()


class RecoveryActionExecutor:
    """
    Converts a Recovery Plan into executable steps and runs them through
    the SupplierIntegrationService with idempotency, retries, timeout handling,
    partial success recovery, and compensating rollback.
    """

    @staticmethod
    def compile_plan_to_actions(plan_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Converts a high-level recovery plan description into the 6 canonical executable actions:
        1. cancel_booking (Cancel original disrupted/missed transport)
        2. rebook_transportation (Rebook onto selected alternative transport)
        3. request_refund (Submit refund claim for cancelled/missed transport)
        4. modify_hotel_checkin (Update downstream hotel arrival window)
        5. notify_traveler (Send recovery itinerary & confirmation to traveler)
        6. notify_relevant_contact (Send late check-in / arrival notice to hotel or contact)
        """
        if plan_input.get("actions") and len(plan_input["actions"]) > 0:
            return list(plan_input["actions"])

        original_ref = plan_input.get("original_booking_id", "12015-SHT")
        original_transport_id = plan_input.get("original_transport_id", "TRN123")
        original_price = float(plan_input.get("original_price", 800.0))
        target_transport_id = plan_input.get("new_transport_id", "TRN124")
        passenger_name = plan_input.get("passenger_name", "Sahil Sharma")
        hotel_booking_id = plan_input.get("hotel_booking_id", "HTL-JAI-101")
        hotel_id = plan_input.get("hotel_id", "HTL101")
        new_check_in = plan_input.get("new_check_in", "2026-10-20T22:30:00")
        traveler_email = plan_input.get("traveler_email", "traveler@example.com")
        contact_email = plan_input.get("contact_email", "frontdesk@heritagepalacejaipur.com")

        return [
            {
                "step": 1,
                "action_type": "cancel_booking",
                "booking_id": original_ref,
                "critical": True,
                "request": {
                    "booking_reference": original_ref,
                    "transport_id": original_transport_id,
                    "supplier_type": "train",
                    "reason": "DISRUPTION_MISSED_CONNECTION",
                    "original_price": original_price
                }
            },
            {
                "step": 2,
                "action_type": "rebook_transportation",
                "booking_id": target_transport_id,
                "critical": True,
                "request": {
                    "original_booking_ref": original_ref,
                    "transport_id": target_transport_id,
                    "passenger_name": passenger_name,
                    "seats": int(plan_input.get("seats", 1)),
                    "reason": "DISRUPTION_RECOVERY_PLAN",
                    "waive_change_fee": True
                }
            },
            {
                "step": 3,
                "action_type": "request_refund",
                "booking_id": original_ref,
                "critical": False,
                "request": {
                    "booking_reference": original_ref,
                    "transport_id": original_transport_id,
                    "supplier_type": "train",
                    "original_price": original_price,
                    "currency": "INR",
                    "reason": "INVOLUNTARY_DISRUPTION_WAIVER",
                    "is_disruption_waiver": True
                }
            },
            {
                "step": 4,
                "action_type": "modify_hotel_checkin",
                "booking_id": hotel_booking_id,
                "critical": False,
                "request": {
                    "booking_reference": hotel_booking_id,
                    "hotel_id": hotel_id,
                    "new_check_in": new_check_in,
                    "late_arrival_notice": True,
                    "notes": f"Traveler rebooked onto {target_transport_id}; updated check-in {new_check_in}."
                }
            },
            {
                "step": 5,
                "action_type": "notify_traveler",
                "booking_id": target_transport_id,
                "critical": False,
                "request": {
                    "recipient": traveler_email,
                    "channel": "EMAIL_AND_WEBSOCKET",
                    "subject": f"Recovery Executed: Rebooked onto {target_transport_id}",
                    "message": (
                        f"Your missed connection ({original_ref}) was cancelled with full refund waiver, "
                        f"rebooked onto {target_transport_id}, and hotel ({hotel_booking_id}) check-in updated to {new_check_in}."
                    )
                }
            },
            {
                "step": 6,
                "action_type": "notify_relevant_contact",
                "booking_id": hotel_booking_id,
                "critical": False,
                "request": {
                    "recipient": contact_email,
                    "contact_role": "HOTEL_FRONT_DESK",
                    "channel": "SUPPLIER_CRS_ALERT",
                    "subject": f"Late Arrival Hold for Booking {hotel_booking_id}",
                    "message": f"Guest {passenger_name} arriving at {new_check_in} on {target_transport_id}."
                }
            }
        ]

    def execute_single_action(
        self,
        plan_id: str,
        action_spec: Dict[str, Any],
        max_retries: int = 2,
        timeout_ms: int = 2000,
        simulate_transient_failures: int = 0
    ) -> Dict[str, Any]:
        """
        Executes a single action with idempotency protection, timeout enforcement, and retry logic.
        Produces a standardized audit record.
        """
        action_type = str(action_spec.get("action_type", "")).lower()
        booking_id = str(action_spec.get("booking_id", "UNKNOWN"))
        req_payload = dict(action_spec.get("request") or {})
        explicit_key = action_spec.get("idempotency_key")
        idempotency_key = explicit_key or IdempotencyAndAuditStore.compute_key(plan_id, action_type, booking_id, req_payload)

        # 1. Check Idempotency Store
        cached = IdempotencyAndAuditStore.get_cached(idempotency_key)
        if cached is not None:
            replay_record = {
                **cached,
                "audit_id": f"AUD-{uuid.uuid4().hex[:8].upper()}",
                "timestamp": datetime.now(UTC).isoformat(),
                "idempotent_replay": True,
                "status": "IDEMPOTENT_REPLAY_SKIPPED_DUPLICATE"
            }
            IdempotencyAndAuditStore.record_audit(replay_record)
            return replay_record

        # 2. Execute with retries & timeout handling
        attempts = 0
        last_error: Optional[str] = None
        response_data: Dict[str, Any] = {}
        remaining_transient = simulate_transient_failures

        while attempts <= max_retries:
            attempts += 1
            try:
                # Check if requested simulated latency exceeds action timeout_ms budget
                sim_lat = req_payload.get("simulate_latency_ms")
                if sim_lat is not None and int(sim_lat) > timeout_ms:
                    raise SupplierAdapterException(
                        message=f"[MOCK API] Action timed out: simulated latency ({sim_lat}ms) exceeded timeout budget ({timeout_ms}ms).",
                        status_code=504,
                        error_code="ACTION_EXECUTION_TIMEOUT"
                    )

                # Inject transient failure on early attempt if requested for testing retry recovery
                call_payload = dict(req_payload)
                if remaining_transient > 0:
                    remaining_transient -= 1
                    call_payload["simulate_failure"] = "timeout"

                response_data = self._dispatch_to_supplier(action_type, call_payload)

                audit_record = {
                    "audit_id": f"AUD-{uuid.uuid4().hex[:8].upper()}",
                    "plan_id": plan_id,
                    "idempotency_key": idempotency_key,
                    "step": action_spec.get("step", 1),
                    "action_type": action_type,
                    "booking_id": booking_id,
                    "status": "SUCCESS",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "attempts": attempts,
                    "idempotent_replay": False,
                    "simulated": True,
                    "is_mock_supplier_transaction": True,
                    "disclaimer": MOCK_TRANSACTION_DISCLAIMER,
                    "request": req_payload,
                    "response": response_data,
                    "error": None
                }
                IdempotencyAndAuditStore.save_successful_action(idempotency_key, audit_record)
                IdempotencyAndAuditStore.record_audit(audit_record)
                return audit_record

            except SupplierAdapterException as exc:
                last_error = f"{exc.error_code}: {exc.message}"
                # Non-retryable client/inventory errors (e.g., 404 Not Found or 409 Insufficient Seats) break immediately
                if exc.status_code in (400, 404, 409) and "TIMEOUT" not in exc.error_code:
                    break
            except Exception as exc:
                last_error = str(exc)

        failed_record = {
            "audit_id": f"AUD-{uuid.uuid4().hex[:8].upper()}",
            "plan_id": plan_id,
            "idempotency_key": idempotency_key,
            "step": action_spec.get("step", 1),
            "action_type": action_type,
            "booking_id": booking_id,
            "status": "FAILED",
            "timestamp": datetime.now(UTC).isoformat(),
            "attempts": attempts,
            "idempotent_replay": False,
            "simulated": True,
            "is_mock_supplier_transaction": True,
            "disclaimer": MOCK_TRANSACTION_DISCLAIMER,
            "request": req_payload,
            "response": {},
            "error": last_error
        }
        IdempotencyAndAuditStore.record_audit(failed_record)
        return failed_record

    def execute_recovery_plan(
        self,
        plan_input: Dict[str, Any],
        max_retries: int = 2,
        timeout_ms: int = 2000,
        rollback_on_critical_failure: bool = True,
        simulate_transient_failures_on_step: Optional[int] = None,
        simulate_transient_count: int = 1
    ) -> Dict[str, Any]:
        """
        Executes a full sequence of actions compiled from a Recovery Plan.
        Handles:
        - Idempotency across all steps
        - Retries on transient supplier errors
        - Compensating Rollback if a critical step (e.g. rebook_transportation) fails after cancel_booking succeeded
        - Partial Success if a non-critical step fails while core bookings succeeded
        """
        plan_id = str(plan_input.get("plan_id") or "PLAN-DEFAULT-101")
        compiled_actions = self.compile_plan_to_actions(plan_input)

        executed_records: List[Dict[str, Any]] = []
        rollback_records: List[Dict[str, Any]] = []
        failed_steps: List[Dict[str, Any]] = []
        critical_failure_occurred = False

        for idx, act_spec in enumerate(compiled_actions, start=1):
            step_num = act_spec.get("step", idx)
            transient_count = simulate_transient_count if (simulate_transient_failures_on_step == step_num) else 0

            record = self.execute_single_action(
                plan_id=plan_id,
                action_spec=act_spec,
                max_retries=max_retries,
                timeout_ms=timeout_ms,
                simulate_transient_failures=transient_count
            )
            executed_records.append(record)

            if record["status"] == "FAILED":
                failed_steps.append(record)
                is_critical = bool(act_spec.get("critical", act_spec.get("action_type") in ("cancel_booking", "rebook_transportation")))
                if is_critical:
                    critical_failure_occurred = True
                    if rollback_on_critical_failure:
                        rollback_records = self._perform_rollback(plan_id, executed_records)
                    break

        # Determine overall execution status
        if critical_failure_occurred:
            overall_status = "ROLLED_BACK" if rollback_records else "FAILED"
        elif len(failed_steps) > 0:
            overall_status = "PARTIAL_SUCCESS"
        elif all(r["status"] == "IDEMPOTENT_REPLAY_SKIPPED_DUPLICATE" for r in executed_records):
            overall_status = "IDEMPOTENT_REPLAY_NO_OP"
        else:
            overall_status = "COMPLETED_SUCCESS"

        summary = {
            "plan_id": plan_id,
            "execution_status": overall_status,
            "total_actions": len(compiled_actions),
            "succeeded_count": sum(1 for r in executed_records if r["status"] in ("SUCCESS", "IDEMPOTENT_REPLAY_SKIPPED_DUPLICATE")),
            "failed_count": len(failed_steps),
            "idempotent_replays": sum(1 for r in executed_records if r.get("idempotent_replay")),
            "rolled_back_count": len(rollback_records),
            "audit_records": executed_records,
            "rollback_records": rollback_records,
            "failed_action_recovery_queue": [
                {"step": f["step"], "action_type": f["action_type"], "booking_id": f["booking_id"], "error": f["error"]}
                for f in failed_steps
            ],
            "simulated": True,
            "is_mock_supplier_transaction": True,
            "disclaimer": MOCK_TRANSACTION_DISCLAIMER
        }

        event_bus.publish("RECOVERY_PLAN_EXECUTION_FINISHED", {
            "plan_id": plan_id,
            "execution_status": overall_status,
            "succeeded_count": summary["succeeded_count"],
            "failed_count": summary["failed_count"],
            "rolled_back_count": len(rollback_records),
            "simulated": True
        })

        return summary

    def _perform_rollback(self, plan_id: str, executed_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executes compensating rollback actions for prior steps that succeeded before a critical failure.
        For example, if 'cancel_booking' succeeded in Step 1 and 'rebook_transportation' failed in Step 2,
        reinstates/rebooks the original transport so the traveler is not left stranded without a ticket.
        """
        rollbacks: List[Dict[str, Any]] = []
        for rec in reversed(executed_records):
            if rec["status"] != "SUCCESS":
                continue

            if rec["action_type"] == "cancel_booking":
                orig_req = rec["request"]
                orig_tid = orig_req.get("transport_id", "TRN123")
                rb_resp = supplier_service.rebook_booking({
                    "original_booking_ref": rec["booking_id"],
                    "transport_id": orig_tid,
                    "passenger_name": "Sahil Sharma (Rollback Reinstatement)",
                    "seats": 1,
                    "reason": "COMPENSATING_ROLLBACK_REINSTATEMENT",
                    "waive_change_fee": True
                })
                rb_audit = {
                    "audit_id": f"AUD-RB-{uuid.uuid4().hex[:6].upper()}",
                    "plan_id": plan_id,
                    "idempotency_key": f"RB-{rec['idempotency_key']}",
                    "step": rec["step"],
                    "action_type": "rollback_reinstate_booking",
                    "booking_id": rec["booking_id"],
                    "status": "ROLLED_BACK",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "attempts": 1,
                    "idempotent_replay": False,
                    "simulated": True,
                    "is_mock_supplier_transaction": True,
                    "disclaimer": MOCK_TRANSACTION_DISCLAIMER,
                    "request": {"reinstated_transport_id": orig_tid, "original_booking_id": rec["booking_id"]},
                    "response": rb_resp,
                    "error": None
                }
                rec["status"] = "ROLLED_BACK"
                IdempotencyAndAuditStore._idempotency_cache.pop(rec["idempotency_key"], None)
                IdempotencyAndAuditStore.record_audit(rb_audit)
                rollbacks.append(rb_audit)

            elif rec["action_type"] == "rebook_transportation":
                new_pnr = rec["response"].get("confirmation_number", rec["booking_id"])
                rb_resp = supplier_service.cancel_booking({
                    "booking_reference": new_pnr,
                    "transport_id": rec["booking_id"],
                    "reason": "COMPENSATING_ROLLBACK_CANCELLATION"
                })
                rb_audit = {
                    "audit_id": f"AUD-RB-{uuid.uuid4().hex[:6].upper()}",
                    "plan_id": plan_id,
                    "idempotency_key": f"RB-{rec['idempotency_key']}",
                    "step": rec["step"],
                    "action_type": "rollback_cancel_rebooking",
                    "booking_id": new_pnr,
                    "status": "ROLLED_BACK",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "attempts": 1,
                    "idempotent_replay": False,
                    "simulated": True,
                    "is_mock_supplier_transaction": True,
                    "disclaimer": MOCK_TRANSACTION_DISCLAIMER,
                    "request": {"cancelled_confirmation": new_pnr},
                    "response": rb_resp,
                    "error": None
                }
                rec["status"] = "ROLLED_BACK"
                IdempotencyAndAuditStore._idempotency_cache.pop(rec["idempotency_key"], None)
                IdempotencyAndAuditStore.record_audit(rb_audit)
                rollbacks.append(rb_audit)

        return rollbacks

    @staticmethod
    def _dispatch_to_supplier(action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if action_type in ("rebook_transportation", "rebook_transport", "rebook"):
            return supplier_service.rebook_booking(payload)
        elif action_type in ("cancel_booking", "cancel"):
            return supplier_service.cancel_booking(payload)
        elif action_type in ("request_refund", "claim_refund", "refund"):
            return supplier_service.request_refund(payload)
        elif action_type in ("modify_hotel_checkin", "modify_hotel", "hotel_modify"):
            return supplier_service.modify_hotel(payload)
        elif action_type in ("notify_traveler", "notify_relevant_contact"):
            # Simulated notification dispatch with optional failure simulation
            sim_fail = payload.get("simulate_failure")
            if sim_fail == "timeout":
                raise SupplierAdapterException(
                    message="[MOCK API] Notification gateway timed out.",
                    status_code=504,
                    error_code="MOCK_NOTIFICATION_TIMEOUT"
                )
            elif sim_fail == "service_unavailable":
                raise SupplierAdapterException(
                    message="[MOCK API] Notification dispatch service unavailable.",
                    status_code=503,
                    error_code="MOCK_NOTIFICATION_UNAVAILABLE"
                )
            return {
                "notification_id": f"NTF-{uuid.uuid4().hex[:8].upper()}",
                "recipient": payload.get("recipient", "traveler@example.com"),
                "channel": payload.get("channel", "EMAIL"),
                "subject": payload.get("subject", "Disruption Recovery Update"),
                "message": payload.get("message", ""),
                "delivery_status": "DELIVERED_SIMULATED",
                "sent_at": datetime.now(UTC).isoformat(),
                "simulated": True,
                "is_mock_api": True
            }
        else:
            raise ValueError(f"Unsupported recovery action_type: '{action_type}'")


recovery_action_executor = RecoveryActionExecutor()
