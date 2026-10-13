import React, { useState } from 'react';
import { 
  AlertTriangle, 
  Flame, 
  Clock, 
  Send, 
  XCircle, 
  CheckCircle2, 
  ArrowRight, 
  BrainCircuit, 
  ShieldAlert, 
  Plane, 
  Train, 
  Bus, 
  Hotel, 
  Sparkles,
  Layers
} from 'lucide-react';

export function DisruptionSimulator({ 
  journey, 
  bookings = [], 
  onSimulate, 
  loading, 
  latestImpactResult 
}) {
  const [selectedBookingId, setSelectedBookingId] = useState(bookings[0]?.id || '');
  const [disruptionType, setDisruptionType] = useState('flight_delay');
  const [delayMinutes, setDelayMinutes] = useState(240); // 4 hours default from prompt

  const handleSimulate = async (e) => {
    e.preventDefault();
    if (!selectedBookingId) return;

    await onSimulate({
      booking_id: parseInt(selectedBookingId),
      type: disruptionType,
      delay_minutes: disruptionType.includes('delay') ? parseInt(delayMinutes) : 0
    });
  };

  const selectedBooking = bookings.find(b => b.id === parseInt(selectedBookingId));

  return (
    <div className="space-y-6">
      
      {/* Simulation Form Card */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
              <Flame className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                Travel Disruption Simulator &amp; Impact Engine
              </h3>
              <p className="text-xs text-slate-400">
                Inject multi-modal disruptions to evaluate downstream graph cascades, missed connections, and unaffected bookings.
              </p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20">
            SIMULATION ENGINE READY
          </span>
        </div>

        <form onSubmit={handleSimulate} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            {/* 1. Target Booking */}
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Target Booking Leg
              </label>
              <select
                value={selectedBookingId}
                onChange={(e) => setSelectedBookingId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 outline-none focus:border-amber-500 font-medium"
              >
                {bookings.map((b) => (
                  <option key={b.id} value={b.id}>
                    [{b.booking_type}] {b.provider_name} - {b.reference_number} ({b.origin} &rarr; {b.destination})
                  </option>
                ))}
              </select>
            </div>

            {/* 2. Disruption Type */}
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Disruption Category
              </label>
              <select
                value={disruptionType}
                onChange={(e) => setDisruptionType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 outline-none focus:border-amber-500 font-medium"
              >
                <option value="flight_delay">Flight Delay</option>
                <option value="flight_cancellation">Flight Cancellation</option>
                <option value="train_delay">Train Delay</option>
                <option value="train_cancellation">Train Cancellation</option>
                <option value="bus_cancellation">Bus Cancellation</option>
                <option value="strike">Union Strike Action</option>
                <option value="weather">Severe Weather Hold</option>
              </select>
            </div>

            {/* 3. Delay Minutes */}
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Delay Duration ({delayMinutes} mins / {(delayMinutes / 60).toFixed(1)} hrs)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="15"
                  max="600"
                  step="15"
                  value={delayMinutes}
                  disabled={!disruptionType.includes('delay')}
                  onChange={(e) => setDelayMinutes(e.target.value)}
                  className="flex-1 accent-amber-500 cursor-pointer disabled:opacity-40"
                />
                <input
                  type="number"
                  min="0"
                  max="1440"
                  value={delayMinutes}
                  disabled={!disruptionType.includes('delay')}
                  onChange={(e) => setDelayMinutes(e.target.value)}
                  className="w-20 bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 text-center font-mono focus:border-amber-500 outline-none disabled:opacity-40"
                />
              </div>
            </div>

          </div>

          <div className="flex items-center justify-between pt-2">
            <div className="text-xs text-slate-400">
              Selected: <strong className="text-white">{selectedBooking?.title || 'None'}</strong>
              {disruptionType.includes('delay') && (
                <span className="text-amber-400 ml-1.5">(+{delayMinutes} mins delay)</span>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !selectedBookingId}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 text-white font-semibold text-xs flex items-center gap-2 cursor-pointer transition shadow-md disabled:opacity-50"
            >
              <Flame className={`w-4 h-4 ${loading ? 'animate-bounce' : ''}`} />
              <span>{loading ? 'Evaluating Cascades...' : 'Trigger Disruption & Analyze Impact'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Structured Impact Analysis Output Card */}
      {latestImpactResult && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-700/80 space-y-6 animate-fadeIn">
          
          {/* Header & Severity Banner */}
          <div className="flex items-start justify-between border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
                <BrainCircuit className="w-5 h-5" />
              </div>
              <div>
                <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                  Impact Analysis Agent Output
                </div>
                <h4 className="text-lg font-bold text-white mt-0.5">
                  Downstream Disruption Assessment
                </h4>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
                latestImpactResult.severity === 'CRITICAL'
                  ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                  : latestImpactResult.severity === 'HIGH'
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                    : 'bg-sky-500/20 text-sky-300 border-sky-500/30'
              }`}>
                {latestImpactResult.severity} SEVERITY IMPACT
              </span>
            </div>
          </div>

          {/* AI Explanation Speech Bubble */}
          <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/30 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-indigo-300 uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              Agent Impact Explanation:
            </div>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              "{latestImpactResult.reasoning}"
            </p>
          </div>

          {/* Missed Connections Details (if any) */}
          {latestImpactResult.missed_connections && latestImpactResult.missed_connections.length > 0 && (
            <div className="space-y-3">
              <h5 className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-2">
                <XCircle className="w-4 h-4" />
                Detected Missed Connections ({latestImpactResult.missed_connections.length})
              </h5>

              <div className="space-y-2">
                {latestImpactResult.missed_connections.map((missed, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-500/30 text-xs flex items-center justify-between gap-4">
                    <div>
                      <div className="font-semibold text-white">
                        {missed.from_booking_ref} &rarr; {missed.to_booking_ref}
                      </div>
                      <div className="text-[11px] text-rose-300 mt-0.5">
                        {missed.explanation}
                      </div>
                    </div>
                    <span className="text-[10px] px-2 py-1 rounded bg-rose-500/20 text-rose-300 font-mono shrink-0">
                      -{missed.deficit_minutes}m Deficit
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Affected vs Unaffected Bookings 2-Column Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            
            {/* Affected Bookings Column */}
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-bold text-amber-400 uppercase tracking-wider">
                <span className="flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4" />
                  Affected Bookings ({latestImpactResult.affected_bookings?.length || 0})
                </span>
              </div>

              <div className="space-y-2.5">
                {latestImpactResult.affected_bookings?.map((b) => (
                  <div key={b.booking_id} className="p-3.5 rounded-xl bg-slate-950 border border-amber-500/30 text-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">{b.title}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300">
                        {b.status}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400">
                      {b.impact_description}
                    </div>
                    <div className="text-[10px] font-mono text-slate-500">
                      Ref: {b.reference_number} &middot; Type: {b.booking_type}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Unaffected Bookings Column */}
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-bold text-emerald-400 uppercase tracking-wider">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  Unaffected Bookings ({latestImpactResult.unaffected_bookings?.length || 0})
                </span>
              </div>

              <div className="space-y-2.5">
                {latestImpactResult.unaffected_bookings?.map((u) => (
                  <div key={u.booking_id} className="p-3.5 rounded-xl bg-slate-950 border border-emerald-500/20 text-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">{u.title}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                        SAFE
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400">
                      {u.reason_unaffected}
                    </div>
                    <div className="text-[10px] font-mono text-slate-500">
                      Ref: {u.reference_number} &middot; Type: {u.booking_type}
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>

        </div>
      )}

    </div>
  );
}
