import React, { useState, useEffect } from 'react';
import {
  Workflow,
  Play,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  ArrowRight,
  Bell,
  FileCheck,
  Sparkles,
  Lock
} from 'lucide-react';
import { apiService } from '../services/api';

const TRAIN_SCENARIO_ALTERNATIVES = [
  {
    transport_id: 'TRAIN-A',
    name: 'Train A (Shatabdi Express)',
    supplier_type: 'train',
    provider: 'Indian Railways',
    origin: 'Delhi',
    destination: 'Jaipur',
    departure: '5:00 PM',
    arrival: '8:30 PM',
    price: 500,
    currency: 'INR',
    available_seats: 12,
    number_of_changes: 0,
    reliability: 0.95,
  },
  {
    transport_id: 'TRAIN-B',
    name: 'Train B (Vande Bharat Express)',
    supplier_type: 'train',
    provider: 'Indian Railways',
    origin: 'Delhi',
    destination: 'Jaipur',
    departure: '5:30 PM',
    arrival: '9:00 PM',
    price: 700,
    currency: 'INR',
    available_seats: 18,
    number_of_changes: 0,
    reliability: 0.97,
  },
  {
    transport_id: 'TRAIN-C',
    name: 'Train C (Night Intercity)',
    supplier_type: 'train',
    provider: 'Indian Railways',
    origin: 'Delhi',
    destination: 'Jaipur',
    departure: '7:00 PM',
    arrival: '10:30 PM',
    price: 400,
    currency: 'INR',
    available_seats: 25,
    number_of_changes: 0,
    reliability: 0.88,
  },
];

