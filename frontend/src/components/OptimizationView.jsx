import React, { useState, useEffect } from 'react';
import {
  Cpu,
  CheckCircle2,
  XCircle,
  Sliders,
  Play,
  Sparkles,
  Clock,
  ShieldCheck,
  AlertTriangle
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
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-violet-500/30 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-violet-500/20 text-violet-300 border border-violet-500/40">
              STAGE 6 &middot; GOOGLE OR-TOOLS CP-SAT SOLVER
            </span>
            {result?.solver_metadata && (
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono bg-slate-800 text-emerald-400 border border-slate-700">
                {result.solver_metadata.solver} &middot; {result.solver_metadata.status} ({result.solver_metadata.wall_time_ms} ms)
              </span>
            )}
          </div>
          <h2 className="text-lg font-bold text-white mt-1.5">
            Constrained Multi-Objective Recovery Optimization Engine
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Mathematical optimization is performed strictly by <strong>Google OR-Tools CP-SAT</strong> (0-1 Integer Linear Programming) enforcing hard departure, connection buffer, hotel check-in, availability, and preference constraints.
          </p>
        </div>

        {/* Scenario Presets */}
        <div className="flex flex-wrap gap-2">
          {presets.map((preset) => (
            <button
              key={preset.id}
              onClick={() => applyPreset(preset)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition cursor-pointer ${
                selectedPresetId === preset.id
                  ? 'bg-violet-600 text-white border-violet-500 shadow'
                  : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-700'
              }`}
            >
              {preset.id === 'prompt-train-scenario'
                ? '1. Prompt Scenario (Train A/B/C)'
                : preset.id === 'tight-buffer-train-b-wins'
                ? '2. Tight Buffer (Train B Wins)'
                : '3. Live Mock Suppliers (Multi-Modal)'}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Constraints & Objective Weight Sliders */}
        <div className="space-y-4">
          {/* Hard Constraints Box */}
          <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-sky-400">
              <ShieldCheck className="w-4 h-4" />
              CP-SAT Hard Constraints
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Current Arrival</label>
                <input
                  type="text"
                  value={currentArrival}
                  onChange={(e) => setCurrentArrival(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Hotel Latest Check-in</label>
                <input
                  type="text"
                  value={hotelLatestCheckin}
                  onChange={(e) => setHotelLatestCheckin(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Min Connection (min)</label>
                <input
                  type="number"
                  value={minConnectionMinutes}
                  onChange={(e) => setMinConnectionMinutes(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Max Budget (INR)</label>
                <input
                  type="number"
                  value={maxBudget}
                  onChange={(e) => setMaxBudget(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white font-mono"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs">
              <span className="text-slate-300">Fetch Live Mock Supplier Inventory</span>
              <input
                type="checkbox"
                checked={autoFetchSuppliers}
                onChange={(e) => setAutoFetchSuppliers(e.target.checked)}
                className="w-4 h-4 accent-violet-500"
              />
            </div>
          </div>

          {/* Configurable Weights Box */}
          <div className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-violet-400">
              <Sliders className="w-4 h-4" />
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
                <div className="flex justify-between text-[11px] text-slate-300 mb-0.5">
                  <span>{w.label}</span>
                  <span className="font-mono text-violet-300">{weights[w.key].toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={weights[w.key]}
                  onChange={(e) => updateWeight(w.key, e.target.value)}
                  className="w-full accent-violet-500"
                />
              </div>
            ))}

            <button
              onClick={() => runOptimization()}
              disabled={loading}
              className="w-full mt-2 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-xs font-bold flex items-center justify-center gap-2 cursor-pointer shadow"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{loading ? 'Solving CP-SAT Model...' : 'Run Google OR-Tools Optimizer'}</span>
            </button>
          </div>
        </div>

        {/* Right 2 Columns: Selected Optimal Option + Candidate Matrix */}
        <div className="lg:col-span-2 space-y-4">
          {result && (
            <>
              {/* Optimal Solution Banner */}
              <div
                className={`p-5 rounded-2xl border space-y-3 ${
                  result.constraints_satisfied
                    ? 'bg-emerald-950/25 border-emerald-500/40'
                    : 'bg-rose-950/30 border-rose-500/40'
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {result.constraints_satisfied ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-rose-400" />
                    )}
                    <span className="text-sm font-bold text-white">
                      {result.constraints_satisfied && result.selected_option
                        ? `Optimal Recovery Selected: ${result.selected_option.name} (${result.selected_option.transport_id})`
                        : 'Infeasible: No Option Satisfies All Hard Constraints'}
                    </span>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-slate-900 text-emerald-300 border border-emerald-500/30">
                    Objective Score: {result.objective_score}
                  </span>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/80 p-3.5 rounded-xl border border-slate-800">
                  {result.explanation}
                </p>
              </div>

              {/* All Evaluated Alternatives Table/Cards */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Evaluated Alternatives &amp; Constraint Satisfaction ({result.alternatives?.length || 0})
                </h3>

                {result.alternatives?.map((alt) => (
                  <div
                    key={alt.transport_id}
                    className={`p-4 rounded-xl border transition space-y-2.5 ${
                      alt.selected
                        ? 'bg-emerald-950/20 border-emerald-500/50'
                        : alt.feasible
                        ? 'bg-slate-900/70 border-slate-800'
                        : 'bg-slate-900/30 border-rose-500/25 opacity-80'
                    }`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded font-mono text-xs font-bold bg-slate-800 text-sky-300 border border-slate-700">
                          {alt.transport_id}
                        </span>
                        <span className="text-sm font-bold text-white">{alt.name}</span>
                        {alt.selected && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                            OR-TOOLS SELECTED OPTIMAL
                          </span>
                        )}
                        {!alt.feasible && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
                            PRUNED (INFEASIBLE)
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-3 text-xs">
                        <span className="font-bold text-emerald-400">
                          {alt.currency} {alt.price}
                        </span>
                        <span className="font-mono text-slate-400">
                          Penalty Score: <strong className="text-slate-200">{alt.objective_score}</strong>
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300">
                      <span>Dep: <strong className="font-mono text-sky-300">{alt.departure}</strong> ({alt.departure_clock})</span>
                      <span>&rarr;</span>
                      <span>Arr: <strong className="font-mono text-sky-300">{alt.arrival}</strong> ({alt.arrival_clock})</span>
                      <span>&bull;</span>
                      <span>Travel: <strong>{alt.travel_time_minutes}m</strong></span>
                      <span>&bull;</span>
                      <span>Wait: <strong>{alt.waiting_time_minutes}m</strong></span>
                      <span>&bull;</span>
                      <span>Seats: <strong>{alt.available_seats}</strong></span>
                      <span>&bull;</span>
                      <span>Reliability: <strong>{Math.round(alt.reliability * 100)}%</strong></span>
                    </div>

                    {/* 5 Constraint Badges */}
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {Object.entries(alt.constraint_checks || {}).map(([cKey, passed]) => (
                        <span
                          key={cKey}
                          className={`px-2 py-0.5 rounded text-[10px] font-mono flex items-center gap-1 border ${
                            passed
                              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25'
                              : 'bg-rose-500/15 text-rose-300 border-rose-500/30 font-semibold'
                          }`}
                        >
                          {passed ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                          {cKey}
                        </span>
                      ))}
                    </div>

                    {alt.violation_reasons && alt.violation_reasons.length > 0 && (
                      <div className="text-[11px] text-rose-300 bg-rose-950/30 px-3 py-1.5 rounded-lg border border-rose-500/20">
                        <strong>Constraint Violation:</strong> {alt.violation_reasons.join(' | ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
