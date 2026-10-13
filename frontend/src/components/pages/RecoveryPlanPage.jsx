import React, { useState } from 'react';
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
  Layers
} from 'lucide-react';
import { OptimizationView } from '../OptimizationView';
import { LangGraphAgentView } from '../LangGraphAgentView';
import { ConfirmDialog } from '../ui/SaaSPrimitives';

export function RecoveryPlanPage({
  onExecuteRecoveryActions,
  executingActions = false,
  actionExecutionResult = null,
}) {
  const [subView, setSubView] = useState('overview');
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);

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
    <div className="space-y-6">
      {/* Sub-navigation bar */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setSubView('overview')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
              subView === 'overview'
                ? 'bg-sky-600 text-white shadow'
                : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            8-Panel Recovery Command Summary
          </button>
          <button
            onClick={() => setSubView('ortools')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition cursor-pointer ${
              subView === 'ortools'
                ? 'bg-violet-600 text-white shadow'
                : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Interactive OR-Tools Optimizer (Stage 6)</span>
          </button>
          <button
            onClick={() => setSubView('langgraph')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition cursor-pointer ${
              subView === 'langgraph'
                ? 'bg-indigo-600 text-white shadow'
                : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <Workflow className="w-3.5 h-3.5" />
            <span>LangGraph 8-Node Agent Workflow (Stage 7)</span>
          </button>
        </div>

        <button
          onClick={() => setConfirmModalOpen(true)}
          disabled={executingActions}
          className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-2 shadow cursor-pointer"
        >
          <Play className="w-3.5 h-3.5" />
          <span>
            {executingActions ? 'Executing Actions...' : 'Approve & Execute Recovery Plan'}
          </span>
        </button>
      </div>

      <ConfirmDialog
        open={confirmModalOpen}
        title="Confirm Autonomous Recovery Execution"
        description="This will execute all 6 recovery actions (Cancel 12015-SHT, Rebook TRN124, Claim INR 600 Refund, Modify Hotel HTL-JAI-101 Check-In to 21:30, and Dispatch Grounded Notifications) against the Mock Supplier APIs with idempotency protection."
        confirmLabel="Execute 6 Recovery Actions"
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
        <div className="space-y-6">
          {/* Row 1: 1. Problem & 2. Impact */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 1. PROBLEM */}
            <div className="rounded-2xl border border-rose-500/30 bg-slate-900/70 p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  1. Problem
                </span>
                <span className="text-xs font-mono text-rose-400 font-bold">
                  DISR-AI202-240M &middot; CRITICAL
                </span>
              </div>
              <h3 className="text-base font-bold text-white">
                Air India Flight AI-202 Delayed +240 Minutes (Mumbai &rarr; Delhi)
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Inbound flight <strong>AI-202</strong> scheduled to land at New Delhi (DEL) at <strong>12:00 IST</strong> has been delayed by 4 hours due to Air Traffic Control slot restrictions, shifting actual arrival to <strong>16:00 IST</strong>.
              </p>
              <div className="grid grid-cols-2 gap-2.5 pt-1 text-xs font-mono">
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">ORIGINAL ARRIVAL</span>
                  <span className="text-slate-200">12:00 IST (DEL T3)</span>
                </div>
                <div className="p-2.5 rounded-xl bg-rose-950/30 border border-rose-500/30">
                  <span className="text-[10px] text-rose-400 block">REVISED ARRIVAL</span>
                  <span className="text-rose-200 font-bold">16:00 IST (+240m)</span>
                </div>
              </div>
            </div>

            {/* 2. IMPACT */}
            <div className="rounded-2xl border border-amber-500/30 bg-slate-900/70 p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  2. Impact Analysis
                </span>
                <span className="text-xs font-mono text-amber-300">
                  3 Affected &middot; 1 Unaffected
                </span>
              </div>
              <h3 className="text-base font-bold text-white">
                Downstream Missed Train Connection &amp; Hotel Late Check-In Risk
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                "Flight delay causes the traveler to miss the Delhi–Jaipur train (<strong>12015-SHT</strong> departing <strong>13:30 IST</strong>) because the revised arrival time (<strong>16:00 IST</strong>) is 150 minutes after train departure."
              </p>
              <div className="grid grid-cols-3 gap-2 text-[11px] font-mono">
                <div className="p-2 rounded-xl bg-rose-950/30 border border-rose-500/30 text-rose-200">
                  <div className="font-bold">Train 12015-SHT</div>
                  <div className="text-[10px] opacity-80">MISSED (13:30)</div>
                </div>
                <div className="p-2 rounded-xl bg-amber-950/30 border border-amber-500/30 text-amber-200">
                  <div className="font-bold">Hotel HTL-JAI-101</div>
                  <div className="text-[10px] opacity-80">AT RISK (22:00)</div>
                </div>
                <div className="p-2 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-emerald-200">
                  <div className="font-bold">Amber Fort Tour</div>
                  <div className="text-[10px] opacity-80">UNAFFECTED</div>
                </div>
              </div>
            </div>
          </div>

          {/* Row 2: 3. Available Alternatives */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase bg-sky-500/20 text-sky-300 border border-sky-500/30">
                3. Available Alternatives (Mock Supplier Ecosystem)
              </span>
              <span className="text-xs text-slate-400">
                5 multi-modal candidates evaluated against hard constraints
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-[11px] text-slate-400 font-mono uppercase">
                    <th className="py-2.5 px-3">Option ID</th>
                    <th className="py-2.5 px-3">Mode</th>
                    <th className="py-2.5 px-3">Departure</th>
                    <th className="py-2.5 px-3">Arrival</th>
                    <th className="py-2.5 px-3">Price</th>
                    <th className="py-2.5 px-3">Feasibility</th>
                    <th className="py-2.5 px-3">Constraint Evaluation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/70">
                  {alternativesList.map((alt) => (
                    <tr
                      key={alt.id}
                      className={
                        alt.selected
                          ? 'bg-emerald-950/25 text-emerald-100'
                          : 'hover:bg-slate-800/30 text-slate-300'
                      }
                    >
                      <td className="py-2.5 px-3 font-mono font-bold">{alt.id}</td>
                      <td className="py-2.5 px-3">{alt.mode}</td>
                      <td className="py-2.5 px-3 font-mono">{alt.departure}</td>
                      <td className="py-2.5 px-3 font-mono">{alt.arrival}</td>
                      <td className="py-2.5 px-3 font-mono font-semibold">{alt.price}</td>
                      <td className="py-2.5 px-3">
                        {alt.selected ? (
                          <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono text-[10px] font-bold">
                            ★ SELECTED OPTIMAL
                          </span>
                        ) : alt.feasible ? (
                          <span className="px-2 py-0.5 rounded bg-sky-500/15 text-sky-300 font-mono text-[10px]">
                            FEASIBLE
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-300 font-mono text-[10px]">
                            PRUNED (INFEASIBLE)
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-[11px]">{alt.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Row 3: 4. Optimization Result & 5. Selected Recovery Plan */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 4. OPTIMIZATION RESULT */}
            <div className="rounded-2xl border border-violet-500/30 bg-slate-900/70 p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase bg-violet-500/20 text-violet-300 border border-violet-500/30">
                  4. Optimization Result (Google OR-Tools CP-SAT)
                </span>
                <span className="text-xs font-mono text-emerald-400 font-bold">
                  OPTIMAL &middot; Score: 18.40
                </span>
              </div>
              <h3 className="text-base font-bold text-white">
                0-1 Integer Linear Programming Constraint Satisfaction
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">DEPARTURE &ge; 16:30</span>
                  <span className="text-emerald-400">✓ 17:30 Satisfied (+60m)</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">ARRIVAL &le; 22:00 CUTOFF</span>
                  <span className="text-emerald-400">✓ 21:00 Satisfied (-60m)</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">SEAT AVAILABILITY &ge; 1</span>
                  <span className="text-emerald-400">✓ 18 Seats Available</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">BUDGET &le; INR 4,500</span>
                  <span className="text-emerald-400">✓ INR 750.00</span>
                </div>
              </div>
            </div>

            {/* 5. SELECTED RECOVERY PLAN */}
            <div className="rounded-2xl border border-emerald-500/30 bg-slate-900/70 p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  5. Selected Recovery Plan
                </span>
                <span className="text-xs font-mono text-emerald-300 font-bold">
                  PLAN-ADR-TRN124 &middot; Confidence 94%
                </span>
              </div>
              <h3 className="text-base font-bold text-white">
                Rebook onto Indian Railways Ashram Express 12916 (TRN124)
              </h3>
              <div className="grid grid-cols-3 gap-2.5 text-xs font-mono">
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">NEW SCHEDULE</span>
                  <span className="text-white font-bold">17:30 &rarr; 21:00</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">NEW FARE / REFUND</span>
                  <span className="text-emerald-300 font-bold">INR 750 / +600</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">NET EXTRA COST</span>
                  <span className="text-sky-300 font-bold">+INR 150.00</span>
                </div>
              </div>
            </div>
          </div>

          {/* Row 4: 6. Actions & 7. Action Status */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase bg-teal-500/20 text-teal-300 border border-teal-500/30">
                  6. Actions &amp; 7. Action Status
                </span>
              </div>
              <span className="text-xs font-mono text-teal-300">
                Idempotent Execution Layer &middot; 6/6 Verified
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {actionsList.map((act, i) => (
                <div
                  key={i}
                  className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/70 flex flex-col justify-between gap-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-sky-300">
                      #{act.step || i + 1} {act.action_type}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono text-[10px] font-bold">
                      ✓ {act.status}
                    </span>
                  </div>
                  <div className="font-semibold text-slate-200">{act.booking_id}</div>
                  {act.description && (
                    <div className="text-[11px] text-slate-400">{act.description}</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Row 5: 8. Explanation */}
          <div className="rounded-2xl border border-sky-500/30 bg-gradient-to-r from-slate-900 via-sky-950/30 to-slate-900 p-5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase bg-sky-500/20 text-sky-300 border border-sky-500/30">
                8. AI &amp; Mathematical Decision Explanation
              </span>
              <span className="text-xs font-mono text-slate-400">
                Explainable Recovery Reasoning
              </span>
            </div>
            <p className="text-sm text-slate-100 leading-relaxed font-medium">
              "Train TRN124 (Ashram Express 12916 departing 17:30 IST) was selected by the Google OR-Tools CP-SAT solver because it is the earliest feasible rail alternative after the revised 16:00 IST flight arrival (providing a safe 90-minute terminal-to-station transfer buffer) that arrives in Jaipur at 21:00 IST — 60 minutes prior to Rambagh Heritage Palace Hotel's 22:00 IST latest check-in cutoff — while keeping the ticket fare at INR 750.00 (only INR 150.00 net difference after the INR 600.00 involuntary missed-connection refund on train 12015-SHT)."
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