export function LangGraphAgentView() {
  const [graphMeta, setGraphMeta] = useState(null);
  const [stateResult, setStateResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Configurable guardrails & scenario controls
  const [revisedArrival, setRevisedArrival] = useState('4:30 PM');
  const [hotelLatestCheckin, setHotelLatestCheckin] = useState('10:00 PM');
  const [minConnectionMinutes, setMinConnectionMinutes] = useState(45);
  const [maxBudget, setMaxBudget] = useState(1000);
  const [autoApproveMaxCost, setAutoApproveMaxCost] = useState(1000);
  const [requireHumanApproval, setRequireHumanApproval] = useState(false);
  const [simulateTransientFailures, setSimulateTransientFailures] = useState(0);
  const [useLiveMockSuppliers, setUseLiveMockSuppliers] = useState(false);

  const runWorkflow = async (customOverride = null) => {
    setLoading(true);
    try {
      const payload = customOverride || {
        journey_id: 'JRN-101',
        disruption: {
          type: 'flight_delay',
          delay_minutes: 240,
          origin: 'Delhi',
          destination: 'Jaipur',
          revised_arrival: useLiveMockSuppliers ? '2026-10-20T16:00:00' : revisedArrival,
          disrupted_booking_ref: '6E-205',
          missed_booking_ref: '12015-SHT',
          hotel_booking_ref: 'HTL-JAI-101',
        },
        alternatives: useLiveMockSuppliers ? null : TRAIN_SCENARIO_ALTERNATIVES,
        constraints_config: {
          current_arrival: useLiveMockSuppliers ? '2026-10-20T16:00:00' : revisedArrival,
          hotel_latest_checkin: useLiveMockSuppliers ? '2026-10-20T23:00:00' : hotelLatestCheckin,
          min_connection_minutes: Number(minConnectionMinutes),
          required_seats: 1,
        },
        preferences_config: {
          max_budget: Number(maxBudget),
        },
        approval_rules: {
          auto_approve_max_cost: Number(autoApproveMaxCost),
          min_confidence_threshold: 0.75,
          require_human_approval: requireHumanApproval,
        },
        simulate_transient_failures: Number(simulateTransientFailures),
        max_retries: 2,
      };
      const res = await apiService.runLangGraphAgent(payload);
      setStateResult(res);
    } catch (err) {
      console.error('LangGraph run error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    apiService.getLangGraphMetadata().then(setGraphMeta).catch(() => {});
    runWorkflow();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-sky-500/30 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-sky-500/20 text-sky-300 border border-sky-500/40">
                STAGE 7 &middot; LANGGRAPH 8-AGENT STATE MACHINE
              </span>
              {stateResult && (
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  Confidence: {Math.round((stateResult.confidence_score || 0) * 100)}% &middot; Retries: {stateResult.verification?.retries_used || 0}
                </span>
              )}
            </div>
            <h2 className="text-lg font-bold text-white mt-1.5">
              Autonomous Disruption Recovery Agent Workflow (LangGraph + OR-Tools)
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Executes the 8-node stateful LangGraph pipeline with confidence scoring, action approval guardrails, supplier retry logic, and natural-language decision reasoning.
            </p>
          </div>

          <button
            onClick={() => runWorkflow()}
            disabled={loading}
            className="px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold flex items-center gap-2 cursor-pointer shadow"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{loading ? 'Executing LangGraph...' : 'Run 8-Agent Recovery Workflow'}</span>
          </button>
        </div>

        {/* Visual 8-Node LangGraph Pipeline */}
        {graphMeta?.nodes && (
          <div className="p-3.5 rounded-xl bg-slate-950/90 border border-slate-800 overflow-x-auto">
            <div className="flex items-center gap-1.5 min-w-max text-[11px]">
              {graphMeta.nodes.map((node, idx) => (
                <React.Fragment key={node.id}>
                  <div className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-sky-500/30 text-slate-200 flex items-center gap-1.5">
                    <span className="w-4 h-4 rounded-full bg-sky-500/20 text-sky-300 font-mono text-[10px] flex items-center justify-center font-bold">
                      {node.step}
                    </span>
                    <span className="font-semibold">{node.name.replace(' Agent', '')}</span>
                  </div>
                  {idx < graphMeta.nodes.length - 1 && (
                    <ArrowRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Guardrail & Scenario Controls */}
        <div className="space-y-4">
          <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
              <Lock className="w-4 h-4" />
              Approval Guardrails &amp; Retry Controls
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Revised Hub Arrival</label>
                <input
                  type="text"
                  value={revisedArrival}
                  onChange={(e) => setRevisedArrival(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Hotel Check-in Cutoff</label>
                <input
                  type="text"
                  value={hotelLatestCheckin}
                  onChange={(e) => setHotelLatestCheckin(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Traveler Budget Limit</label>
                <input
                  type="number"
                  value={maxBudget}
                  onChange={(e) => setMaxBudget(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Auto-Approve Cap (INR)</label>
                <input
                  type="number"
                  value={autoApproveMaxCost}
                  onChange={(e) => setAutoApproveMaxCost(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono"
                />
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800 space-y-2.5 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-300">Require Human Approval Gate</span>
                <input
                  type="checkbox"
                  checked={requireHumanApproval}
                  onChange={(e) => setRequireHumanApproval(e.target.checked)}
                  className="w-4 h-4 accent-amber-500"
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-300">Query Live Mock Supplier APIs</span>
                <input
                  type="checkbox"
                  checked={useLiveMockSuppliers}
                  onChange={(e) => setUseLiveMockSuppliers(e.target.checked)}
                  className="w-4 h-4 accent-sky-500"
                />
              </div>

              <div>
                <label className="block text-[11px] text-slate-400 mb-1">
                  Simulate Transient Supplier Failures (Tests Retry Loop): <strong>{simulateTransientFailures}</strong>
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="1"
                  value={simulateTransientFailures}
                  onChange={(e) => setSimulateTransientFailures(Number(e.target.value))}
                  className="w-full accent-sky-500"
                />
              </div>
            </div>
          </div>

          {/* Notifications Dispatched */}
          {stateResult?.notifications && (
            <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-sky-400">
                <Bell className="w-4 h-4" />
                Node 8: Dispatched Notifications ({stateResult.notifications.length})
              </div>
              {stateResult.notifications.map((n, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] text-sky-400">{n.channel}</span>
                    <span className="font-mono text-[10px] text-emerald-400">{n.status}</span>
                  </div>
                  <div className="font-semibold text-white">{n.subject}</div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{n.message}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right 2 Columns: Decision Explanation, Actions, Verification & Step-by-Step Trace */}
        <div className="lg:col-span-2 space-y-4">
          {stateResult && (
            <>
              {/* Decision & WHY Explanation Card */}
              <div className="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-500/40 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-emerald-400" />
                    <span className="text-sm font-bold text-white">
                      Selected Plan: {stateResult.selected_plan?.selected_option?.name || 'Escalated'}
                    </span>
                  </div>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold border ${
                      stateResult.approval_required
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                    }`}
                  >
                    {stateResult.selected_plan?.status}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950/90 border border-slate-800 text-xs text-slate-200 leading-relaxed">
                  <span className="text-emerald-400 font-bold block mb-1 uppercase tracking-wider text-[11px]">
                    WHY This Recovery Plan Was Selected:
                  </span>
                  {stateResult.selected_plan?.why_selected}
                </div>
              </div>

              {/* Executed / Staged Actions */}
              <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Node 6 &amp; 7: Recovery Actions &amp; Verification Status
                  </span>
                  <span className="text-[11px] font-mono text-emerald-400">
                    {stateResult.verification?.status} (Retries: {stateResult.verification?.retries_used || 0})
                  </span>
                </div>

                <div className="space-y-2">
                  {stateResult.actions?.map((act, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex flex-wrap items-center justify-between gap-2 text-xs"
                    >
                      <div>
                        <span className="font-mono text-[11px] text-sky-400 font-bold mr-2">
                          [{act.action_type}]
                        </span>
                        <span className="text-slate-200">{act.description}</span>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold border ${
                          act.status === 'EXECUTED'
                            ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                            : 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                        }`}
                      >
                        {act.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 8-Agent Step-by-Step Execution Trace */}
              <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  LangGraph Agent Execution Trace ({stateResult.agent_trace?.length || 0} transitions)
                </div>
                <div className="space-y-2">
                  {stateResult.agent_trace?.map((t, idx) => (
                    <div key={idx} className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-sky-300">{t.agent}</span>
                        <span className="font-mono text-[10px] text-slate-500">Step #{idx + 1}</span>
                      </div>
                      <p className="text-slate-300 text-[11px]">{t.summary}</p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
