import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
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
  Clock,
  Terminal,
  Zap
} from 'lucide-react';
import { apiService } from '../services/api';
import { CountUpNumber } from './ui/SaaSPrimitives';

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
    <div className="space-y-4">
      {/* Header & Mock Disclaimer */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="p-3.5 sm:p-4 rounded-xl bg-surface-container-low/90 backdrop-blur-2xl border border-surface-container-high shadow-glass-card space-y-2 relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="flex flex-wrap items-center justify-between gap-3 relative z-10">
          <div>
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-teal-500/20 text-teal-300 border border-teal-500/40 font-mono shadow-[0_0_8px_rgba(20,184,166,0.15)]">
                STAGE 8 &middot; AUTONOMOUS RECOVERY EXECUTION &amp; AUDIT LOG
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-amber-500/15 text-amber-300 border border-amber-500/30">
                SIMULATED MOCK SUPPLIER TRANSACTIONS
              </span>
            </div>
            <h2 className="text-lg sm:text-xl font-bold text-white mt-1 tracking-tight font-display">
              Idempotent Action Execution Layer &amp; Audit History
            </h2>
            <p className="text-xs text-on-surface-variant mt-0.5 max-w-3xl leading-relaxed font-sans">
              Converts Recovery Plans into executable actions (<strong className="text-slate-200">Cancel, Rebook, Refund, Modify Hotel, Notify Traveler, Notify Contact</strong>) against our Mock Supplier APIs with strict idempotency keys, retries, timeout handling, partial success, and compensating rollbacks.
            </p>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleClearHistory}
            className="px-3 py-1.5 rounded-lg bg-[#0d1527] hover:bg-[#131f38] text-xs font-semibold text-slate-200 border border-surface-container-high hover:border-teal-500/40 flex items-center gap-1.5 cursor-pointer transition shadow-sm h-8"
          >
            <RotateCcw className="w-3.5 h-3.5 text-teal-400" />
            <span>Clear Audit Log &amp; Reset</span>
          </motion.button>
        </div>
      </motion.div>

      {/* Action Controls & Test Scenarios */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left Column: Plan Parameters & 1-Click Scenario Triggers */}
        <div className="space-y-3.5">
          <motion.div
            initial={{ opacity: 0, x: -15 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="p-3.5 rounded-xl bg-surface-container-low/90 backdrop-blur-2xl border border-surface-container-high shadow-glass-card space-y-3"
          >
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-teal-400 font-mono">
              <Terminal className="w-3.5 h-3.5 text-teal-400" />
              <span>Recovery Plan Parameters</span>
            </div>

            <div className="space-y-2.5">
              <div>
                <label className="block text-[10px] font-semibold text-on-surface-variant mb-1 font-sans">
                  Plan ID (Idempotency Scope)
                </label>
                <input
                  type="text"
                  value={planId}
                  onChange={(e) => setPlanId(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white font-mono focus:outline-none focus:border-teal-500/50 transition h-8"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[10px] font-semibold text-on-surface-variant mb-1 font-sans">
                    Cancel Booking ID
                  </label>
                  <input
                    type="text"
                    value={originalBookingId}
                    onChange={(e) => setOriginalBookingId(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white font-mono focus:outline-none focus:border-teal-500/50 transition h-8"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-semibold text-on-surface-variant mb-1 font-sans">
                    Rebook Target ID
                  </label>
                  <input
                    type="text"
                    value={newTransportId}
                    onChange={(e) => setNewTransportId(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-xs text-white font-mono focus:outline-none focus:border-teal-500/50 transition h-8"
                  />
                </div>
              </div>
            </div>

            <div className="pt-1 space-y-1.5">
              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={() => handleExecuteStandardPlan()}
                disabled={loading}
                className="w-full h-8 py-1.5 rounded-lg bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 text-white text-xs font-bold flex items-center justify-center gap-1.5 cursor-pointer shadow-[0_0_12px_rgba(20,184,166,0.2)] transition font-display disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                <span>1. Execute 6-Step Recovery Plan</span>
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={() => handleExecuteStandardPlan()}
                disabled={loading}
                className="w-full h-8 py-1.5 rounded-lg bg-indigo-600/80 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer transition shadow-sm font-sans disabled:opacity-50"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>2. Re-Trigger Same Plan (Idempotency)</span>
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={handleSimulateTransientRetry}
                disabled={loading}
                className="w-full h-8 py-1.5 rounded-lg bg-sky-600/80 hover:bg-sky-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer transition shadow-sm font-sans disabled:opacity-50"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>3. Simulate Timeout &amp; Auto-Retry (#2)</span>
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={handleSimulatePartialSuccess}
                disabled={loading}
                className="w-full h-8 py-1.5 rounded-lg bg-amber-600/80 hover:bg-amber-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer transition shadow-sm font-sans disabled:opacity-50"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>4. Simulate Partial Success Recovery</span>
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={handleSimulateCriticalRollback}
                disabled={loading}
                className="w-full h-8 py-1.5 rounded-lg bg-rose-600/80 hover:bg-rose-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer transition shadow-sm font-sans disabled:opacity-50"
              >
                <Undo2 className="w-3.5 h-3.5" />
                <span>5. Simulate Critical Failure &amp; Rollback</span>
              </motion.button>
            </div>
          </motion.div>

          {/* Selected Audit Record JSON Inspector */}
          {selectedAudit && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3.5 rounded-xl bg-surface-container-low/90 backdrop-blur-2xl border border-surface-container-high shadow-glass-card space-y-2.5"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-teal-400 font-mono">
                  Audit Record Inspector ({selectedAudit.audit_id})
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/[0.06] border border-surface-container-high text-teal-300 font-bold">
                  {selectedAudit.action_type}
                </span>
              </div>
              <pre className="p-2.5 rounded-lg bg-surface-container-lowest border border-surface-container-high text-[10px] text-slate-300 overflow-x-auto max-h-72 font-mono leading-relaxed">
                {JSON.stringify(selectedAudit, null, 2)}
              </pre>
            </motion.div>
          )}
        </div>

        {/* Right 2 Columns: Latest Plan Execution Summary + Complete Action Audit History */}
        <div className="lg:col-span-2 space-y-3.5">
          {lastExecutionSummary && (
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3.5 sm:p-4 rounded-xl bg-surface-container-low/90 backdrop-blur-2xl border border-surface-container-high shadow-glass-card space-y-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-teal-500/15 border border-teal-500/30 text-teal-400">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-[10px] font-mono uppercase text-on-surface-variant">Execution Result</div>
                    <span className="text-xs sm:text-sm font-bold text-white font-display">
                      Plan ID: {lastExecutionSummary.plan_id}
                    </span>
                  </div>
                </div>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold border ${
                    lastExecutionSummary.execution_status === 'COMPLETED_SUCCESS'
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-[0_0_8px_rgba(16,185,129,0.15)]'
                      : lastExecutionSummary.execution_status === 'IDEMPOTENT_REPLAY_NO_OP'
                      ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40 shadow-[0_0_8px_rgba(99,102,241,0.15)]'
                      : lastExecutionSummary.execution_status === 'PARTIAL_SUCCESS'
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-[0_0_8px_rgba(245,158,11,0.15)]'
                      : 'bg-rose-500/20 text-rose-300 border-rose-500/40 shadow-[0_0_8px_rgba(244,63,94,0.15)]'
                  }`}
                >
                  {lastExecutionSummary.execution_status}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                <div className="p-2.5 rounded-xl bg-surface-container-lowest border border-surface-container-high">
                  <div className="text-on-surface-variant text-[10px] font-sans">Succeeded</div>
                  <div className="text-base sm:text-lg font-bold text-emerald-400 font-display mt-0.5">
                    <CountUpNumber end={lastExecutionSummary.succeeded_count} duration={0.8} />
                  </div>
                </div>
                <div className="p-2.5 rounded-xl bg-surface-container-lowest border border-surface-container-high">
                  <div className="text-on-surface-variant text-[10px] font-sans">Idempotent Replays</div>
                  <div className="text-base sm:text-lg font-bold text-indigo-400 font-display mt-0.5">
                    <CountUpNumber end={lastExecutionSummary.idempotent_replays} duration={0.8} />
                  </div>
                </div>
                <div className="p-2.5 rounded-xl bg-surface-container-lowest border border-surface-container-high">
                  <div className="text-on-surface-variant text-[10px] font-sans">Failed Actions</div>
                  <div className="text-base sm:text-lg font-bold text-amber-400 font-display mt-0.5">
                    <CountUpNumber end={lastExecutionSummary.failed_count} duration={0.8} />
                  </div>
                </div>
                <div className="p-2.5 rounded-xl bg-surface-container-lowest border border-surface-container-high">
                  <div className="text-on-surface-variant text-[10px] font-sans">Rolled Back</div>
                  <div className="text-base sm:text-lg font-bold text-rose-400 font-display mt-0.5">
                    <CountUpNumber end={lastExecutionSummary.rolled_back_count} duration={0.8} />
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Action Audit History List */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.15 }}
            className="p-3.5 sm:p-4 rounded-xl bg-surface-container-low/90 backdrop-blur-2xl border border-surface-container-high shadow-glass-card space-y-3"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-surface-container-high pb-2.5">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
                <History className="w-3.5 h-3.5 text-teal-400" />
                <span>Action Execution Audit History ({auditHistory.length} records)</span>
              </div>
              <span className="text-[10px] text-on-surface-variant font-sans">Click audit row to inspect JSON</span>
            </div>

            {auditHistory.length > 0 ? (
              <div className="space-y-2 max-h-[460px] overflow-y-auto pr-1">
                {auditHistory.map((rec, i) => (
                  <motion.div
                    key={rec.audit_id || i}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.25, delay: i * 0.03 }}
                    onClick={() => setSelectedAudit(rec)}
                    className={`p-3 rounded-xl border transition cursor-pointer flex flex-wrap items-center justify-between gap-2 text-xs ${
                      selectedAudit?.audit_id === rec.audit_id
                        ? 'bg-[#0e172e] border-teal-500/50 shadow-[0_0_12px_rgba(20,184,166,0.12)]'
                        : 'bg-surface-container-lowest border-surface-container-high/60 hover:border-white/[0.15] hover:bg-surface-container-low'
                    }`}
                  >
                    <div className="space-y-0.5">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-300 font-bold border border-teal-500/30">
                          {rec.action_type}
                        </span>
                        <span className="font-semibold text-white font-display text-xs">Booking: {rec.booking_id}</span>
                        <span className="font-mono text-[10px] text-on-surface-variant">Plan: {rec.plan_id}</span>
                        {rec.attempts > 1 && (
                          <span className="px-1.5 py-0.5 rounded-full bg-sky-500/20 text-sky-300 font-mono text-[9px] border border-sky-500/30">
                            Attempts: {rec.attempts}
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-on-surface-variant font-mono">
                        Idempotency Key: {rec.idempotency_key} &middot; {rec.timestamp}
                      </div>
                      {rec.error && (
                        <div className="text-[10px] text-rose-400 font-medium">Error: {rec.error}</div>
                      )}
                    </div>

                    <span
                      className={`px-2.5 py-0.5 rounded-full font-mono text-[10px] font-bold border ${
                        rec.status === 'SUCCESS'
                          ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30 shadow-[0_0_6px_rgba(16,185,129,0.12)]'
                          : rec.status === 'IDEMPOTENT_REPLAY_SKIPPED_DUPLICATE'
                          ? 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30 shadow-[0_0_6px_rgba(99,102,241,0.12)]'
                          : rec.status === 'ROLLED_BACK'
                          ? 'bg-amber-500/15 text-amber-300 border-amber-500/30 shadow-[0_0_6px_rgba(245,158,11,0.12)]'
                          : 'bg-rose-500/15 text-rose-300 border-rose-500/30 shadow-[0_0_6px_rgba(244,63,94,0.12)]'
                      }`}
                    >
                      {rec.status}
                    </span>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-outline font-sans">
                No recovery actions executed yet. Click <strong className="text-teal-400">"1. Execute 6-Step Recovery Plan"</strong> to run a recovery plan against the Mock Supplier APIs.
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
}
