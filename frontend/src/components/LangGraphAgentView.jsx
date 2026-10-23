import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
  Lock,
  Cpu,
  Sliders,
  Check
} from 'lucide-react';
import { apiService } from '../services/api';
import { CountUpNumber } from './ui/SaaSPrimitives';

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
    <div className="space-y-4">
      {/* Header Banner */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="p-3.5 sm:p-4 rounded-xl bg-[#070b16]/80 backdrop-blur-2xl border border-white/[0.08] shadow-sm space-y-3 relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-80 h-80 bg-sky-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="flex flex-wrap items-center justify-between gap-3 relative z-10">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-sky-500/20 text-sky-300 border border-sky-500/40 font-mono">
                STAGE 7 &middot; LANGGRAPH 8-AGENT STATE MACHINE
              </span>
              {stateResult && (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Confidence:{' '}
                  <strong className="text-white">
                    <CountUpNumber end={Math.round((stateResult.confidence_score || 0) * 100)} duration={0.8} />%
                  </strong>{' '}
                  &middot; Retries: {stateResult.verification?.retries_used || 0}
                </span>
              )}
            </div>
            <h2 className="text-base sm:text-lg font-bold text-white mt-1 tracking-tight font-display">
              Autonomous Disruption Recovery Agent Workflow (LangGraph + OR-Tools)
            </h2>
            <p className="text-xs text-slate-400 mt-0.5 max-w-3xl leading-relaxed font-sans">
              Executes the 8-node stateful LangGraph pipeline with confidence scoring, action approval guardrails, supplier retry logic, and natural-language decision reasoning.
            </p>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => runWorkflow()}
            disabled={loading}
            className="h-8 px-3 py-1.5 rounded-lg bg-gradient-to-r from-sky-600 via-blue-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 cursor-pointer shadow-sm transition font-display disabled:opacity-50"
          >
            <Play className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Executing...' : 'Run 8-Agent Recovery'}</span>
          </motion.button>
        </div>

        {/* Visual 8-Node LangGraph Pipeline */}
        {graphMeta?.nodes && (
          <div className="p-2.5 rounded-lg bg-[#04060d]/90 border border-white/[0.08] overflow-x-auto">
            <div className="flex items-center gap-1.5 min-w-max text-[10px]">
              {graphMeta.nodes.map((node, idx) => (
                <React.Fragment key={node.id}>
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    className="px-2 py-1 rounded-md bg-[#0a1122] border border-sky-500/30 text-slate-200 flex items-center gap-1.5 shadow-sm"
                  >
                    <span className="w-4 h-4 rounded-full bg-sky-500/20 text-sky-300 font-mono text-[9px] flex items-center justify-center font-bold border border-sky-500/40">
                      {node.step}
                    </span>
                    <span className="font-semibold font-display">{node.name.replace(' Agent', '')}</span>
                  </motion.div>
                  {idx < graphMeta.nodes.length - 1 && (
                    <ArrowRight className="w-3 h-3 text-slate-600 shrink-0" />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        )}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left Column: Guardrail & Scenario Controls */}
        <div className="space-y-3.5">
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: 0.05 }}
            className="p-3.5 sm:p-4 rounded-xl bg-[#070b16]/80 backdrop-blur-2xl border border-white/[0.08] shadow-sm space-y-3"
          >
            <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-amber-400 font-mono">
              <Lock className="w-3.5 h-3.5 text-amber-400" />
              <span>Approval Guardrails &amp; Retry Controls</span>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className="block text-[10px] font-semibold text-slate-400 mb-0.5 font-sans">Revised Hub Arrival</label>
                <input
                  type="text"
                  value={revisedArrival}
                  onChange={(e) => setRevisedArrival(e.target.value)}
                  className="w-full h-8 px-2.5 py-1 rounded-lg bg-[#04060d] border border-white/[0.1] text-xs text-white font-mono focus:outline-none focus:border-sky-500/50 transition"
                />
              </div>
              <div>
                <label className="block text-[10px] font-semibold text-slate-400 mb-0.5 font-sans">Hotel Check-in Cutoff</label>
                <input
                  type="text"
                  value={hotelLatestCheckin}
                  onChange={(e) => setHotelLatestCheckin(e.target.value)}
                  className="w-full h-8 px-2.5 py-1 rounded-lg bg-[#04060d] border border-white/[0.1] text-xs text-white font-mono focus:outline-none focus:border-sky-500/50 transition"
                />
              </div>
              <div>
                <label className="block text-[10px] font-semibold text-slate-400 mb-0.5 font-sans">Traveler Budget Limit</label>
                <input
                  type="number"
                  value={maxBudget}
                  onChange={(e) => setMaxBudget(e.target.value)}
                  className="w-full h-8 px-2.5 py-1 rounded-lg bg-[#04060d] border border-white/[0.1] text-xs text-white font-mono focus:outline-none focus:border-sky-500/50 transition"
                />
              </div>
              <div>
                <label className="block text-[10px] font-semibold text-slate-400 mb-0.5 font-sans">Auto-Approve Cap (INR)</label>
                <input
                  type="number"
                  value={autoApproveMaxCost}
                  onChange={(e) => setAutoApproveMaxCost(e.target.value)}
                  className="w-full h-8 px-2.5 py-1 rounded-lg bg-[#04060d] border border-white/[0.1] text-xs text-white font-mono focus:outline-none focus:border-sky-500/50 transition"
                />
              </div>
            </div>

            <div className="pt-3 border-t border-white/[0.08] space-y-3 text-xs font-sans">
              <div className="flex items-center justify-between">
                <span className="text-slate-300 font-medium">Require Human Approval Gate</span>
                <input
                  type="checkbox"
                  checked={requireHumanApproval}
                  onChange={(e) => setRequireHumanApproval(e.target.checked)}
                  className="w-4 h-4 accent-amber-500 cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-300 font-medium">Query Live Mock Supplier APIs</span>
                <input
                  type="checkbox"
                  checked={useLiveMockSuppliers}
                  onChange={(e) => setUseLiveMockSuppliers(e.target.checked)}
                  className="w-4 h-4 accent-sky-500 cursor-pointer"
                />
              </div>

              <div className="space-y-1.5 pt-1">
                <label className="block text-[11px] text-slate-400 font-sans">
                  Simulate Transient Supplier Failures (Tests Retry Loop):{' '}
                  <strong className="text-sky-400 font-mono">{simulateTransientFailures}</strong>
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="1"
                  value={simulateTransientFailures}
                  onChange={(e) => setSimulateTransientFailures(Number(e.target.value))}
                  className="w-full accent-sky-500 cursor-pointer"
                />
              </div>
            </div>
          </motion.div>

          {/* Notifications Dispatched */}
          {stateResult?.notifications && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3.5 sm:p-4 rounded-xl bg-[#070b16]/80 backdrop-blur-2xl border border-white/[0.08] shadow-sm space-y-2.5"
            >
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-sky-400 font-mono">
                <Bell className="w-3.5 h-3.5 text-sky-400" />
                <span>Node 8: Dispatched Notifications ({stateResult.notifications.length})</span>
              </div>
              <div className="space-y-2">
                {stateResult.notifications.map((n, idx) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-[#04060d] border border-white/[0.08] text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[9px] text-sky-400 px-1.5 py-0.5 rounded bg-sky-500/10 border border-sky-500/30">
                        {n.channel}
                      </span>
                      <span className="font-mono text-[9px] text-emerald-400 font-bold">{n.status}</span>
                    </div>
                    <div className="font-semibold text-white font-display text-xs">{n.subject}</div>
                    <p className="text-[11px] text-slate-400 leading-relaxed font-sans">{n.message}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </div>

        {/* Right 2 Columns: Decision Explanation, Actions, Verification & Step-by-Step Trace */}
        <div className="lg:col-span-2 space-y-3.5">
          {stateResult && (
            <>
              {/* Decision & WHY Explanation Card */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3.5 sm:p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 shadow-sm space-y-2.5"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-400">
                      <Sparkles className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-[9px] font-mono uppercase text-slate-400">Optimal Selected Plan</div>
                      <span className="text-sm sm:text-base font-bold text-white font-display">
                        {stateResult.selected_plan?.selected_option?.name || 'Escalated'}
                      </span>
                    </div>
                  </div>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold border ${
                      stateResult.approval_required
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                    }`}
                  >
                    {stateResult.selected_plan?.status}
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-[#04060d]/90 border border-white/[0.08] text-xs text-slate-200 leading-relaxed font-sans">
                  <span className="text-emerald-400 font-bold block mb-0.5 uppercase tracking-wider text-[10px] font-mono">
                    WHY This Recovery Plan Was Selected:
                  </span>
                  {stateResult.selected_plan?.why_selected}
                </div>
              </motion.div>

              {/* Executed / Staged Actions */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.05 }}
                className="p-3.5 sm:p-4 rounded-xl bg-[#070b16]/80 backdrop-blur-2xl border border-white/[0.08] shadow-sm space-y-3"
              >
                <div className="flex items-center justify-between border-b border-white/[0.08] pb-2.5">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono">
                    Node 6 &amp; 7: Recovery Actions &amp; Verification Status
                  </span>
                  <span className="text-[10px] font-mono text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/30">
                    {stateResult.verification?.status} (Retries: {stateResult.verification?.retries_used || 0})
                  </span>
                </div>

                <div className="space-y-2">
                  {stateResult.actions?.map((act, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg bg-[#04060d] border border-white/[0.08] flex flex-wrap items-center justify-between gap-2 text-xs"
                    >
                      <div>
                        <span className="font-mono text-[10px] text-sky-400 font-bold mr-1.5">
                          [{act.action_type}]
                        </span>
                        <span className="text-slate-200 font-sans">{act.description}</span>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded-full font-mono text-[9px] font-bold border ${
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
              </motion.div>

              {/* 8-Agent Step-by-Step Execution Trace */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.1 }}
                className="p-3.5 sm:p-4 rounded-xl bg-[#070b16]/80 backdrop-blur-2xl border border-white/[0.08] shadow-sm space-y-3"
              >
                <div className="text-xs font-bold uppercase tracking-wider text-slate-200 font-mono border-b border-white/[0.08] pb-2.5">
                  LangGraph Agent Execution Trace ({stateResult.agent_trace?.length || 0} transitions)
                </div>
                <div className="space-y-2">
                  {stateResult.agent_trace?.map((t, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg bg-[#04060d]/80 border border-white/[0.06] text-xs space-y-0.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-sky-300 font-display text-xs">{t.agent}</span>
                        <span className="font-mono text-[9px] text-slate-500">Step #{idx + 1}</span>
                      </div>
                      <p className="text-slate-300 text-[11px] font-sans leading-relaxed">{t.summary}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
