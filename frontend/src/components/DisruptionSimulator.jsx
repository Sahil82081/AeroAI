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
    <div className="space-y-4">
      
      {/* Simulation Form Card */}
      <div className="p-3.5 sm:p-4 rounded-xl bg-[#070b16]/80 backdrop-blur-2xl border border-white/[0.08] shadow-sm space-y-3.5 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-white/[0.08] pb-3 gap-2.5 relative z-10">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-400">
              <Flame className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white tracking-tight font-display">
                Travel Disruption Simulator &amp; Impact Engine
              </h3>
              <p className="text-xs text-slate-400 font-sans mt-0.5">
                Inject multi-modal disruptions to evaluate downstream graph cascades, missed connections, and unaffected bookings.
              </p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30 self-start sm:self-auto">
            SIMULATION ENGINE READY
          </span>
        </div>

        <form onSubmit={handleSimulate} className="space-y-3 relative z-10">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            
            {/* 1. Target Booking */}
            <div>
              <label className="text-[11px] font-semibold text-slate-300 block mb-1 font-display">
                Target Booking Leg
              </label>
              <select
                value={selectedBookingId}
                onChange={(e) => setSelectedBookingId(e.target.value)}
                className="w-full bg-[#04060d] border border-white/[0.1] rounded-lg h-8 px-2.5 text-xs text-slate-200 outline-none focus:border-amber-400 font-medium transition"
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
              <label className="text-[11px] font-semibold text-slate-300 block mb-1 font-display">
                Disruption Category
              </label>
              <select
                value={disruptionType}
                onChange={(e) => setDisruptionType(e.target.value)}
                className="w-full bg-[#04060d] border border-white/[0.1] rounded-lg h-8 px-2.5 text-xs text-slate-200 outline-none focus:border-amber-400 font-medium transition"
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
              <label className="text-[11px] font-semibold text-slate-300 block mb-1 font-display">
                Delay Duration ({delayMinutes} mins / {(delayMinutes / 60).toFixed(1)} hrs)
              </label>
              <div className="flex items-center gap-2.5">
                <input
                  type="range"
                  min="15"
                  max="600"
                  step="15"
                  value={delayMinutes}
                  disabled={!disruptionType.includes('delay')}
                  onChange={(e) => setDelayMinutes(e.target.value)}
                  className="flex-1 accent-amber-500 cursor-pointer disabled:opacity-40 h-1.5"
                />
                <input
                  type="number"
                  min="0"
                  max="1440"
                  value={delayMinutes}
                  disabled={!disruptionType.includes('delay')}
                  onChange={(e) => setDelayMinutes(e.target.value)}
                  className="w-16 bg-[#04060d] border border-white/[0.1] rounded-lg h-8 px-2 text-xs text-slate-200 text-center font-mono focus:border-amber-400 outline-none disabled:opacity-40"
                />
              </div>
            </div>

          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between pt-2 gap-2.5">
            <div className="text-xs text-slate-400 font-sans">
              Selected: <strong className="text-white font-display">{selectedBooking?.title || 'None'}</strong>
              {disruptionType.includes('delay') && (
                <span className="text-amber-400 font-mono ml-1.5">(+{delayMinutes}m delay)</span>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !selectedBookingId}
              className="h-8 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 text-white font-semibold text-xs flex items-center justify-center gap-1.5 cursor-pointer transition shadow-sm disabled:opacity-50 font-display"
            >
              <Flame className={`w-3.5 h-3.5 ${loading ? 'animate-bounce' : ''}`} />
              <span>{loading ? 'Evaluating...' : 'Trigger Disruption & Analyze'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Structured Impact Analysis Output Card */}
      {latestImpactResult && (
        <div className="p-3.5 sm:p-4 rounded-xl bg-[#070b16]/80 backdrop-blur-2xl border border-white/[0.08] shadow-sm space-y-4 relative overflow-hidden">
          
          {/* Header & Severity Banner */}
          <div className="flex flex-col sm:flex-row sm:items-start justify-between border-b border-white/[0.08] pb-3 gap-2.5">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 shrink-0">
                <BrainCircuit className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
                  Impact Analysis Agent Output
                </div>
                <h4 className="text-sm sm:text-base font-bold text-white mt-0.5 font-display">
                  Downstream Disruption Assessment
                </h4>
              </div>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto">
              <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold uppercase tracking-wider border ${
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
          <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-400/30 space-y-1.5 backdrop-blur-xl">
            <div className="flex items-center gap-1.5 text-[11px] font-bold text-indigo-300 uppercase tracking-wider font-mono">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              Agent Impact Explanation:
            </div>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              "{latestImpactResult.reasoning}"
            </p>
          </div>

          {/* Missed Connections Details (if any) */}
          {latestImpactResult.missed_connections && latestImpactResult.missed_connections.length > 0 && (
            <div className="space-y-2.5">
              <h5 className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5 font-mono">
                <XCircle className="w-3.5 h-3.5" />
                Detected Missed Connections ({latestImpactResult.missed_connections.length})
              </h5>

              <div className="space-y-2">
                {latestImpactResult.missed_connections.map((missed, idx) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-500/30 text-xs flex items-center justify-between gap-3 backdrop-blur-xl">
                    <div>
                      <div className="font-semibold text-white font-display text-xs">
                        {missed.from_booking_ref} &rarr; {missed.to_booking_ref}
                      </div>
                      <div className="text-[11px] text-rose-300 mt-0.5 font-sans">
                        {missed.explanation}
                      </div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-mono shrink-0 border border-rose-500/30">
                      -{missed.deficit_minutes}m Deficit
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Affected vs Unaffected Bookings 2-Column Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
            
            {/* Affected Bookings Column */}
            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-xs font-bold text-amber-400 uppercase tracking-wider font-mono">
                <span className="flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Affected Bookings ({latestImpactResult.affected_bookings?.length || 0})
                </span>
              </div>

              <div className="space-y-2">
                {latestImpactResult.affected_bookings?.map((b) => (
                  <div key={b.booking_id} className="p-3 rounded-xl bg-[#04060d]/80 border border-amber-500/30 text-xs space-y-1 hover:border-amber-500/50 transition-colors">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white font-display text-xs">{b.title}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        {b.status}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-sans">
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
            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-xs font-bold text-emerald-400 uppercase tracking-wider font-mono">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Unaffected Bookings ({latestImpactResult.unaffected_bookings?.length || 0})
                </span>
              </div>

              <div className="space-y-2">
                {latestImpactResult.unaffected_bookings?.map((u) => (
                  <div key={u.booking_id} className="p-3 rounded-xl bg-[#04060d]/80 border border-emerald-500/20 text-xs space-y-1 hover:border-emerald-500/40 transition-colors">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white font-display text-xs">{u.title}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        SAFE
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-sans">
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

export default DisruptionSimulator;
