import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Cpu,
  CheckCircle2,
  XCircle,
  Sliders,
  Play,
  Sparkles,
  Clock,
  ShieldCheck,
  AlertTriangle,
  Layers,
  ArrowRight
} from 'lucide-react';
import { apiService } from '../services/api';

const DEFAULT_PROMPT_ALTERNATIVES = [
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

export function OptimizationView() {
  const [presets, setPresets] = useState([]);
  const [selectedPresetId, setSelectedPresetId] = useState('prompt-train-scenario');

  // Constraints state
  const [currentArrival, setCurrentArrival] = useState('4:00 PM');
  const [hotelLatestCheckin, setHotelLatestCheckin] = useState('10:00 PM');
  const [minConnectionMinutes, setMinConnectionMinutes] = useState(45);
  const [requiredSeats, setRequiredSeats] = useState(1);
  const [maxBudget, setMaxBudget] = useState(5000);
  const [autoFetchSuppliers, setAutoFetchSuppliers] = useState(false);

  // Configurable objective weights
  const [weights, setWeights] = useState({
    price: 0.35,
    travel_time: 0.25,
    waiting_time: 0.15,
    number_of_changes: 0.10,
    arrival_time: 0.10,
    reliability: 0.05,
  });

  const [candidates, setCandidates] = useState(DEFAULT_PROMPT_ALTERNATIVES);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runOptimization = async (customPayload = null) => {
    setLoading(true);
    try {
      const payload = customPayload || {
        origin: 'Delhi',
        destination: 'Jaipur',
        auto_fetch_from_suppliers: autoFetchSuppliers,
        available_alternatives: autoFetchSuppliers ? null : candidates,
        constraints: {
          current_arrival: currentArrival,
          hotel_latest_checkin: hotelLatestCheckin,
          min_connection_minutes: Number(minConnectionMinutes),
          required_seats: Number(requiredSeats),
        },
        traveler_preferences: {
          max_budget: Number(maxBudget),
          allowed_modes: ['flight', 'train', 'bus'],
          excluded_modes: [],
          weights,
        },
      };
      const res = await apiService.optimizeRecovery(payload);
      setResult(res);
    } catch (err) {
      console.error('OR-Tools Optimization error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    apiService.getOptimizationPresets().then((list) => {
      if (list && list.length > 0) setPresets(list);
    }).catch(() => {});
    runOptimization();
  }, []);

  const applyPreset = (preset) => {
    setSelectedPresetId(preset.id);
    const p = preset.payload;
    setCurrentArrival(p.constraints.current_arrival);
    setHotelLatestCheckin(p.constraints.hotel_latest_checkin);
    setMinConnectionMinutes(p.constraints.min_connection_minutes);
    setRequiredSeats(p.constraints.required_seats || 1);
    setMaxBudget(p.traveler_preferences.max_budget || 5000);
    setWeights(p.traveler_preferences.weights);
    const autoFetch = Boolean(p.auto_fetch_from_suppliers);
    setAutoFetchSuppliers(autoFetch);
    if (!autoFetch && p.available_alternatives) {
      setCandidates(p.available_alternatives);
    }
    runOptimization(p);
  };

  const updateWeight = (key, val) => {
    setWeights((prev) => ({ ...prev, [key]: Number(val) }));
  };

  return (
    <div className="space-y-4">
      {/* Header Banner */}
      <div className="p-3.5 sm:p-4 rounded-xl bg-[#070b16]/80 border border-white/[0.08] backdrop-blur-2xl shadow-sm flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 relative overflow-hidden">
        <div className="absolute inset-0 aviation-grid-overlay opacity-30 pointer-events-none" />
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-violet-500/30 to-transparent pointer-events-none" />

        <div className="relative z-10 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider bg-violet-500/15 text-violet-300 border border-violet-500/30">
              STAGE 6 &middot; GOOGLE OR-TOOLS CP-SAT SOLVER
            </span>
            {result?.solver_metadata && (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#04060d] text-emerald-400 border border-emerald-500/30">
                {result.solver_metadata.solver} &middot; {result.solver_metadata.status} ({result.solver_metadata.wall_time_ms} ms)
              </span>
            )}
          </div>
          <h2 className="text-base sm:text-lg font-bold text-white font-display tracking-tight">
            Constrained Multi-Objective Recovery Optimization Engine
          </h2>
          <p className="text-xs text-slate-300 max-w-3xl font-sans leading-relaxed">
            Mathematical optimization performed strictly by <strong>Google OR-Tools CP-SAT</strong> (0-1 Integer Linear Programming) enforcing hard departure, transfer buffer, hotel check-in cutoff, seat availability, and preference weight constraints.
          </p>
        </div>

        {/* Scenario Presets */}
        <div className="flex flex-wrap gap-1.5 relative z-10">
          {presets.map((preset) => (
            <button
              key={preset.id}
              onClick={() => applyPreset(preset)}
              className={`h-8 px-2.5 py-1 rounded-lg text-xs font-semibold border transition cursor-pointer font-display ${
                selectedPresetId === preset.id
                  ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white border-violet-400/40 shadow-sm'
                  : 'bg-[#04060d] text-slate-400 border-white/[0.08] hover:bg-slate-800/80 hover:text-white'
              }`}
            >
              {preset.id === 'prompt-train-scenario'
                ? '1. Prompt Scenario'
                : preset.id === 'tight-buffer-train-b-wins'
                ? '2. Tight Buffer'
                : '3. Live Mock Suppliers'}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left Column: Constraints & Objective Weight Sliders */}
        <div className="space-y-4">
          {/* Hard Constraints Box */}
          <div className="p-3.5 sm:p-4 rounded-xl bg-[#070b16]/80 border border-white/[0.08] backdrop-blur-2xl shadow-sm space-y-3">
            <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-sky-400 font-mono">
              <ShieldCheck className="w-3.5 h-3.5" />
              CP-SAT Hard Constraints
            </div>

            <div className="grid grid-cols-2 gap-2.5 font-sans">
              <div>
                <label className="block text-[10px] text-slate-400 mb-0.5 font-mono">Current Arrival</label>
                <input
                  type="text"
                  value={currentArrival}
                  onChange={(e) => setCurrentArrival(e.target.value)}
                  className="w-full h-8 px-2.5 py-1 rounded-lg bg-[#04060d] border border-white/[0.08] text-xs text-white font-mono focus:outline-none focus:border-sky-400"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-400 mb-0.5 font-mono">Hotel Latest Check-in</label>
                <input
                  type="text"
                  value={hotelLatestCheckin}
                  onChange={(e) => setHotelLatestCheckin(e.target.value)}
                  className="w-full h-8 px-2.5 py-1 rounded-lg bg-[#04060d] border border-white/[0.08] text-xs text-white font-mono focus:outline-none focus:border-sky-400"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-400 mb-0.5 font-mono">Min Connection (min)</label>
                <input
                  type="number"
                  value={minConnectionMinutes}
                  onChange={(e) => setMinConnectionMinutes(e.target.value)}
                  className="w-full h-8 px-2.5 py-1 rounded-lg bg-[#04060d] border border-white/[0.08] text-xs text-white font-mono focus:outline-none focus:border-sky-400"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-400 mb-0.5 font-mono">Max Budget (INR)</label>
                <input
                  type="number"
                  value={maxBudget}
                  onChange={(e) => setMaxBudget(e.target.value)}
                  className="w-full h-8 px-2.5 py-1 rounded-lg bg-[#04060d] border border-white/[0.08] text-xs text-white font-mono focus:outline-none focus:border-sky-400"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2.5 border-t border-white/[0.08] text-xs font-sans">
              <span className="text-slate-300">Fetch Live Mock Supplier Inventory</span>
              <input
                type="checkbox"
                checked={autoFetchSuppliers}
                onChange={(e) => setAutoFetchSuppliers(e.target.checked)}
                className="w-3.5 h-3.5 accent-violet-500 rounded"
              />
            </div>
          </div>

          {/* Configurable Weights Box */}
          <div className="p-3.5 sm:p-4 rounded-xl bg-[#070b16]/80 border border-white/[0.08] backdrop-blur-2xl shadow-sm space-y-2.5">
            <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-violet-400 font-mono">
              <Sliders className="w-3.5 h-3.5" />
              Configurable Objective Weights
            </div>

            {[
              { key: 'price', label: 'Price Weight' },
              { key: 'travel_time', label: 'Travel Time Weight' },
              { key: 'waiting_time', label: 'Waiting Time Weight' },
              { key: 'number_of_changes', label: 'Number of Changes Weight' },
              { key: 'arrival_time', label: 'Arrival Time Weight' },
              { key: 'reliability', label: 'Reliability Weight' },
            ].map((w) => (
              <div key={w.key}>
                <div className="flex justify-between text-[11px] text-slate-300 mb-0.5 font-sans">
                  <span>{w.label}</span>
                  <span className="font-mono text-violet-300 font-semibold">{weights[w.key].toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={weights[w.key]}
                  onChange={(e) => updateWeight(w.key, e.target.value)}
                  className="w-full accent-violet-500 cursor-pointer h-1.5"
                />
              </div>
            ))}

            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => runOptimization()}
              disabled={loading}
              className="w-full mt-2 h-8.5 rounded-lg bg-gradient-to-r from-violet-600 via-indigo-600 to-sky-600 hover:from-violet-500 hover:to-sky-500 text-white text-xs font-bold flex items-center justify-center gap-1.5 cursor-pointer shadow-sm font-display"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{loading ? 'Solving CP-SAT Model...' : 'Run Google OR-Tools Optimizer'}</span>
            </motion.button>
          </div>
        </div>

        {/* Right 2 Columns: Selected Optimal Option + Candidate Matrix */}
        <div className="lg:col-span-2 space-y-3.5">
          {result && (
            <>
              {/* Optimal Solution Banner */}
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className={`p-3.5 sm:p-4 rounded-xl border space-y-2.5 backdrop-blur-2xl shadow-sm relative overflow-hidden ${
                  result.constraints_satisfied
                    ? 'bg-emerald-950/20 border-emerald-500/40 shadow-emerald-950/20'
                    : 'bg-rose-950/25 border-rose-500/40 shadow-rose-950/20'
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2.5">
                  <div className="flex items-center gap-2">
                    {result.constraints_satisfied ? (
                      <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400">
                        <CheckCircle2 className="w-4 h-4" />
                      </div>
                    ) : (
                      <div className="p-1.5 rounded-lg bg-rose-500/20 text-rose-400">
                        <AlertTriangle className="w-4 h-4" />
                      </div>
                    )}
                    <span className="text-sm sm:text-base font-bold text-white font-display">
                      {result.constraints_satisfied && result.selected_option
                        ? `Optimal Recovery Selected: ${result.selected_option.name} (${result.selected_option.transport_id})`
                        : 'Infeasible: No Option Satisfies All Hard Constraints'}
                    </span>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-[#04060d] text-emerald-300 border border-emerald-500/30">
                    Score: {result.objective_score}
                  </span>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed bg-[#04060d]/80 p-2.5 rounded-lg border border-white/[0.08] font-sans">
                  {result.explanation}
                </p>
              </motion.div>

              {/* All Evaluated Alternatives Table/Cards */}
              <div className="space-y-2.5">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
                  Evaluated Alternatives &amp; Constraint Satisfaction ({result.alternatives?.length || 0})
                </h3>

                {result.alternatives?.map((alt) => (
                  <motion.div
                    key={alt.transport_id}
                    whileHover={{ y: -1 }}
                    className={`p-3.5 sm:p-4 rounded-xl border transition-all space-y-2 backdrop-blur-md ${
                      alt.selected
                        ? 'bg-emerald-950/20 border-emerald-500/50 shadow-sm'
                        : alt.feasible
                        ? 'bg-[#070b16]/80 border-white/[0.08] hover:border-white/20'
                        : 'bg-[#070b16]/50 border-rose-500/20 opacity-80'
                    }`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="px-2 py-0.5 rounded font-mono text-[11px] font-bold bg-[#04060d] text-sky-300 border border-white/[0.08]">
                          {alt.transport_id}
                        </span>
                        <span className="text-xs sm:text-sm font-bold text-white font-display">{alt.name}</span>
                        {alt.selected && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                            OR-TOOLS SELECTED OPTIMAL
                          </span>
                        )}
                        {!alt.feasible && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
                            PRUNED (INFEASIBLE)
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-3 text-xs">
                        <span className="font-bold text-emerald-400 font-mono">
                          {alt.currency} {alt.price}
                        </span>
                        <span className="font-mono text-slate-400">
                          Penalty: <strong className="text-slate-200">{alt.objective_score}</strong>
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2.5 sm:gap-3.5 text-xs text-slate-300 font-sans">
                      <span>Dep: <strong className="font-mono text-sky-300">{alt.departure}</strong> ({alt.departure_clock})</span>
                      <span>&rarr;</span>
                      <span>Arr: <strong className="font-mono text-sky-300">{alt.arrival}</strong> ({alt.arrival_clock})</span>
                      <span className="text-slate-600">&bull;</span>
                      <span>Travel: <strong>{alt.travel_time_minutes}m</strong></span>
                      <span className="text-slate-600">&bull;</span>
                      <span>Wait: <strong>{alt.waiting_time_minutes}m</strong></span>
                      <span className="text-slate-600">&bull;</span>
                      <span>Seats: <strong>{alt.available_seats}</strong></span>
                      <span className="text-slate-600">&bull;</span>
                      <span>Reliability: <strong>{Math.round(alt.reliability * 100)}%</strong></span>
                    </div>

                    {/* 5 Constraint Badges */}
                    <div className="flex flex-wrap gap-1.5 pt-0.5">
                      {Object.entries(alt.constraint_checks || {}).map(([cKey, passed]) => (
                        <span
                          key={cKey}
                          className={`px-2 py-0.5 rounded-full text-[10px] font-mono flex items-center gap-1 border ${
                            passed
                              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25'
                              : 'bg-rose-500/15 text-rose-300 border-rose-500/30 font-semibold'
                          }`}
                        >
                          {passed ? <CheckCircle2 className="w-3 h-3 text-emerald-400" /> : <XCircle className="w-3 h-3 text-rose-400" />}
                          {cKey}
                        </span>
                      ))}
                    </div>

                    {alt.violation_reasons && alt.violation_reasons.length > 0 && (
                      <div className="text-[11px] text-rose-300 bg-rose-950/25 px-2.5 py-1.5 rounded-lg border border-rose-500/20 font-sans">
                        <strong>Constraint Violation:</strong> {alt.violation_reasons.join(' | ')}
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default OptimizationView;
