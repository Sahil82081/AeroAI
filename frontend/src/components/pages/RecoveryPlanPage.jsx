import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  Cpu,
  CheckCircle2,
  XCircle,
  Sparkles,
  Play,
  ArrowRight,
  Workflow,
  ShieldCheck,
  FileText,
  HelpCircle,
  Layers,
  Clock,
  Check
} from 'lucide-react';
import { OptimizationView } from '../OptimizationView';
import { LangGraphAgentView } from '../LangGraphAgentView';
import { ConfirmDialog } from '../ui/SaaSPrimitives';
import { RejectionDialog } from '../RejectionDialog';
import { api } from '../../services/api';

export function RecoveryPlanPage({
  onExecuteRecoveryActions,
  onRejectPlan = null,
  executingActions = false,
  actionExecutionResult = null,
}) {
  const [subView, setSubView] = useState('overview');
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [rejectToast, setRejectToast] = useState(false);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [revising, setRevising] = useState(false);
  const [revisionFeedbackInfo, setRevisionFeedbackInfo] = useState(null);

  const alternativesList = [
    {
      id: 'TRN-A (12015-E)',
      mode: 'Train',
      departure: '16:15 IST',
      arrival: '19:45 IST',
      price: 'INR 500',
      seats: 12,
      feasible: false,
      reason: 'Violates 30-min minimum transfer buffer after 16:00 flight arrival (only 15m gap)',
    },
    {
      id: 'TRN124 (Ashram Exp 12916)',
      mode: 'Train',
      departure: '17:30 IST',
      arrival: '21:00 IST',
      price: 'INR 750',
      seats: 18,
      feasible: true,
      selected: true,
      score: 18.4,
      reason: 'Optimal CP-SAT choice: 90m transfer buffer + arrives 60m before 22:00 hotel cutoff',
    },
    {
      id: 'TRN-C (Chetak Exp 20473)',
      mode: 'Train',
      departure: '19:00 IST',
      arrival: '22:30 IST',
      price: 'INR 400',
      seats: 24,
      feasible: false,
      reason: 'Arrives 22:30 — violates Rambagh Palace Hotel 22:00 latest check-in constraint',
    },
    {
      id: 'BUS-RSRTC-VOLVO-02',
      mode: 'Bus',
      departure: '17:00 IST',
      arrival: '21:45 IST',
      price: 'INR 950',
      seats: 9,
      feasible: true,
      selected: false,
      score: 34.2,
      reason: 'Feasible backup, but longer transit duration (285m) and lower reliability (0.86)',
    },
    {
      id: 'FLT-6E-912',
      mode: 'Flight',
      departure: '18:15 IST',
      arrival: '19:15 IST',
      price: 'INR 4,200',
      seats: 4,
      feasible: true,
      selected: false,
      score: 41.0,
      reason: 'Feasible, but high cost penalty (INR 4,200 vs INR 750 rail alternative)',
    },
  ];

  const actionsList = actionExecutionResult?.audit_records || [
    {
      step: 1,
      action_type: 'cancel_booking',
      booking_id: '12015-SHT (TRN123)',
      description: 'Cancel missed 13:30 Delhi → Jaipur train reservation & release seat',
      status: 'SUCCESS',
    },
    {
      step: 2,
      action_type: 'rebook_transportation',
      booking_id: 'TRN124 (Ashram Express 12916)',
      description: 'Confirm seat on 17:30 Delhi → Jaipur train (Arrives 21:00, INR 750)',
      status: 'SUCCESS',
    },
    {
      step: 3,
      action_type: 'request_refund',
      booking_id: '12015-SHT (INR 600.00)',
      description: 'Submit involuntary missed-connection refund claim under IRCTC-INV-DELAY-75PCT',
      status: 'SUCCESS',
    },
    {
      step: 4,
      action_type: 'modify_hotel_checkin',
      booking_id: 'HTL-JAI-101 (Rambagh Palace)',
      description: 'Update guest check-in from 18:00 to 21:30 prior to 22:00 cutoff',
      status: 'SUCCESS',
    },
    {
      step: 5,
      action_type: 'notify_traveler',
      booking_id: 'Aarav Sharma <aarav.sharma@example.com>',
      description: 'Dispatch grounded recovery itinerary & PNR confirmation email',
      status: 'SUCCESS',
    },
    {
      step: 6,
      action_type: 'notify_relevant_contact',
      booking_id: 'Rambagh Palace Front Desk & Emergency Contact',
      description: 'Dispatch late check-in hold & family schedule reassurance',
      status: 'SUCCESS',
    },
  ];

  return (
    <div className="space-y-4">
      {/* Sub-navigation bar */}
      <div className="rounded-xl border border-surface-container-high bg-surface-container-low/90 p-2.5 sm:p-3 flex flex-col lg:flex-row lg:items-center justify-between gap-2.5 backdrop-blur-md shadow-sm">
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setSubView('overview')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer font-display h-8 ${
              subView === 'overview'
                ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white shadow-sm'
                : 'bg-surface-container-lowest text-on-surface-variant hover:text-white border border-surface-container-high'
            }`}
          >
            8-Panel Recovery Command Summary
          </button>
          <button
            onClick={() => setSubView('ortools')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer font-display h-8 ${
              subView === 'ortools'
                ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-sm'
                : 'bg-surface-container-lowest text-on-surface-variant hover:text-white border border-surface-container-high'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Interactive OR-Tools Optimizer</span>
          </button>
          <button
            onClick={() => setSubView('langgraph')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer font-display h-8 ${
              subView === 'langgraph'
                ? 'bg-gradient-to-r from-indigo-600 to-sky-600 text-white shadow-sm'
                : 'bg-surface-container-lowest text-on-surface-variant hover:text-white border border-surface-container-high'
            }`}
          >
            <Workflow className="w-3.5 h-3.5" />
            <span>LangGraph 8-Node Agent Workflow</span>
          </button>
        </div>

        <div className="flex items-center gap-2 self-start lg:self-auto w-full lg:w-auto justify-end">
          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setRejectModalOpen(true)}
            disabled={executingActions || revising}
            className="flex-1 lg:flex-initial px-3.5 py-1.5 rounded-lg border border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-xs font-bold flex items-center justify-center gap-1.5 shadow-sm transition cursor-pointer font-display h-8"
            title="Reject proposed plan and trigger replanning"
          >
            <XCircle className="w-3.5 h-3.5 text-amber-400" />
            <span>{revising ? 'Replanning...' : 'Reject & Revise'}</span>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setConfirmModalOpen(true)}
            disabled={executingActions || revising}
            className="flex-1 lg:flex-initial px-4 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold flex items-center justify-center gap-1.5 shadow-sm transition cursor-pointer font-display h-8"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>
              {executingActions ? 'Executing Actions...' : 'Approve & Execute'}
            </span>
          </motion.button>
        </div>
      </div>

      {rejectToast && (
        <div className="rounded-lg border border-amber-500/40 bg-amber-950/40 p-3 text-xs text-amber-200 flex flex-col gap-1.5 font-display">
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-amber-400 shrink-0" />
            <span className="font-bold">
              Recovery Plan Rejected &amp; Replanned with Constraints (Rev {revisionFeedbackInfo?.revisionCount || 2})
            </span>
          </div>
          <span className="text-slate-300 font-sans">
            Feedback interpreted into planning constraints. Human approval gate has strictly blocked execution until the revised plan is reviewed and approved.
          </span>
          {revisionFeedbackInfo?.activeConstraints?.descriptions?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {revisionFeedbackInfo.activeConstraints.descriptions.map((d, i) => (
                <span key={i} className="px-2 py-0.5 rounded bg-sky-500/20 border border-sky-500/40 text-sky-300 font-mono text-[10px]">
                  ✓ {d}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      <RejectionDialog
        open={rejectModalOpen}
        onClose={() => setRejectModalOpen(false)}
        onSubmit={async ({ reasons, feedbackText }) => {
          setRevising(true);
          try {
            if (onRejectPlan) {
              await onRejectPlan({ reasons, feedbackText });
            } else {
              const res = await api.rejectAndReplanLiveWorkspaceRecovery({
                reasons,
                feedback_text: feedbackText,
              });
              setRevisionFeedbackInfo({
                reasons,
                feedbackText,
                revisionCount: res?.proposed_plan?.revision_count || 2,
                activeConstraints: res?.proposed_plan?.active_constraints,
                summary: res?.proposed_plan?.summary,
              });
            }
            setRejectToast(true);
            setTimeout(() => setRejectToast(false), 8000);
          } catch {
            setRejectToast(true);
          } finally {
            setRevising(false);
            setRejectModalOpen(false);
          }
        }}
        revisionCount={revisionFeedbackInfo?.revisionCount || 1}
        maxRevisions={3}
        previousConstraints={revisionFeedbackInfo?.activeConstraints}
        submitting={revising}
      />

      <ConfirmDialog
        open={confirmModalOpen}
        title="Confirm Plan Approval & Autonomous Execution"
        description="This action marks the recovery plan as APPROVED in accordance with the Human Approval Gate, and authorizes execution of the 6 recovery actions against the Mock Supplier APIs with strict idempotency protection."
        confirmLabel="Approve & Execute"
        onCancel={() => setConfirmModalOpen(false)}
        onConfirm={() => {
          setConfirmModalOpen(false);
          if (onExecuteRecoveryActions) onExecuteRecoveryActions();
        }}
      />

      {subView === 'ortools' ? (
        <OptimizationView />
      ) : subView === 'langgraph' ? (
        <LangGraphAgentView />
      ) : (
        <div className="space-y-3.5">
          {/* Row 1: 1. Problem & 2. Impact */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
            {/* 1. PROBLEM */}
            <div className="rounded-xl border border-rose-500/30 bg-surface-container-low/90 p-4 sm:p-4.5 space-y-2.5 backdrop-blur-md shadow-sm relative overflow-hidden">
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-rose-500/40 to-transparent pointer-events-none" />
              
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase bg-rose-500/15 text-rose-300 border border-rose-500/30">
                  1. Problem
                </span>
                <span className="text-[11px] font-mono text-rose-400 font-bold">
                  DISR-AI202-240M &middot; CRITICAL
                </span>
              </div>
              <h3 className="text-sm sm:text-base font-bold text-white font-display">
                Air India Flight AI-202 Delayed +240 Minutes (Mumbai &rarr; Delhi)
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                Inbound flight <strong>AI-202</strong> scheduled to land at New Delhi (DEL) at <strong>12:00 IST</strong> has been delayed by 4 hours due to Air Traffic Control slot restrictions, shifting actual arrival to <strong>16:00 IST</strong>.
              </p>
              <div className="grid grid-cols-2 gap-2 pt-0.5 text-xs font-mono">
                <div className="p-2 rounded-lg bg-surface-container-lowest border border-surface-container-high">
                  <span className="text-[9px] text-outline block">ORIGINAL ARRIVAL</span>
                  <span className="text-slate-200 font-bold">12:00 IST (DEL T3)</span>
                </div>
                <div className="p-2 rounded-lg bg-rose-950/25 border border-rose-500/30">
                  <span className="text-[9px] text-rose-400 block font-semibold">REVISED ARRIVAL</span>
                  <span className="text-rose-200 font-bold">16:00 IST (+240m)</span>
                </div>
              </div>
            </div>

            {/* 2. IMPACT */}
            <div className="rounded-xl border border-amber-500/30 bg-surface-container-low/90 p-4 sm:p-4.5 space-y-2.5 backdrop-blur-md shadow-sm relative overflow-hidden">
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-amber-500/40 to-transparent pointer-events-none" />

              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase bg-amber-500/15 text-amber-300 border border-amber-500/30">
                  2. Impact Analysis
                </span>
                <span className="text-[11px] font-mono text-amber-300">
                  3 Affected &middot; 1 Unaffected
                </span>
              </div>
              <h3 className="text-sm sm:text-base font-bold text-white font-display">
                Downstream Missed Train Connection &amp; Hotel Late Check-In Risk
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                "Flight delay causes the traveler to miss the Delhi–Jaipur train (<strong>12015-SHT</strong> departing <strong>13:30 IST</strong>) because the revised arrival time (<strong>16:00 IST</strong>) is 150 minutes after train departure."
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] font-mono">
                <div className="p-2 rounded-lg bg-rose-950/25 border border-rose-500/30 text-rose-200">
                  <div className="font-bold">Train 12015-SHT</div>
                  <div className="text-[9px] opacity-80">MISSED (13:30)</div>
                </div>
                <div className="p-2 rounded-lg bg-amber-950/25 border border-amber-500/30 text-amber-200">
                  <div className="font-bold">Hotel HTL-JAI-101</div>
                  <div className="text-[9px] opacity-80">AT RISK (22:00)</div>
                </div>
                <div className="p-2 rounded-lg bg-emerald-950/25 border border-emerald-500/30 text-emerald-200">
                  <div className="font-bold">Amber Fort Tour</div>
                  <div className="text-[9px] opacity-80">UNAFFECTED</div>
                </div>
              </div>
            </div>
          </div>

          {/* Row 2: 3. Available Alternatives */}
          <div className="rounded-xl border border-surface-container-high bg-surface-container-low/90 p-4 sm:p-4.5 space-y-3 backdrop-blur-md shadow-sm relative overflow-hidden">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase bg-sky-500/15 text-sky-300 border border-sky-500/30 w-fit">
                3. Available Alternatives (Mock Supplier Ecosystem)
              </span>
              <span className="text-[11px] text-on-surface-variant font-mono">
                5 multi-modal candidates evaluated against hard constraints
              </span>
            </div>

            <div className="overflow-x-auto rounded-lg border border-surface-container-high">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-surface-container-high bg-surface-container-lowest text-[10px] text-on-surface-variant font-mono uppercase tracking-wider">
                    <th className="py-2 px-3">Option ID</th>
                    <th className="py-2 px-3">Mode</th>
                    <th className="py-2 px-3">Departure</th>
                    <th className="py-2 px-3">Arrival</th>
                    <th className="py-2 px-3">Price</th>
                    <th className="py-2 px-3">Feasibility</th>
                    <th className="py-2 px-3">Constraint Evaluation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.06] font-sans">
                  {alternativesList.map((alt) => (
                    <tr
                      key={alt.id}
                      className={`transition-colors ${
                        alt.selected
                          ? 'bg-emerald-950/25 text-emerald-100 font-medium'
                          : 'hover:bg-white/[0.03] text-slate-300'
                      }`}
                    >
                      <td className="py-2 px-3 font-mono font-bold">{alt.id}</td>
                      <td className="py-2 px-3">{alt.mode}</td>
                      <td className="py-2 px-3 font-mono">{alt.departure}</td>
                      <td className="py-2 px-3 font-mono">{alt.arrival}</td>
                      <td className="py-2 px-3 font-mono font-semibold">{alt.price}</td>
                      <td className="py-2 px-3">
                        {alt.selected ? (
                          <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono text-[9px] font-bold">
                            ★ SELECTED OPTIMAL
                          </span>
                        ) : alt.feasible ? (
                          <span className="px-2 py-0.5 rounded-md bg-sky-500/15 text-sky-300 border border-sky-500/30 font-mono text-[9px]">
                            FEASIBLE
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-md bg-rose-500/15 text-rose-300 border border-rose-500/30 font-mono text-[9px]">
                            PRUNED (INFEASIBLE)
                          </span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-[11px] text-slate-300">{alt.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Row 3: 4. Optimization Result & 5. Selected Recovery Plan */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
            {/* 4. OPTIMIZATION RESULT */}
            <div className="rounded-xl border border-violet-500/30 bg-surface-container-low/90 p-4 sm:p-4.5 space-y-2.5 backdrop-blur-md shadow-sm relative overflow-hidden">
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-violet-500/40 to-transparent pointer-events-none" />

              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase bg-violet-500/15 text-violet-300 border border-violet-500/30">
                  4. Optimization Result (Google OR-Tools CP-SAT)
                </span>
                <span className="text-[11px] font-mono text-emerald-400 font-bold">
                  OPTIMAL &middot; Score: 18.40
                </span>
              </div>
              <h3 className="text-sm sm:text-base font-bold text-white font-display">
                0-1 Integer Linear Programming Constraint Satisfaction
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 rounded-lg bg-surface-container-lowest border border-surface-container-high">
                  <span className="text-[9px] text-outline block">DEPARTURE &ge; 16:30</span>
                  <span className="text-emerald-400 font-semibold">✓ 17:30 Satisfied (+60m)</span>
                </div>
                <div className="p-2 rounded-lg bg-surface-container-lowest border border-surface-container-high">
                  <span className="text-[9px] text-outline block">ARRIVAL &le; 22:00 CUTOFF</span>
                  <span className="text-emerald-400 font-semibold">✓ 21:00 Satisfied (-60m)</span>
                </div>
                <div className="p-2 rounded-lg bg-surface-container-lowest border border-surface-container-high">
                  <span className="text-[9px] text-outline block">SEAT AVAILABILITY &ge; 1</span>
                  <span className="text-emerald-400 font-semibold">✓ 18 Seats Available</span>
                </div>
                <div className="p-2 rounded-lg bg-surface-container-lowest border border-surface-container-high">
                  <span className="text-[9px] text-outline block">BUDGET &le; INR 4,500</span>
                  <span className="text-emerald-400 font-semibold">✓ INR 750.00</span>
                </div>
              </div>
            </div>

            {/* 5. SELECTED RECOVERY PLAN */}
            <div className="rounded-xl border border-emerald-500/30 bg-surface-container-low/90 p-4 sm:p-4.5 space-y-2.5 backdrop-blur-md shadow-sm relative overflow-hidden">
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent pointer-events-none" />

              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  5. Selected Recovery Plan
                </span>
                <span className="text-[11px] font-mono text-emerald-300 font-bold">
                  PLAN-ADR-TRN124 &middot; Confidence 94%
                </span>
              </div>
              <h3 className="text-sm sm:text-base font-bold text-white font-display">
                Rebook onto Indian Railways Ashram Express 12916 (TRN124)
              </h3>
              <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                <div className="p-2 rounded-lg bg-surface-container-lowest border border-surface-container-high">
                  <span className="text-[9px] text-outline block">NEW SCHEDULE</span>
                  <span className="text-white font-bold">17:30 &rarr; 21:00</span>
                </div>
                <div className="p-2 rounded-lg bg-surface-container-lowest border border-surface-container-high">
                  <span className="text-[9px] text-outline block">NEW FARE / REFUND</span>
                  <span className="text-emerald-300 font-bold">INR 750 / +600</span>
                </div>
                <div className="p-2 rounded-lg bg-surface-container-lowest border border-surface-container-high">
                  <span className="text-[9px] text-outline block">NET EXTRA COST</span>
                  <span className="text-sky-300 font-bold">+INR 150.00</span>
                </div>
              </div>
            </div>
          </div>

          {/* Row 4: 6. Actions & 7. Action Status */}
          <div className="rounded-xl border border-surface-container-high bg-surface-container-low/90 p-4 sm:p-4.5 space-y-3 backdrop-blur-md shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase bg-teal-500/15 text-teal-300 border border-teal-500/30">
                6. Actions &amp; 7. Action Status
              </span>
              <span className="text-[11px] font-mono text-teal-300">
                Idempotent Execution Layer &middot; 6/6 Verified
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {actionsList.map((act, i) => (
                <div
                  key={i}
                  className="p-3 rounded-lg border border-surface-container-high bg-surface-container-lowest flex flex-col justify-between gap-1.5 text-xs hover:border-white/20 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-sky-400 text-[11px]">
                      #{act.step || i + 1} {act.action_type}
                    </span>
                    <span className="px-1.5 py-0.2 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono text-[9px] font-bold">
                      ✓ {act.status}
                    </span>
                  </div>
                  <div className="font-bold text-slate-100 font-display text-xs">{act.booking_id}</div>
                  {act.description && (
                    <div className="text-[10px] text-on-surface-variant leading-relaxed font-sans">{act.description}</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Row 5: 8. Explanation */}
          <div className="rounded-xl border border-sky-500/30 bg-gradient-to-br from-[#0b1120] via-[#070b16] to-[#04060d] p-4 sm:p-4.5 space-y-2 backdrop-blur-md shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold uppercase bg-sky-500/15 text-sky-300 border border-sky-500/30">
                8. AI &amp; Mathematical Decision Explanation
              </span>
              <span className="text-[11px] font-mono text-on-surface-variant">
                Explainable Recovery Reasoning
              </span>
            </div>
            <p className="text-xs sm:text-[13px] text-slate-100 leading-relaxed font-normal font-sans">
              "Train TRN124 (Ashram Express 12916 departing 17:30 IST) was selected by the Google OR-Tools CP-SAT solver because it is the earliest feasible rail alternative after the revised 16:00 IST flight arrival (providing a safe 90-minute terminal-to-station transfer buffer) that arrives in Jaipur at 21:00 IST — 60 minutes prior to Rambagh Heritage Palace Hotel's 22:00 IST latest check-in cutoff — while keeping the ticket fare at INR 750.00 (only INR 150.00 net difference after the INR 600.00 involuntary missed-connection refund on train 12015-SHT)."
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default RecoveryPlanPage;
