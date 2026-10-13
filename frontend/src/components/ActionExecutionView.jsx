import React, { useState, useEffect } from 'react';
import {
  Play,
  RotateCcw,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Copy,
  RefreshCw,
  AlertTriangle,
  History,
  Undo2,
  Clock
} from 'lucide-react';
import { apiService } from '../services/api';

export function ActionExecutionView() {
  const [planId, setPlanId] = useState('PLAN-TRN-456');
  const [originalBookingId, setOriginalBookingId] = useState('12015-SHT');
  const [newTransportId, setNewTransportId] = useState('TRN124');
  const [hotelBookingId, setHotelBookingId] = useState('HTL-JAI-101');
  const [newCheckIn, setNewCheckIn] = useState('2026-10-20T22:30:00');

  const [lastExecutionSummary, setLastExecutionSummary] = useState(null);
  const [auditHistory, setAuditHistory] = useState([]);
  const [selectedAudit, setSelectedAudit] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadHistory = async () => {
    try {
      const res = await apiService.getActionHistory();
      setAuditHistory(res.history || []);
      if (res.history && res.history.length > 0 && !selectedAudit) {
        setSelectedAudit(res.history[0]);
      }
    } catch (err) {
      console.error('Error loading action history:', err);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleExecuteStandardPlan = async (customPayload = null) => {
    setLoading(true);
    try {
      const payload = customPayload || {
        plan_id: planId,
        original_booking_id: originalBookingId,
        original_transport_id: 'TRN123',
        original_price: 800,
        new_transport_id: newTransportId,
        passenger_name: 'Sahil Sharma',
        seats: 1,
        hotel_booking_id: hotelBookingId,
        hotel_id: 'HTL101',
        new_check_in: newCheckIn,
        max_retries: 2,
        timeout_ms: 2000,
        rollback_on_critical_failure: true,
      };
      const res = await apiService.executeRecoveryPlan(payload);
      setLastExecutionSummary(res);
      if (res.audit_records && res.audit_records.length > 0) {
        setSelectedAudit(res.audit_records[0]);
      }
      await loadHistory();
    } catch (err) {
      console.error('Execution error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateTransientRetry = () => {
    const newId = `PLAN-RETRY-${Math.floor(100 + Math.random() * 900)}`;
    setPlanId(newId);
    handleExecuteStandardPlan({
      plan_id: newId,
      original_booking_id: originalBookingId,
      original_transport_id: 'TRN123',
      new_transport_id: newTransportId,
      hotel_booking_id: hotelBookingId,
      new_check_in: newCheckIn,
      max_retries: 2,
      simulate_transient_failures_on_step: 2,
      simulate_transient_count: 1,
    });
  };

  const handleSimulatePartialSuccess = () => {
    const newId = `PLAN-PARTIAL-${Math.floor(100 + Math.random() * 900)}`;
    setPlanId(newId);
    handleExecuteStandardPlan({
      plan_id: newId,
      max_retries: 1,
      actions: [
        {
          step: 1,
          action_type: 'cancel_booking',
          booking_id: originalBookingId,
          critical: true,
          request: { booking_reference: originalBookingId, transport_id: 'TRN123', supplier_type: 'train', original_price: 800 },
        },
        {
          step: 2,
          action_type: 'rebook_transportation',
          booking_id: newTransportId,
          critical: true,
          request: { transport_id: newTransportId, passenger_name: 'Sahil Sharma', seats: 1, waive_change_fee: true },
        },
        {
          step: 3,
          action_type: 'request_refund',
          booking_id: originalBookingId,
          critical: FalseValue(),
          request: { booking_reference: originalBookingId, transport_id: 'TRN123', original_price: 800, is_disruption_waiver: true },
        },
        {
          step: 4,
          action_type: 'notify_relevant_contact',
          booking_id: hotelBookingId,
          critical: false,
          request: { recipient: 'frontdesk@hotel.com', simulate_failure: 'service_unavailable' },
        },
      ],
    });
  };

  function FalseValue() {
    return false;
  }

  const handleSimulateCriticalRollback = () => {
    const newId = `PLAN-ROLLBACK-${Math.floor(100 + Math.random() * 900)}`;
    setPlanId(newId);
    handleExecuteStandardPlan({
      plan_id: newId,
      rollback_on_critical_failure: true,
      actions: [
        {
          step: 1,
          action_type: 'cancel_booking',
          booking_id: originalBookingId,
          critical: true,
          request: { booking_reference: originalBookingId, transport_id: 'TRN123', supplier_type: 'train', original_price: 800 },
        },
        {
          step: 2,
          action_type: 'rebook_transportation',
          booking_id: newTransportId,
          critical: true,
          request: { transport_id: newTransportId, seats: 99 }, // Exceeds available seats -> triggers compensating rollback of Step 1!
        },
      ],
    });
  };

  const handleClearHistory = async () => {
    await apiService.clearActionHistory();
    await apiService.resetSupplierSimulation();
    setLastExecutionSummary(null);
    setSelectedAudit(null);
    await loadHistory();
  };

  return (
    <div className="space-y-6">
      {/* Header & Mock Disclaimer */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-teal-500/30 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-teal-500/20 text-teal-300 border border-teal-500/40">
                STAGE 8 &middot; AUTONOMOUS RECOVERY EXECUTION &amp; AUDIT LOG
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono bg-amber-500/15 text-amber-300 border border-amber-500/30">
                SIMULATED MOCK SUPPLIER TRANSACTIONS
              </span>
            </div>
            <h2 className="text-lg font-bold text-white mt-1.5">
              Idempotent Action Execution Layer &amp; Audit History
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Converts Recovery Plans into executable actions (<strong>Cancel, Rebook, Refund, Modify Hotel, Notify Traveler, Notify Contact</strong>) against our Mock Supplier APIs with strict idempotency keys, retries, timeout handling, partial success, and compensating rollbacks.
            </p>
          </div>

          <button
            onClick={handleClearHistory}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 flex items-center gap-1.5 cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5 text-teal-400" />
            Clear Audit Log &amp; Reset
          </button>
        </div>
      </div>

      {/* Action Controls & Test Scenarios */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Plan Parameters & 1-Click Scenario Triggers */}
        <div className="space-y-4">
          <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
            <div className="text-xs font-bold uppercase tracking-wider text-teal-400">
              Recovery Plan Parameters
            </div>

            <div className="space-y-2.5">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Plan ID (Idempotency Scope)</label>
                <input
                  type="text"
                  value={planId}
                  onChange={(e) => setPlanId(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Cancel Booking ID</label>
                  <input
                    type="text"
                    value={originalBookingId}
                    onChange={(e) => setOriginalBookingId(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Rebook Target ID</label>
                  <input
                    type="text"
                    value={newTransportId}
                    onChange={(e) => setNewTransportId(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono"
                  />
                </div>
              </div>
            </div>

            <div className="pt-2 space-y-2">
              <button
                onClick={() => handleExecuteStandardPlan()}
                disabled={loading}
                className="w-full py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold flex items-center justify-center gap-2 cursor-pointer shadow"
              >
                <Play className="w-3.5 h-3.5" />
                <span>1. Execute 6-Step Recovery Plan</span>
              </button>

              <button
                onClick={() => handleExecuteStandardPlan()}
                disabled={loading}
                className="w-full py-2 rounded-xl bg-indigo-600/80 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center gap-2 cursor-pointer"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>2. Re-Trigger Same Plan (Test Idempotency)</span>
              </button>

              <button
                onClick={handleSimulateTransientRetry}
                disabled={loading}
                className="w-full py-2 rounded-xl bg-sky-600/80 hover:bg-sky-500 text-white text-xs font-semibold flex items-center justify-center gap-2 cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>3. Simulate Timeout &amp; Auto-Retry (#2)</span>
              </button>

              <button
                onClick={handleSimulatePartialSuccess}
                disabled={loading}
                className="w-full py-2 rounded-xl bg-amber-600/80 hover:bg-amber-500 text-white text-xs font-semibold flex items-center justify-center gap-2 cursor-pointer"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>4. Simulate Partial Success Recovery</span>
              </button>

              <button
                onClick={handleSimulateCriticalRollback}
                disabled={loading}
                className="w-full py-2 rounded-xl bg-rose-600/80 hover:bg-rose-500 text-white text-xs font-semibold flex items-center justify-center gap-2 cursor-pointer"
              >
                <Undo2 className="w-3.5 h-3.5" />
                <span>5. Simulate Critical Failure &amp; Rollback</span>
              </button>
            </div>
          </div>

          {/* Selected Audit Record JSON Inspector */}
          {selectedAudit && (
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-teal-400">
                  Audit Record Inspector ({selectedAudit.audit_id})
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  {selectedAudit.action_type}
                </span>
              </div>
              <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[10px] text-slate-300 overflow-x-auto max-h-96 font-mono">
                {JSON.stringify(selectedAudit, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Right 2 Columns: Latest Plan Execution Summary + Complete Action Audit History */}
        <div className="lg:col-span-2 space-y-4">
          {lastExecutionSummary && (
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-700 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-teal-400" />
                  <span className="text-sm font-bold text-white">
                    Plan Execution Result: {lastExecutionSummary.plan_id}
                  </span>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-mono font-bold border ${
                    lastExecutionSummary.execution_status === 'COMPLETED_SUCCESS'
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                      : lastExecutionSummary.execution_status === 'IDEMPOTENT_REPLAY_NO_OP'
                      ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40'
                      : lastExecutionSummary.execution_status === 'PARTIAL_SUCCESS'
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                      : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                  }`}
                >
                  {lastExecutionSummary.execution_status}
                </span>
              </div>

              <div className="grid grid-cols-4 gap-3 text-center text-xs">
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="text-slate-400 text-[10px]">Succeeded</div>
                  <div className="text-base font-bold text-emerald-400">{lastExecutionSummary.succeeded_count}</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="text-slate-400 text-[10px]">Idempotent Replays</div>
                  <div className="text-base font-bold text-indigo-400">{lastExecutionSummary.idempotent_replays}</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="text-slate-400 text-[10px]">Failed Actions</div>
                  <div className="text-base font-bold text-amber-400">{lastExecutionSummary.failed_count}</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="text-slate-400 text-[10px]">Rolled Back</div>
                  <div className="text-base font-bold text-rose-400">{lastExecutionSummary.rolled_back_count}</div>
                </div>
              </div>
            </div>
          )}

          {/* Action Audit History List */}
          <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300">
                <History className="w-4 h-4 text-teal-400" />
                Action Execution Audit History ({auditHistory.length} records)
              </div>
              <span className="text-[11px] text-slate-500">Click any audit row to inspect request/response JSON</span>
            </div>

            {auditHistory.length > 0 ? (
              <div className="space-y-2">
                {auditHistory.map((rec) => (
                  <div
                    key={rec.audit_id}
                    onClick={() => setSelectedAudit(rec)}
                    className={`p-3.5 rounded-xl border transition cursor-pointer flex flex-wrap items-center justify-between gap-2 text-xs ${
                      selectedAudit?.audit_id === rec.audit_id
                        ? 'bg-slate-800/90 border-teal-500/50'
                        : 'bg-slate-950/80 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-800 text-teal-300 font-bold">
                          {rec.action_type}
                        </span>
                        <span className="font-semibold text-white">Booking: {rec.booking_id}</span>
                        <span className="font-mono text-[10px] text-slate-400">Plan: {rec.plan_id}</span>
                        {rec.attempts > 1 && (
                          <span className="px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 font-mono text-[10px]">
                            Attempts: {rec.attempts}
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        Idempotency Key: {rec.idempotency_key} &middot; {rec.timestamp}
                      </div>
                      {rec.error && (
                        <div className="text-[11px] text-rose-400 font-medium">Error: {rec.error}</div>
                      )}
                    </div>

                    <span
                      className={`px-2.5 py-1 rounded-full font-mono text-[10px] font-bold border ${
                        rec.status === 'SUCCESS'
                          ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                          : rec.status === 'IDEMPOTENT_REPLAY_SKIPPED_DUPLICATE'
                          ? 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30'
                          : rec.status === 'ROLLED_BACK'
                          ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                          : 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                      }`}
                    >
                      {rec.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                No recovery actions executed yet. Click <strong>"1. Execute 6-Step Recovery Plan"</strong> to run a recovery plan against the Mock Supplier APIs.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
